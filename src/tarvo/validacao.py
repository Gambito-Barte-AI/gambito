"""Consolidação determinística e invariantes antes de qualquer publicação."""

from collections import Counter, defaultdict
from decimal import Decimal
import re

from .modelos import ErroEntrada, Resultado


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
            })


def validar(resultado: Resultado) -> None:
    def chave(origem):
        return origem.arquivo, origem.ref

    destinos = [chave(c.origem) for c in resultado.contribuicoes]
    destinos += [chave(p.origem) for p in resultado.pendencias]
    if len(destinos) != resultado.linhas_lidas or any(n != 1 for n in Counter(destinos).values()):
        raise ErroEntrada("Cobertura inválida: cada linha lida deve ter exatamente um destino principal")
    if not {chave(e.origem) for e in resultado.eventos} <= set(destinos):
        raise ErroEntrada("Evento sem destino principal")
    originais = {(c.origem.arquivo, c.origem.ref): c for c in resultado.contribuicoes}
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
