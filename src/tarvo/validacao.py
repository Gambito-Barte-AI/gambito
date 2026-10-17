"""Consolidação determinística e invariantes antes de qualquer publicação."""

from collections import Counter, defaultdict
from decimal import Decimal
import re

from .contratos import ARQUIVOS, CAMPOS_VALOR
from .modelos import ErroEntrada, Resultado, ResultadoParte


def validar_parte(parte: ResultadoParte) -> None:
    """Confere o contrato monetário comum, sem fórmulas de módulos futuros."""
    parte.validado = False

    def dinheiro(texto):
        if not isinstance(texto, str) or not re.fullmatch(r"-?[0-9]+\.[0-9]{2}", texto):
            raise ErroEntrada("Valor monetário fora do contrato de saída")
        return Decimal(texto)

    valores, desconhecidos = {}, set()
    if set(parte.linhas) - set(parte.relatorios):
        raise ErroEntrada("Parte produziu relatório fora do seu contrato")
    for arquivo, linhas in parte.linhas.items():
        if arquivo not in CAMPOS_VALOR:
            raise ErroEntrada("Relatório não reconhecido no contrato da parte")
        obrigatorias = ARQUIVOS[arquivo][:6] if arquivo == "pendencias.csv" else ARQUIVOS[arquivo]
        for linha in linhas:
            if not isinstance(linha, dict) or not set(obrigatorias) <= linha.keys() or set(linha) - set(ARQUIVOS[arquivo]):
                raise ErroEntrada("Linha incompatível com o contrato do relatório")
            identificador = linha["id_saida"]
            if not identificador or identificador in valores or identificador in desconhecidos:
                raise ErroEntrada("ID de saída ausente ou duplicado na parte")
            valor = linha[CAMPOS_VALOR[arquivo]]
            if arquivo == "pendencias.csv":
                if any(not linha.get(c) for c in ("tipo", "ref_origem", "motivo", "quem_decide", "proximo_passo")):
                    raise ErroEntrada("Pendência sem motivo, responsável ou próximo passo")
                if linha.get("categoria") not in {"DADOS", "NEGOCIO"}:
                    raise ErroEntrada("Pendência sem categoria reconhecida")
                if valor == "" and linha.get("natureza_valor") == "NAO_INFORMADO":
                    desconhecidos.add(identificador)
                    continue
            valores[identificador] = dinheiro(valor)
    somas, vistos = defaultdict(lambda: Decimal(0)), set()
    for linha in parte.rastro:
        if not isinstance(linha, dict) or not set(ARQUIVOS["rastro.csv"][:4]) <= linha.keys() or set(linha) - set(ARQUIVOS["rastro.csv"]):
            raise ErroEntrada("Rastro incompatível com o contrato")
        identificador = linha["id_saida"]
        chave = (identificador, linha["arquivo_origem"], linha["ref_origem"])
        if identificador not in valores or not all(chave) or chave in vistos:
            raise ErroEntrada("Rastro sem saída monetária ou referência duplicada/ausente")
        vistos.add(chave)
        somas[identificador] += dinheiro(linha["valor"])
    if set(somas) != set(valores) or any(somas[k] != v for k, v in valores.items()):
        raise ErroEntrada("Soma do rastro não fecha para a parte")
    if parte.cobertura:
        c = parte.cobertura
        if (set(c) != {"linhas_lidas", "calculadas", "pendentes", "bloqueadas"}
                or any(type(v) is not int or v < 0 for v in c.values())
                or c["linhas_lidas"] != c["calculadas"] + c["pendentes"] + c["bloqueadas"]):
            raise ErroEntrada("Cobertura inválida na parte")
    if desconhecidos:
        parte.situacao = "PROVISORIO"
        parte.motivos.append("Há pendências sem valor conhecido; não são zero e não têm rastro monetário")
    parte.validado = True


def consolidar(resultado: Resultado) -> None:
    grupos = defaultdict(list)
    for contribuicao in resultado.contribuicoes:
        grupos[(contribuicao.competencia, contribuicao.cnpj)].append(contribuicao)
    for (competencia, cnpj), linhas in sorted(grupos.items()):
        identificador = f"CHECKOUT:{competencia}:{cnpj}"
        resultado.comissoes.append({
            "id_saida": identificador, "cnpj": cnpj,
            "lojista": min(c.lojista for c in linhas), "linha_negocio": "CHECKOUT",
            "comissao_brl": format(sum((c.valor for c in linhas), Decimal(0)), ".2f"),
        })
        for contribuicao in sorted(linhas, key=lambda c: (c.origem.arquivo, c.origem.ref)):
            resultado.rastro.append({
                "id_saida": identificador, "arquivo_origem": contribuicao.origem.arquivo,
                "ref_origem": contribuicao.origem.ref, "valor": format(contribuicao.valor, ".2f"),
                "contrato_origem": contribuicao.contrato.arquivo,
                "ref_contrato": contribuicao.contrato.ref,
                "taxa_contratada_fracao": str(contribuicao.taxa),
                "faixa": contribuicao.faixa, "regra": contribuicao.regra,
                "vinculo_identidade": contribuicao.vinculo,
                "tipo_lancamento": contribuicao.tipo,
                "data_base_taxa": contribuicao.data_base_taxa.isoformat() if contribuicao.data_base_taxa else "",
                "ref_evento_original": contribuicao.ref_original,
                "arquivo_evento_original": contribuicao.arquivo_original,
            })


def validar(resultado: Resultado) -> None:
    resultado.validado = False

    def chave(origem):
        return origem.arquivo, origem.ref

    destinos = [chave(c.origem) for c in resultado.contribuicoes]
    destinos += [chave(p.origem) for p in resultado.pendencias]
    if len(destinos) != resultado.linhas_lidas or any(n != 1 for n in Counter(destinos).values()):
        raise ErroEntrada("Cobertura inválida: cada linha lida deve ter exatamente um destino principal")
    if not {chave(e.origem) for e in resultado.eventos} <= set(destinos):
        raise ErroEntrada("Evento sem destino principal")
    if len({c.origem.ref for c in resultado.contribuicoes}) != len(resultado.contribuicoes):
        raise ErroEntrada("ID econômico calculado mais de uma vez entre arquivos")
    if any(p.categoria not in {"DADOS", "NEGOCIO"} or not p.tipo or not p.proximo_passo.strip()
           for p in resultado.pendencias):
        raise ErroEntrada("Pendência sem categoria, tipo ou próximo passo (RN-58)")
    originais = {(c.origem.arquivo, c.origem.ref): c for c in resultado.contribuicoes}
    reversoes = set()
    for contribuicao in resultado.contribuicoes:
        if contribuicao.tipo != "REVERSAO ANTECIPACAO":
            continue
        ref = (contribuicao.arquivo_original, contribuicao.ref_original)
        original = originais.get(ref)
        if (original is None or original.tipo != "ANTECIPACAO" or ref in reversoes
                or original.cnpj != contribuicao.cnpj or contribuicao.valor != -original.valor
                or contribuicao.taxa != original.taxa or contribuicao.contrato != original.contrato
                or contribuicao.data_base_taxa != original.data_base_taxa or contribuicao.regra != original.regra):
            raise ErroEntrada("Reversão não anula exclusivamente a antecipação referenciada")
        reversoes.add(ref)
    if len(resultado.rastro) != len(originais):
        raise ErroEntrada("Quantidade de contribuições diferente do rastro")
    vistos = set()
    somas = defaultdict(lambda: Decimal(0))
    for linha in resultado.rastro:
        ref = (linha["arquivo_origem"], linha["ref_origem"])
        contribuicao = originais.get(ref)
        valor = Decimal(linha["valor"])
        if contribuicao is None or ref in vistos or not valor.is_finite() or valor != contribuicao.valor:
            raise ErroEntrada("Rastro não corresponde à contribuição de origem")
        esperado = f"CHECKOUT:{contribuicao.competencia}:{contribuicao.cnpj}"
        if linha["id_saida"] != esperado:
            raise ErroEntrada("Rastro associado ao lojista/competência incorretos")
        if (linha["ref_evento_original"] != contribuicao.ref_original
                or linha["arquivo_evento_original"] != contribuicao.arquivo_original
                or linha["data_base_taxa"] != (contribuicao.data_base_taxa.isoformat() if contribuicao.data_base_taxa else "")
                or linha["tipo_lancamento"] != contribuicao.tipo):
            raise ErroEntrada("Rastro perdeu o vínculo ou a data base do evento")
        vistos.add(ref)
        somas[linha["id_saida"]] += valor
    ids = set()
    for linha in resultado.comissoes:
        identificador = linha["id_saida"]
        if identificador in ids or not re.fullmatch(r"[0-9]{14}", linha["cnpj"]):
            raise ErroEntrada("Comissão com ID duplicado ou CNPJ inválido")
        valor = Decimal(linha["comissao_brl"])
        if identificador not in somas or not valor.is_finite() or somas[identificador] != valor:
            raise ErroEntrada(f"Rastro não fecha para {identificador}")
        ids.add(identificador)
    if ids != set(somas):
        raise ErroEntrada("Rastro sem comissão correspondente")
    resultado.validado = True
