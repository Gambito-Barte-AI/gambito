"""A2: taxas contratuais, contestação líquida e devolução de concessões."""

from collections import defaultdict
from decimal import Decimal, DecimalException, ROUND_HALF_UP

from .modelos import ErroEntrada, ResultadoParte

CENTAVO = Decimal("0.01")


def centavos(valor):
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def origem_rastro(c, identificador, valor, natureza):
    return dict(id_saida=identificador, arquivo_origem=c.origem.arquivo, ref_origem=c.origem.ref,
                valor=format(valor, ".2f"), contrato_origem=c.contrato.arquivo, ref_contrato=c.contrato.ref,
                taxa_contratada_fracao=str(c.taxa), faixa=c.faixa, regra=c.regra,
                vinculo_identidade=c.vinculo, tipo_lancamento=c.tipo,
                data_base_taxa=c.data_base_taxa.isoformat() if c.data_base_taxa else "",
                ref_evento_original=c.ref_original, arquivo_evento_original=c.arquivo_original,
                natureza_valor=natureza)


def pendencia(identificador, tipo, cnpj, itens, motivo, proximo_passo, natureza, categoria="NEGOCIO"):
    # Uma linha agregada por lojista, com detalhe monetário completo no rastro.
    return dict(id_saida=identificador, tipo=tipo,
                ref_origem=itens[0][0].origem.ref,
                valor_brl=format(sum((v for _, v in itens), Decimal(0)), ".2f"),
                motivo=motivo, quem_decide="Financeiro", proximo_passo=proximo_passo,
                arquivo_origem=itens[0][0].origem.arquivo,
                linha_origem=str(itens[0][0].origem.linha),
                cnpj=cnpj, categoria=categoria, natureza_valor=natureza)


def revisar(parte, c, motivo, prefixo):
    identificador = f"{prefixo}:{c.origem.arquivo}:{c.origem.ref}"
    linha = pendencia(identificador, "DADO_FINANCEIRO_A_CONFERIR", c.cnpj, [(c, Decimal(0))],
                      motivo, "Conferir o campo na Orbe e reprocessar; não liberar o valor enquanto estiver desconhecido.",
                      "NAO_INFORMADO", "DADOS")
    linha["valor_brl"] = ""  # não existe contribuição financeira a inventar
    parte.linhas["pendencias.csv"].append(linha)
    parte.situacao = "PROVISORIO"
    parte.motivos.append(motivo)


def calcular_divergencias(eventos, contribuicoes, pendencias_base, regras, linhas_lidas, avisos=()):
    """Reutiliza a resolução contratual, sem depender da soma/rastro das comissões."""
    por_origem = {(e.origem.arquivo, e.origem.ref): e for e in eventos}
    ordenadas = sorted(contribuicoes, key=lambda c: (c.origem.arquivo, c.origem.linha, c.origem.ref))
    fontes = ("orbe", "taxas", "regras")
    divergencias = ResultadoParte(fontes=fontes, relatorios=("divergencias_taxa.csv", "pendencias.csv"),
        implementado=True, situacao="COMPLETO", linhas={"divergencias_taxa.csv": [], "pendencias.csv": []})
    concessoes = regras.get("devolucoes_checkout", [])
    isencoes_concessao = {(d["cnpj"], d["isencao"]) for d in concessoes}
    grupos = defaultdict(list)
    desconhecidas = 0
    for c in ordenadas:
        e = por_origem[c.origem.arquivo, c.origem.ref]
        if (c.cnpj, c.regra) in isencoes_concessao:
            continue  # D-09: concessão vigente não integra a cobrança contratual à Orbe
        if e.taxa_aplicada_pct is None:
            revisar(divergencias, c, e.erro_taxa_aplicada or "Taxa aplicada não informada", "REVISAO_DIVERGENCIA")
            desconhecidas += 1
            continue
        aplicada = e.taxa_aplicada_pct / Decimal(100)
        if aplicada == c.taxa:
            continue  # RN-20: não comparar valor_taxa nem centavos de truncamento
        valor = centavos(e.bruto * (aplicada - c.taxa))
        id_saida = f"DIVERGENCIA:CHECKOUT:{c.origem.arquivo}:{c.origem.ref}"
        divergencias.linhas["divergencias_taxa.csv"].append(dict(
            id_saida=id_saida, cnpj=c.cnpj, linha_negocio="CHECKOUT", ref_origem=c.origem.ref,
            taxa_contratada_pct=format(c.taxa * 100, "f"), taxa_aplicada_pct=format(e.taxa_aplicada_pct, "f"),
            diferenca_brl=format(valor, ".2f")))
        divergencias.rastro.append(origem_rastro(c, id_saida, valor, "DIVERGENCIA_CONTRATUAL"))
        grupos[c.competencia, c.cnpj].append((c, valor))
    for (competencia, cnpj), itens in sorted(grupos.items()):
        id_saida = f"CONTESTACAO_ORBE:{competencia}:{cnpj}"
        divergencias.linhas["pendencias.csv"].append(pendencia(
            id_saida, "CONTESTACAO_TAXA_ORBE", cnpj, itens,
            "Diferença contratual líquida da Orbe: valores de venda e estorno assinados, sem concessões ao lojista.",
            "Revisar contrato e operações e encaminhar contestação à Orbe; diferença negativa exige decisão caso a caso.",
            "DIFERENCA_CONTRATUAL_LIQUIDA"))
        divergencias.rastro.extend(origem_rastro(c, id_saida, v, "CONTESTACAO_ORBE") for c, v in itens)
    divergencias.cobertura = dict(linhas_lidas=linhas_lidas, calculadas=len(ordenadas) - desconhecidas,
                                  pendentes=linhas_lidas - len(ordenadas) + desconhecidas, bloqueadas=0)
    if avisos or any(p.categoria == "DADOS" for p in pendencias_base):
        divergencias.situacao = "PROVISORIO"
        divergencias.motivos.append("Há fontes rejeitadas ou eventos não resolvidos; análise restrita ao subconjunto contratual disponível")

    return divergencias


def calcular_devolucao(eventos, contribuicoes, pendencias_base, regras, linhas_lidas, avisos=()):
    por_origem = {(e.origem.arquivo, e.origem.ref): e for e in eventos}
    ordenadas = sorted(contribuicoes, key=lambda c: (c.origem.arquivo, c.origem.linha, c.origem.ref))
    concessoes = regras.get("devolucoes_checkout", [])
    devolucao = ResultadoParte(fontes=("orbe", "taxas", "regras"), relatorios=("pendencias.csv",),
        implementado=True, situacao="COMPLETO", linhas={"pendencias.csv": []})
    elegiveis_total = 0
    valores_desconhecidos = 0
    for condicao in concessoes:
        isencao = next(i for i in regras["isencoes"] if i["id"] == condicao["isencao"])
        candidatas = [c for c in ordenadas if c.cnpj == condicao["cnpj"] and c.regra == isencao["id"]
                      and isencao["inicio"] <= c.data_base_taxa <= isencao["fim"]]
        if any(p.cnpj == condicao["cnpj"] for p in pendencias_base):
            devolucao.situacao = "PROVISORIO"
            devolucao.motivos.append("Há operações da concessão sem contrato ou identidade resolvida; total incompleto, não liberar devolução")
        # Checkout já conferiu o vínculo do estorno e resolveu a isenção pela
        # data da venda original. Movimento no período não torna venda antiga isenta.
        elegiveis = [c for c in candidatas if c.tipo in {"VENDA", "ANTECIPACAO", "ESTORNO"}]
        elegiveis_total += len(elegiveis)
        grupos_casa = defaultdict(list)
        for c in elegiveis:
            e = por_origem[c.origem.arquivo, c.origem.ref]
            if e.valor_taxa is None:
                valores_desconhecidos += 1
                revisar(devolucao, c, e.erro_valor_taxa or "Valor efetivamente cobrado não informado", "REVISAO_DEVOLUCAO")
                continue
            # c.valor já é a comissão contratada arredondada por linha; nunca recalcular pelo cobrado.
            grupos_casa[c.competencia, c.cnpj].append((c, centavos(e.valor_taxa - c.valor)))
        for (competencia, cnpj), itens in sorted(grupos_casa.items()):
            id_saida = f"DEVOLUCAO_CHECKOUT:{competencia}:{cnpj}"
            motivo = "Concessão ao lojista paga pela Tarvo; devolução pelo efetivamente cobrado menos comissão contratada (RN-64); fora da cobrança à Orbe."
            if devolucao.situacao == "PROVISORIO":
                motivo += " Subtotal incompleto: não liberar devolução antes de resolver os dados pendentes."
            devolucao.linhas["pendencias.csv"].append(pendencia(
                id_saida, "DEVOLUCAO_LOJISTA", cnpj, itens, motivo,
                "Conferir o total e o detalhe no rastro e autorizar a devolução ao lojista pelo Financeiro; pagamento não executado pela solução.",
                "DEVOLUCAO_LOJISTA"))
            devolucao.rastro.extend(origem_rastro(c, id_saida, v, "DEVOLUCAO_LOJISTA") for c, v in itens)
    devolucao.cobertura = dict(linhas_lidas=elegiveis_total, calculadas=elegiveis_total - valores_desconhecidos,
                              pendentes=valores_desconhecidos, bloqueadas=0)
    if avisos or any(p.categoria == "DADOS" for p in pendencias_base):
        if devolucao.situacao != "BLOQUEADO":
            devolucao.situacao = "PROVISORIO"
        devolucao.motivos.append("Cobertura da fonte incompleta; não liberar devolução sem revisão")
    return devolucao


def calcular(*args):
    partes = []
    for funcao, relatorios in ((calcular_divergencias, ("divergencias_taxa.csv", "pendencias.csv")),
                               (calcular_devolucao, ("pendencias.csv",))):
        try:
            partes.append(funcao(*args))
        except (ErroEntrada, ValueError, KeyError, TypeError, DecimalException) as exc:
            partes.append(ResultadoParte(fontes=("orbe", "taxas", "regras"), relatorios=relatorios,
                implementado=True, motivos=[f"Análise A2 não concluída: {exc}"]))
    return tuple(partes)
