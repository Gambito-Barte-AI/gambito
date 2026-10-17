"""Conferência de A2 pelas fontes e pelos CSVs, sem importar a aplicação."""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import re

from validar_saida import exigir, dinheiro


def numero_br(texto):
    return Decimal(texto.replace(".", "").replace(",", "."))


def verificar(manifesto, arquivos, config, origens):
    nomes = ("DIVERGENCIA:", "CONTESTACAO_ORBE:", "DEVOLUCAO_CHECKOUT:",
             "REVISAO_DIVERGENCIA:", "REVISAO_DEVOLUCAO:")
    saidas = arquivos["divergencias_taxa.csv"] + [
        p for p in arquivos["pendencias.csv"] if not p["id_saida"].startswith("PENDENCIA:")]
    traces = [r for r in arquivos["rastro.csv"] if r["id_saida"].startswith(nomes)]
    if manifesto["escopo_comando"] == "checkout":
        exigir(not saidas and not traces, "A2 publicada fora do escopo solicitado")
        return
    por_id = {s["id_saida"]: s for s in saidas}
    exigir(len(por_id) == len(saidas), "ID A2 repetido")
    somas, detalhes = defaultdict(Decimal), defaultdict(list)
    concessoes = {c["cnpj"]: c for c in config.get("devolucoes_checkout", [])}
    comissoes = {(r["arquivo_origem"], r["ref_origem"]): r for r in arquivos["rastro.csv"]
                 if r["id_saida"].startswith("CHECKOUT:")}
    for r in traces:
        identificador = r["id_saida"]
        exigir(identificador in por_id, "Rastro A2 sem saída")
        chave = r["arquivo_origem"], r["ref_origem"]
        exigir(chave in origens, "Origem A2 inexistente")
        e = origens[chave]
        exigir(r.get("contrato_origem") and r.get("ref_contrato") and r.get("regra"), "Contrato A2 sem proveniência")
        exigir(r.get("tipo_lancamento") == e["tipo_lancamento"], "Tipo A2 divergente da origem")
        data = datetime.strptime(e["data_venda_original"] if e["tipo_lancamento"] in
                                 {"ESTORNO", "REVERSAO ANTECIPACAO"} else e["data_movimento"], "%d/%m/%Y").date()
        exigir(r.get("data_base_taxa") == data.isoformat(), "Data A2 incorreta")
        if e["tipo_lancamento"] in {"ESTORNO", "REVERSAO ANTECIPACAO"}:
            exigir(r.get("ref_evento_original") == e["id_referencia"], "Referência original A2 perdida")
        if chave in comissoes:
            for campo in ("taxa_contratada_fracao", "faixa", "regra", "ref_contrato", "data_base_taxa"):
                exigir(r.get(campo) == comissoes[chave].get(campo), "Contrato A2 diverge da resolução do checkout")
        somas[identificador] += dinheiro(r["valor"])
        detalhes[identificador].append((r, e))
    divergencias = defaultdict(list)
    for s in saidas:
        identificador = s["id_saida"]
        exigir(identificador.startswith(nomes), "Saída de natureza A2 desconhecida")
        exigir(re.fullmatch(r"[0-9]{14}", s.get("cnpj", "")), "CNPJ A2 inválido")
        if identificador.startswith("REVISAO_"):
            exigir(s["valor_brl"] == "" and identificador not in detalhes and s.get("proximo_passo"),
                   "Valor desconhecido A2 virou contribuição monetária")
            continue
        campo = "diferenca_brl" if identificador.startswith("DIVERGENCIA:") else "valor_brl"
        exigir(identificador in detalhes and somas[identificador] == dinheiro(s[campo]), "Soma A2 não reconcilia")
        chaves = [(r["arquivo_origem"], r["ref_origem"]) for r, _ in detalhes[identificador]]
        exigir(len(set(chaves)) == len(chaves), "Operação duplicada no mesmo destino A2")
        if identificador.startswith("DIVERGENCIA:"):
            exigir(len(chaves) == 1 and s["linha_negocio"] == "CHECKOUT",
                   "Concessão/agrupamento indevido na divergência")
            r, e = detalhes[identificador][0]
            exigir(r["regra"] != concessoes.get(s["cnpj"], {}).get("isencao"), "Concessão incluída na cobrança contratual")
            aplicada = numero_br(e["taxa_aplicada_pct"]) / 100
            contratada = Decimal(r["taxa_contratada_fracao"])
            exigir(aplicada != contratada and Decimal(s["taxa_contratada_pct"]) == contratada * 100
                   and Decimal(s["taxa_aplicada_pct"]) == aplicada * 100, "Comparação de taxas A2 incorreta")
            esperado = (numero_br(e["valor_bruto"]) * (aplicada - contratada)).quantize(Decimal(".01"), ROUND_HALF_UP)
            exigir(dinheiro(s[campo]) == esperado and s["ref_origem"] == e["id_transacao"], "Fórmula da divergência incorreta")
            divergencias[s["cnpj"]].append((chaves[0], esperado))
        elif identificador.startswith("DEVOLUCAO_CHECKOUT:"):
            condicao = concessoes[s["cnpj"]]
            isencao = next(i for i in config["isencoes"] if i["id"] == condicao["isencao"])
            exigir(s["tipo"] == "DEVOLUCAO_LOJISTA" and s.get("natureza_valor") == "DEVOLUCAO_LOJISTA", "Devolução confundida com contestação")
            for r, e in detalhes[identificador]:
                permitidos = {"VENDA", "ANTECIPACAO", "ESTORNO"}
                exigir(condicao["politica_estornos"] == "VENDA_ORIGINAL_ISENTA", "Política de devolução não aprovada")
                exigir(e["tipo_lancamento"] in permitidos and isencao["inicio"].isoformat() <= r["data_base_taxa"] <= isencao["fim"].isoformat()
                       and r["regra"] == isencao["id"], "Recorte da devolução inválido")
                if e["tipo_lancamento"] == "ESTORNO":
                    original = origens.get((r.get("arquivo_evento_original"), e["id_referencia"]))
                    if original is not None:
                        exigir(original["tipo_lancamento"] == "VENDA"
                               and original["cod_estabelecimento"] == e["cod_estabelecimento"]
                               and original["data_movimento"] == e["data_venda_original"],
                               "Estorno da devolução sem vínculo compatível com a venda original")
                    else:
                        exigir(e["data_venda_original"][3:] != e["data_movimento"][3:]
                               and not r.get("arquivo_evento_original"),
                               "Estorno do mês sem venda original verificável na devolução")
                exigir(dinheiro(r["valor"]) == numero_br(e["valor_taxa"]), "Devolução não usa cobrança efetiva isenta")
        else:
            exigir(s["tipo"] == "CONTESTACAO_TAXA_ORBE" and s.get("natureza_valor") == "DIFERENCA_CONTRATUAL_LIQUIDA", "Natureza da contestação incorreta")
        if campo == "valor_brl":
            exigir(s.get("proximo_passo") and s.get("quem_decide") == "Financeiro", "Pendência A2 sem ação humana")
            primeiro = detalhes[identificador][0][0]
            exigir((s["arquivo_origem"], s["ref_origem"]) == (primeiro["arquivo_origem"], primeiro["ref_origem"]),
                   "Referência representativa da pendência não corresponde ao detalhe")
    for s in saidas:
        if s["id_saida"].startswith("CONTESTACAO_ORBE:"):
            esperadas = divergencias.pop(s["cnpj"], [])
            obtidas = [((r["arquivo_origem"], r["ref_origem"]), dinheiro(r["valor"])) for r, _ in detalhes[s["id_saida"]]]
            exigir(sorted(esperadas) == sorted(obtidas), "Contestação não corresponde às divergências líquidas")
    exigir(not divergencias, "Divergência sem pendência de contestação")
    # Confronta completude contra os eventos contratuais do mínimo, quando publicados.
    for nome, prefixo in (("DIVERGENCIAS_CHECKOUT", "DIVERGENCIA:"), ("DEVOLUCAO_CASA", "DEVOLUCAO_CHECKOUT:")):
        if not manifesto["partes"][nome]["rastro_validado"]:
            continue
        esperadas = set()
        for chave, r in comissoes.items():
            e = origens[chave]
            cnpj = r["id_saida"].rsplit(":", 1)[-1]
            if nome == "DIVERGENCIAS_CHECKOUT":
                if r["regra"] != concessoes.get(cnpj, {}).get("isencao") and re.fullmatch(r"-?[0-9]+(?:,[0-9]+)?", e.get("taxa_aplicada_pct", "")):
                    if numero_br(e["taxa_aplicada_pct"]) / 100 != Decimal(r["taxa_contratada_fracao"]):
                        esperadas.add(chave)
            elif cnpj in concessoes:
                condicao = concessoes[cnpj]
                if r["regra"] == condicao["isencao"] and e["tipo_lancamento"] in {"VENDA", "ANTECIPACAO", "ESTORNO"}:
                    try:
                        numero_br(e["valor_taxa"])
                    except (ValueError, ArithmeticError, KeyError):
                        continue
                    esperadas.add(chave)
        obtidas = {(r["arquivo_origem"], r["ref_origem"]) for r in traces if r["id_saida"].startswith(prefixo)}
        exigir(esperadas <= obtidas, "Operação elegível omitida de A2")
