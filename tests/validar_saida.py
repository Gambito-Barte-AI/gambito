"""Auditoria independente das saídas do mínimo; usa somente a biblioteca padrão."""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
import tomllib


CONTRATO = {
    "comissoes_por_lojista.csv": ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"],
    "divergencias_taxa.csv": ["id_saida", "cnpj", "linha_negocio", "ref_origem", "taxa_contratada_pct", "taxa_aplicada_pct", "diferenca_brl"],
    "notas_a_emitir.csv": ["id_saida", "tomador_cnpj", "tomador", "linha_negocio", "valor_brl", "discriminacao"],
    "lancamentos_classificados.csv": ["id_saida", "banco", "ref_origem", "data", "descricao", "valor", "conta_codigo", "metodo", "confianca"],
    "pendencias.csv": ["id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide"],
    "rastro.csv": ["id_saida", "arquivo_origem", "ref_origem", "valor"],
}


class ErroAceite(ValueError):
    """Artefato incompatível com as entradas ou com o contrato de saída."""


def exigir(condicao, mensagem):
    if not condicao:
        raise ErroAceite(mensagem)


def dinheiro(texto):
    exigir(isinstance(texto, str) and re.fullmatch(r"-?[0-9]+\.[0-9]{2}", texto),
           f"Valor monetário fora do formato: {texto!r}")
    return Decimal(texto)


def ler_csv(caminho, obrigatorias):
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";", strict=True)
        colunas = leitor.fieldnames or []
        exigir(set(obrigatorias) <= set(colunas) and len(colunas) == len(set(colunas)),
               f"{caminho.name}: cabeçalho inválido")
        if isinstance(obrigatorias, list):
            exigir(colunas[:len(obrigatorias)] == obrigatorias, f"{caminho.name}: ordem das colunas obrigatórias inválida")
        linhas = list(leitor)
        exigir(all(None not in l and all(v is not None for v in l.values()) for l in linhas),
               f"{caminho.name}: linha com quantidade de campos incorreta")
        return linhas


def agregar(estados):
    estados = list(estados)
    return ("BLOQUEADO" if not estados or all(e == "BLOQUEADO" for e in estados) else
            "COMPLETO" if all(e == "COMPLETO" for e in estados) else "PROVISORIO")


def verificar_partes(manifesto):
    partes = manifesto.get("partes", {})
    minimo = {"CHECKOUT", "PENDENCIAS_CHECKOUT"}
    futuras = {"REMESSAS", "DIVERGENCIAS_CHECKOUT", "DIVERGENCIAS_REMESSA", "NOTAS_CHECKOUT",
               "NOTAS_REMESSA", "EXTRATO_AURORA", "EXTRATO_MERIDIANO"}
    implementadas = set(minimo)
    if manifesto.get("versao", 0) >= 4:
        futuras.remove("DIVERGENCIAS_CHECKOUT")
        implementadas |= {"DIVERGENCIAS_CHECKOUT", "DEVOLUCAO_CASA"}
    if manifesto.get("versao", 0) >= 5:
        futuras -= {"REMESSAS", "DIVERGENCIAS_REMESSA"}
        implementadas |= {"REMESSAS", "DIVERGENCIAS_REMESSA"}
    if manifesto.get("versao", 0) >= 6:
        futuras -= {"NOTAS_CHECKOUT", "NOTAS_REMESSA"}
        implementadas |= {"NOTAS_CHECKOUT", "NOTAS_REMESSA"}
    if manifesto.get("versao", 0) >= 7:
        futuras.remove("EXTRATO_AURORA")
        implementadas.add("EXTRATO_AURORA")
    if manifesto.get("versao", 0) >= 8:
        futuras.remove("EXTRATO_MERIDIANO")
        implementadas.add("EXTRATO_MERIDIANO")
    if manifesto.get("versao", 0) >= 9:
        implementadas.add("ALERTAS_ANTECIPACAO")
    exigir(set(partes) == implementadas | futuras, "Partes ausentes ou desconhecidas")
    for nome, parte in partes.items():
        estado = parte.get("situacao")
        exigir(estado in {"COMPLETO", "PROVISORIO", "BLOQUEADO"}, "Situação de parte inválida")
        exigir(parte.get("rastro_validado") is (estado != "BLOQUEADO"), "Validade da parte incompatível com o status")
        if nome in futuras:
            exigir(parte.get("implementado") is False and estado == "BLOQUEADO" and parte.get("motivos"),
                   "Parte futura apresentada como implementada no aceite de A1")
        else:
            exigir(parte.get("implementado") is True, "Parte do mínimo não implementada")
        dependencias = parte.get("dependencias", {})
        exigir(isinstance(dependencias.get("fontes"), list) and isinstance(dependencias.get("partes"), list),
               "Dependências não declaradas")
        for fonte in dependencias["fontes"]:
            esperado = manifesto.get("fontes", {}).get(fonte, {}).get("situacao", "NAO_AVALIADA")
            exigir(parte.get("fontes", {}).get(fonte) == esperado, "Estado da fonte da parte incorreto")
        if estado != "BLOQUEADO":
            exigir(all(partes.get(d, {}).get("rastro_validado") is True for d in dependencias["partes"]),
                   "Parte liberada apesar de resultado requerido bloqueado")
            exigir(all(e in {"DISPONIVEL", "PROVISORIO"} for e in parte.get("fontes", {}).values()),
                   "Parte liberada sem fontes válidas")
    exigir(partes["CHECKOUT"]["situacao"] == manifesto.get("situacao"), "Status legado diverge do checkout")
    exigir(manifesto.get("rastro_validado") is partes["CHECKOUT"]["rastro_validado"], "Rastro legado diverge do checkout")
    fechamento = manifesto.get("fechamento", {})
    exigir(fechamento.get("situacao") == agregar(p["situacao"] for p in partes.values()), "Situação agregada incorreta")
    exigir(set(fechamento.get("partes", [])) == set(partes)
           and set(fechamento.get("bloqueadas", [])) == {n for n,p in partes.items() if p["situacao"] == "BLOQUEADO"}
           and set(fechamento.get("provisorias", [])) == {n for n,p in partes.items() if p["situacao"] == "PROVISORIO"},
           "Resumo das partes incorreto")
    escopo = manifesto.get("escopo_comando")
    exigir(escopo in {"checkout", "alvo"}, "Escopo do comando inválido")
    escolhidas = minimo if escopo == "checkout" else set(partes)
    exigir(manifesto.get("situacao_comando") == agregar(partes[n]["situacao"] for n in escolhidas),
           "Código de conclusão não corresponde ao escopo")
    for arquivo, detalhe in manifesto["resultados"].items():
        previstas = {n for n,p in partes.items() if arquivo == "rastro.csv" or arquivo in p.get("relatorios", [])}
        participantes = previstas & escolhidas
        if manifesto.get("versao", 0) < 4:
            participantes = participantes or previstas
        exigir(set(detalhe.get("partes", [])) == participantes, "Produtores do relatório incorretos")
        exigir(detalhe.get("situacao") == agregar(partes[n]["situacao"] for n in participantes)
               and detalhe.get("situacao_alvo") == agregar(partes[n]["situacao"] for n in previstas),
               "Status do relatório omite uma parte bloqueada")
    return partes


def verificar(dados: Path, saida: Path, regras: Path, esperar=None, esperar_fechamento=None):
    manifesto = json.loads((saida / "manifesto.json").read_text(encoding="utf-8"))
    exigir(isinstance(manifesto, dict), "Manifesto não é objeto")
    situacao = manifesto.get("situacao")
    exigir(situacao in {"COMPLETO", "PROVISORIO", "BLOQUEADO"}, "Situação não reconhecida")
    if esperar:
        exigir(situacao == esperar, f"Esperado {esperar}, encontrado {situacao}")
    configuracao = tomllib.loads(regras.read_text(encoding="utf-8"))
    exigir(manifesto.get("decisoes_financeiras_pendentes") == configuracao.get("decisoes_pendentes", []),
           "Decisões financeiras pendentes foram omitidas ou alteradas")
    exigir(manifesto.get("decisoes_documentadas", []) == configuracao.get("decisoes_documentadas", []),
           "Decisões documentadas foram omitidas ou alteradas")
    nomes = set(CONTRATO)
    if situacao == "BLOQUEADO" and manifesto.get("publicacao_concluida") is False:
        exigir(manifesto.get("arquivos") == {} and manifesto.get("rastro_validado") is False
               and manifesto.get("total_parcial_brl") is None and manifesto.get("motivos"),
               "Publicação interrompida apresenta valores válidos")
        return {"situacao": situacao, "arquivos_validos": 0, "publicacao_concluida": False}
    exigir(set(manifesto.get("arquivos", {})) == nomes, "Lista de arquivos diferente do mínimo")
    for nome, digest in manifesto["arquivos"].items():
        exigir(sha256((saida / nome).read_bytes()).hexdigest() == digest, f"Hash de {nome} não confere")
    arquivos = {nome: ler_csv(saida / nome, colunas) for nome, colunas in CONTRATO.items()}
    resultados = manifesto.get("resultados", {})
    exigir(set(resultados) == nomes, "Faltam status por relatório")
    for nome, linhas in arquivos.items():
        exigir(resultados[nome].get("linhas") == len(linhas), f"Contagem incorreta: {nome}")
        exigir(resultados[nome].get("situacao") in {"COMPLETO", "PROVISORIO", "BLOQUEADO"}, f"Status inválido: {nome}")
    partes = verificar_partes(manifesto) if manifesto.get("versao", 0) >= 3 else {}
    if manifesto.get("versao", 0) >= 8:
        from auditoria_integrada import verificar as verificar_integrada
        verificar_integrada(manifesto, arquivos)
    if esperar_fechamento:
        exigir(manifesto.get("fechamento", {}).get("situacao") == esperar_fechamento, "Fechamento diferente do esperado")
    vazios = ()
    if manifesto.get("versao", 0) < 7 or manifesto.get("escopo_comando") == "checkout":
        vazios += ("lancamentos_classificados.csv",)
    if manifesto.get("versao", 0) < 6 or manifesto.get("escopo_comando") == "checkout":
        vazios += ("notas_a_emitir.csv",)
    if manifesto.get("versao", 0) < 4 or manifesto.get("escopo_comando") == "checkout":
        vazios += ("divergencias_taxa.csv",)
    for nome in vazios:
        exigir(not arquivos[nome] and resultados[nome].get("situacao") == "BLOQUEADO"
               and resultados[nome].get("motivos"), "Relatório do alvo apresentado como processado")
    comissoes = [l for l in arquivos["comissoes_por_lojista.csv"] if l["linha_negocio"] == "CHECKOUT"]
    if manifesto.get("versao", 0) >= 5:
        from auditoria_a3 import verificar as verificar_a3
        verificar_a3(manifesto, arquivos, configuracao, dados)
    if manifesto.get("versao", 0) >= 6:
        from auditoria_a4 import verificar as verificar_a4
        verificar_a4(manifesto, arquivos, configuracao)
    if manifesto.get("versao", 0) >= 7:
        from auditoria_a5 import verificar as verificar_a5
        verificar_a5(manifesto, arquivos, configuracao, dados, regras)
    if manifesto.get("versao", 0) >= 8:
        from auditoria_a6 import verificar as verificar_a6
        verificar_a6(manifesto, arquivos, configuracao, dados, regras)
    if manifesto.get("versao", 0) >= 9:
        from auditoria_e3 import verificar as verificar_e3
        verificar_e3(manifesto, arquivos, configuracao, dados)
    rastros = arquivos["rastro.csv"]
    if situacao == "BLOQUEADO" and not any(arquivos.values()):
        exigir(not any(arquivos.values()) and (partes or all(r["situacao"] == "BLOQUEADO" for r in resultados.values()))
               and manifesto.get("rastro_validado") is False
               and manifesto.get("total_parcial_brl") is None and manifesto.get("motivos"),
               "Bloqueio deve ter apenas cabeçalhos, sem valores válidos")
        return {"situacao": situacao, "motivos": manifesto["motivos"], "arquivos_validos": 0}
    exigir(manifesto.get("rastro_validado") is (situacao != "BLOQUEADO"), "Rastro não corresponde ao estado do checkout")
    fontes = manifesto.get("fontes", {})
    exigir({"orbe", "taxas", "regras"} <= set(fontes), "Dependências do mínimo não identificadas")
    if partes and all(not partes[n]["rastro_validado"] for n in ("CHECKOUT", "PENDENCIAS_CHECKOUT")) and any(
            fontes[n].get("situacao") == "BLOQUEADO" for n in ("orbe", "taxas", "regras")):
        exigir(not comissoes and not any(r["id_saida"].startswith(("CHECKOUT:", "PENDENCIA:")) for r in rastros),
               "Parte checkout sem fontes publicou valores")
        return {"situacao": situacao, "checkout_bloqueado": True, "ponte_auditada": True,
                "situacao_comando": manifesto["situacao_comando"]}
    for nome in ("taxas", "regras"):
        fonte = fontes[nome]
        arquivo = fonte.get("arquivo", "")
        exigir(arquivo and Path(arquivo).name == arquivo and fonte.get("situacao") == "DISPONIVEL",
               f"Fonte inválida: {nome}")
        caminho = regras if nome == "regras" else dados / arquivo
        exigir(sha256(caminho.read_bytes()).hexdigest() == fonte.get("sha256"), f"Fonte {nome} mudou")
    from io import StringIO
    origem, por_origem, por_ref, linhas_fisicas = [], {}, {}, {}
    competencia = manifesto.get("competencia")
    entradas = fontes["orbe"].get("arquivos", [])
    exigir(entradas and fontes["orbe"].get("situacao") in {"DISPONIVEL", "PROVISORIO"}, "Fonte Orbe inválida")
    candidatos = set()
    for caminho in dados.glob("*.csv"):
        try:
            bruto = caminho.read_bytes()
            try:
                texto = bruto.decode("utf-8-sig")
            except UnicodeDecodeError:
                texto = bruto.decode("cp1252")
            cabecalho = next(csv.reader(StringIO(texto), delimiter=";"), [])
            assinatura = {"id_transacao", "data_movimento", "cod_estabelecimento", "tipo_lancamento",
                          "modalidade", "qtd_parcelas", "valor_bruto", "id_referencia", "data_venda_original"}
            if "id_transacao" in cabecalho or len(assinatura.intersection(cabecalho)) >= 3:
                candidatos.add(caminho.name)
        except (UnicodeError, csv.Error):
            continue
    exigir({e.get("arquivo") for e in entradas} == candidatos and len(entradas) == len(candidatos),
           "Manifesto omite ou duplica um CSV Orbe reconhecido na pasta")
    for fonte in entradas:
        arquivo = fonte.get("arquivo", "")
        exigir(arquivo and Path(arquivo).name == arquivo, "Nome de fonte Orbe inválido")
        bruto = (dados / arquivo).read_bytes()
        exigir(sha256(bruto).hexdigest() == fonte.get("sha256"), f"Fonte Orbe {arquivo} mudou")
        if fonte.get("situacao") == "BLOQUEADO":
            exigir(fonte.get("motivo") and fonte["motivo"] in manifesto.get("avisos", []), "Fonte inválida sem aviso")
            continue
        try:
            texto = bruto.decode("utf-8-sig")
        except UnicodeDecodeError:
            texto = bruto.decode("cp1252")
        leitor = csv.DictReader(StringIO(texto), delimiter=";", strict=True)
        linhas = [(leitor.line_num, l) for l in leitor]
        exigir(len(linhas) == fonte.get("linhas"), "Contagem física da fonte incorreta")
        for fisica, l in linhas:
            ref = l.get("id_transacao", "").strip()
            exigir(ref and (arquivo, ref) not in por_origem, "IDs de entrada ausentes/duplicados no mesmo arquivo")
            try:
                mes = datetime.strptime(l.get("data_movimento", ""), "%d/%m/%Y").strftime("%Y-%m")
            except ValueError:
                mes = competencia  # data inválida tem de aparecer como pendência
            if mes != competencia:
                continue
            por_origem[arquivo, ref] = l
            linhas_fisicas[arquivo, ref] = fisica
            por_ref.setdefault(ref, (arquivo, l))
            origem.append((arquivo, ref))
    pendencias = manifesto.get("pendencias", [])
    exigir(isinstance(pendencias, list), "Pendências inválidas")
    for p in pendencias:
        exigir(all(p.get(k) for k in ("ref_origem", "motivo", "quem_decide", "tipo", "proximo_passo"))
               and p.get("categoria") in {"DADOS", "NEGOCIO"}, "Pendência sem origem, motivo, categoria ou próximo passo")
        if p.get("valor_orbe_brl") is not None:
            dinheiro(p["valor_orbe_brl"])
        exigir(p.get("linha") == linhas_fisicas.get((p.get("arquivo_origem"), p.get("ref_origem"))),
               "Pendência perdeu a linha física de origem")
    if manifesto.get("versao", 0) >= 4:
        from auditoria_a2 import verificar as verificar_a2
        a2 = dict(arquivos)
        a2["comissoes_por_lojista.csv"] = comissoes
        a2["divergencias_taxa.csv"] = [l for l in arquivos["divergencias_taxa.csv"] if l["linha_negocio"] == "CHECKOUT"]
        a2["pendencias.csv"] = [l for l in arquivos["pendencias.csv"] if l["id_saida"].startswith(
            ("PENDENCIA:", "CONTESTACAO_ORBE:", "DEVOLUCAO_CHECKOUT:", "REVISAO_DIVERGENCIA:", "REVISAO_DEVOLUCAO:"))]
        a2["rastro.csv"] = [r for r in arquivos["rastro.csv"] if r["id_saida"].startswith(
            ("CHECKOUT:", "PENDENCIA:", "DIVERGENCIA:CHECKOUT:", "CONTESTACAO_ORBE:", "DEVOLUCAO_CHECKOUT:", "REVISAO_DIVERGENCIA:", "REVISAO_DEVOLUCAO:"))]
        verificar_a2(manifesto, a2, configuracao, por_origem)
        rastros = [r for r in rastros if r["id_saida"].startswith(("CHECKOUT:", "PENDENCIA:"))]
    pendencias_csv = [p for p in arquivos["pendencias.csv"] if p["id_saida"].startswith("PENDENCIA:")]
    pendencias_publicadas = pendencias if not partes or partes["PENDENCIAS_CHECKOUT"]["rastro_validado"] else []
    exigir(len(pendencias_csv) == len(pendencias_publicadas), "Contagem de pendencias.csv difere da parte validada")
    por_pendencia = {(p["arquivo_origem"], p["ref_origem"], str(p["linha"])): p for p in pendencias}
    ids_pendencias = set()
    valores_pendencias = {}
    for linha in pendencias_csv:
        chave = (linha.get("arquivo_origem"), linha["ref_origem"], linha.get("linha_origem"))
        p = por_pendencia.get(chave)
        exigir(p is not None, "Pendência CSV sem origem no manifesto")
        esperado = f"PENDENCIA:{chave[0]}:L{chave[2]}:{chave[1]}"
        exigir(linha["id_saida"] == esperado and esperado not in ids_pendencias, "ID de pendência incorreto ou duplicado")
        ids_pendencias.add(esperado)
        for campo in ("tipo", "motivo", "quem_decide", "proximo_passo", "categoria"):
            exigir(linha.get(campo) == p.get(campo) and linha[campo], f"Pendência CSV perdeu {campo}")
        exigir(linha.get("cnpj") == (p.get("cnpj") or ""), "Pendência CSV perdeu o CNPJ")
        valor = p.get("valor_orbe_brl") if p.get("valor_orbe_brl") is not None else p.get("valor_bruto_brl")
        natureza = "COBRANCA_ORBE" if p.get("valor_orbe_brl") is not None else "BRUTO_REFERENCIA" if valor is not None else "NAO_INFORMADO"
        exigir(linha.get("natureza_valor") == natureza, "Natureza do valor da pendência incorreta")
        if valor is None:
            exigir(linha["valor_brl"] == "", "Valor desconhecido de pendência virou zero")
        else:
            exigir(dinheiro(linha["valor_brl"]) == Decimal(valor), "Valor da pendência CSV difere da origem")
            if natureza == "COBRANCA_ORBE":
                bruto_origem = por_origem[chave[0], chave[1]].get("valor_taxa", "").strip()
                exigir(bruto_origem and Decimal(bruto_origem.replace(".", "").replace(",", ".")) == dinheiro(linha["valor_brl"]),
                       "Valor cobrado da pendência difere da Orbe")
            valores_pendencias[esperado] = linha
    rastros_pendencias = [r for r in rastros if r["id_saida"].startswith("PENDENCIA:")]
    exigir(Counter(r["id_saida"] for r in rastros_pendencias) == Counter(valores_pendencias.keys()),
           "Rastro das pendências incompleto ou duplicado")
    for r in rastros_pendencias:
        p = valores_pendencias[r["id_saida"]]
        exigir(r["arquivo_origem"] == p["arquivo_origem"] and r["ref_origem"] == p["ref_origem"]
               and dinheiro(r["valor"]) == dinheiro(p["valor_brl"])
               and r.get("natureza_valor") == p["natureza_valor"], "Rastro da pendência não reconcilia")
    rastros = [r for r in rastros if not r["id_saida"].startswith("PENDENCIA:")]
    orfaos = [p for p in arquivos["pendencias.csv"] if p["id_saida"].startswith("AJUSTE_ORFAO_ORBE:")]
    rastros_orfaos = [r for r in arquivos["rastro.csv"] if r["id_saida"].startswith("AJUSTE_ORFAO_ORBE:")]
    exigir(Counter(p["id_saida"] for p in orfaos) == Counter(r["id_saida"] for r in rastros_orfaos),
           "Ajuste órfão sem rastro ou pendência derivada")
    rastro_comissoes = {(r["arquivo_origem"], r["ref_origem"]): r for r in rastros if r["id_saida"].startswith("CHECKOUT:")}
    exigir(set(rastro_comissoes) <= set(por_origem), "checkout com destino sem origem de entrada")
    esperados_orfaos = {
        chave for chave, c in rastro_comissoes.items()
        if (por_origem[chave]["tipo_lancamento"] in {"ESTORNO", "REVERSAO ANTECIPACAO"}
            and por_origem[chave]["id_referencia"] not in por_ref
            and por_origem[chave]["data_venda_original"][3:] == por_origem[chave]["data_movimento"][3:])
    }
    exigir({(p["arquivo_origem"], p["ref_origem"]) for p in orfaos} == esperados_orfaos,
           "Contribuição órfã sem pendência de revisão")
    for p in orfaos:
        chave = p["arquivo_origem"], p["ref_origem"]
        e = por_origem.get(chave)
        c = rastro_comissoes.get(chave)
        r = next(r for r in rastros_orfaos if r["id_saida"] == p["id_saida"])
        exigir(e and c and e["tipo_lancamento"] in {"ESTORNO", "REVERSAO ANTECIPACAO"}
               and e["id_referencia"] and e["id_referencia"] not in por_ref
               and e["data_venda_original"][3:] == e["data_movimento"][3:]
               and p["categoria"] == "DADOS" and p["quem_decide"] == "Financeiro"
               and p["natureza_valor"] == "COMISSAO_AJUSTE_ORFAO_A_CONFERIR"
               and dinheiro(p["valor_brl"]) == dinheiro(r["valor"]) == dinheiro(c["valor"])
               and r["ref_evento_original"] == e["id_referencia"],
               "Ajuste órfão não corresponde à origem ou à contribuição provisória")
    if not partes:
        exigir(resultados["comissoes_por_lojista.csv"]["situacao"] == situacao, "Status da comissão diverge do checkout")
        esperado_pendencias = "PROVISORIO" if any(not p["valor_brl"] for p in pendencias_csv) else situacao
        for nome in ("pendencias.csv", "rastro.csv"):
            exigir(resultados[nome]["situacao"] == esperado_pendencias, f"Status incoerente em {nome}")
    destinos = [(l["arquivo_origem"], l["ref_origem"]) for l in rastros]
    destinos += [(p["arquivo_origem"], p["ref_origem"]) for p in pendencias_publicadas]
    exigir(Counter(destinos) <= Counter(origem), "Entrada sem destino, duplicada ou com referência inventada")
    exigir(len({l["ref_origem"] for l in rastros}) == len(rastros), "ID econômico calculado mais de uma vez")
    cobertura = manifesto.get("cobertura", {})
    exigir(cobertura == {"linhas_lidas": len(origem), "calculadas": len(rastros),
                         "pendentes": len(pendencias_publicadas), "bloqueadas": len(origem) - len(destinos)}, "Cobertura declarada não corresponde aos arquivos")
    provisorio = bool(manifesto.get("avisos")) or bool(orfaos) or any(p["categoria"] == "DADOS" for p in pendencias)
    if situacao != "BLOQUEADO":
        exigir((situacao == "PROVISORIO") == provisorio, "Situação incompatível com D-13")
    if situacao != "BLOQUEADO" and (not partes or partes["PENDENCIAS_CHECKOUT"]["rastro_validado"]):
        exigir(Counter(destinos) == Counter(origem), "Cobertura incompleta sem parte bloqueada")
    ids = [l["id_saida"] for l in comissoes]
    exigir(len(set(ids)) == len(ids), "IDs de saída duplicados")
    exigir(len({l["cnpj"] for l in comissoes}) == len(comissoes), "CNPJ duplicado nas comissões do mês")
    por_saida = {l["id_saida"]: l for l in comissoes}
    somas = defaultdict(lambda: Decimal(0))
    por_rastro = {l["ref_origem"]: l for l in rastros}
    competencia = manifesto.get("competencia")
    if situacao != "BLOQUEADO":
        exigir(isinstance(competencia, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}", competencia),
               "Competência inválida")
    for linha in comissoes:
        exigir(re.fullmatch(r"[0-9]{14}", linha["cnpj"]) and linha["lojista"].strip()
               and linha["linha_negocio"] == "CHECKOUT", "Domínio da comissão inválido")
        dinheiro(linha["comissao_brl"])
    for linha in rastros:
        exigir((linha["arquivo_origem"], linha["ref_origem"]) in por_origem and linha["id_saida"] in por_saida,
               "Rastro aponta para arquivo ou saída inexistentes")
        somas[linha["id_saida"]] += dinheiro(linha["valor"])
        evento = por_origem[linha["arquivo_origem"], linha["ref_origem"]]
        exigir(linha.get("tipo_lancamento") == evento["tipo_lancamento"], "Rastro mudou tipo de evento")
        movimento = datetime.strptime(evento["data_movimento"], "%d/%m/%Y").date()
        exigir(movimento.strftime("%Y-%m") == competencia, "Competência não corresponde ao movimento de origem")
        if evento["tipo_lancamento"] in {"ESTORNO", "REVERSAO ANTECIPACAO"}:
            exigir(linha.get("ref_evento_original") == evento["id_referencia"], "Referência original perdida")
        if evento.get("id_referencia") in por_ref:
            exigir(linha.get("arquivo_evento_original") == por_ref[evento["id_referencia"]][0],
                   "Arquivo da referência original incorreto")
        if evento["tipo_lancamento"] == "REVERSAO ANTECIPACAO":
            anterior = por_rastro.get(evento["id_referencia"])
            exigir(anterior is not None and anterior["tipo_lancamento"] == "ANTECIPACAO"
                   and anterior["id_saida"] == linha["id_saida"]
                   and dinheiro(anterior["valor"]) + dinheiro(linha["valor"]) == 0,
                   "Reversão não anula sua antecipação")
        base = (datetime.strptime(evento["data_venda_original"], "%d/%m/%Y").date()
                if evento["tipo_lancamento"] in {"ESTORNO", "REVERSAO ANTECIPACAO"} else movimento)
        exigir(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", linha.get("data_base_taxa", ""))
               and date.fromisoformat(linha["data_base_taxa"]) == base,
               "Data base não corresponde ao evento de origem")
    exigir(set(somas) == set(ids), "Comissão sem rastro ou rastro sem comissão")
    exigir(all(somas[l["id_saida"]] == dinheiro(l["comissao_brl"]) for l in comissoes),
           "Soma do rastro não corresponde à comissão")
    total = sum((dinheiro(l["comissao_brl"]) for l in comissoes), Decimal(0))
    if situacao == "BLOQUEADO":
        exigir(not comissoes and not rastros and manifesto.get("total_parcial_brl") is None, "Comissão bloqueada publicou valores")
    else:
        exigir(total == dinheiro(manifesto.get("total_parcial_brl")), "Total do manifesto não confere")
    return {"situacao": situacao, "competencia": manifesto.get("competencia"),
            "cobertura": cobertura, "comissoes": len(comissoes), "total_brl": format(total, ".2f") if situacao != "BLOQUEADO" else None,
            "rastro_exato": True, "fontes_e_hashes": True, "decisoes_preservadas": True,
            "pendencias_csv": len(arquivos["pendencias.csv"]), "pendencias_minimo": len(pendencias_csv),
            "divergencias_checkout": sum(l["linha_negocio"] == "CHECKOUT" for l in arquivos["divergencias_taxa.csv"]),
            "rastro_pendencias": len(rastros_pendencias), "contratos_csv": len(arquivos), "fechamento": manifesto.get("fechamento", {}).get("situacao"),
            "situacao_comando": manifesto.get("situacao_comando", situacao)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", required=True, type=Path)
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--regras", required=True, type=Path)
    parser.add_argument("--esperar", choices=["COMPLETO", "PROVISORIO", "BLOQUEADO"])
    parser.add_argument("--esperar-fechamento", choices=["COMPLETO", "PROVISORIO", "BLOQUEADO"])
    args = parser.parse_args()
    try:
        resultado = verificar(args.dados, args.saida, args.regras, args.esperar, args.esperar_fechamento)
    except (ValueError, OSError, KeyError, TypeError, csv.Error) as exc:
        parser.exit(1, f"ACEITE REPROVADO: {exc}\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
