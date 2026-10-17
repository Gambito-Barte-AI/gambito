"""A3: participação realizada e comparação contratual, sem notas ou pagamentos."""

from collections import defaultdict
from decimal import Decimal, DecimalException
import re

from .divergencias import centavos
from .modelos import ResultadoParte


def referencia_ajuste(operacao):
    return re.fullmatch(r"AJUSTE REF (PC-[A-Z0-9-]+)(?:\s.*)?", operacao.observacao.upper())


def resolver(operacao, contratos):
    candidatos = [c for c in (contratos or []) if c.cnpj == operacao.cnpj]
    if any(c.inicio is None and c.fim is None for c in candidatos):
        return None, "Vigência de spread desconhecida"
    vigentes = [c for c in candidatos if (c.inicio is None or c.inicio <= operacao.contratacao)
                and (c.fim is None or operacao.contratacao <= c.fim)]
    if len(vigentes) != 1 or vigentes[0].limitacao or vigentes[0].spread is None:
        return None, "Cadastro/spread ausente, inválido ou com vigência conflitante; Comercial deve confirmar"
    return vigentes[0], ""


def rastro(e, identificador, valor, natureza, regra, contrato=None, ref_original="", arquivo_original=""):
    ajuste = referencia_ajuste(e)
    ref_original = ref_original or (ajuste.group(1) if ajuste else "")
    return dict(id_saida=identificador, arquivo_origem=e.origem.arquivo, ref_origem=e.origem.ref,
        valor=format(valor, ".2f"), linha_origem=str(e.origem.linha), natureza_valor=natureza,
        regra=regra, data_base_taxa=e.contratacao.isoformat(), tipo_lancamento="AJUSTE" if ref_original else "OPERACAO",
        ref_original=ref_original, ref_evento_original=ref_original, arquivo_evento_original=arquivo_original,
        contrato_origem=contrato.origem.arquivo if contrato else "",
        ref_contrato=contrato.origem.ref if contrato else "",
        taxa_contratada_fracao=str(contrato.spread) if contrato else "")


def pendencia(parte, identificador, tipo, itens, motivo, natureza, decisor="Financeiro",
              proximo="Revisar operações e encaminhar à Ponte; nenhuma contestação ou pagamento foi executado.",
              reportado=None, solicitado=None, ref_original="", arquivo_original="", categoria="NEGOCIO"):
    e = itens[0][0]
    desconhecido = any(v is None for _, v, _ in itens)
    valor = None if desconhecido else sum((v for _, v, _ in itens), Decimal(0))
    linha = dict(id_saida=identificador, tipo=tipo, ref_origem=e.origem.ref,
        valor_brl="" if valor is None else format(valor, ".2f"), motivo=motivo, quem_decide=decisor,
        proximo_passo=proximo, arquivo_origem=e.origem.arquivo, linha_origem=str(e.origem.linha),
        cnpj=e.cnpj, categoria=categoria, natureza_valor="NAO_INFORMADO" if desconhecido else natureza,
        valor_reportado_brl="" if reportado is None else format(reportado, ".2f"),
        valor_solicitado_brl="" if solicitado is None else format(solicitado, ".2f"), ref_original=ref_original)
    parte.linhas["pendencias.csv"].append(linha)
    if desconhecido:
        parte.situacao = "PROVISORIO"
        parte.motivos.append(motivo)
    else:
        parte.rastro.extend(rastro(op, identificador, v, natureza, tipo, c, ref_original, arquivo_original)
                            for op, v, c in itens)


def calcular(operacoes, falhas, quantidade, contratos, regras):
    parametros = regras["remessas"]
    fracao = Decimal(parametros["participacao_fracao"])
    tolerancia = Decimal(parametros["tolerancia_pp"]) / 100
    com = ResultadoParte(fontes=("ponte", "regras"), relatorios=("comissoes_por_lojista.csv", "pendencias.csv"),
        implementado=True, situacao="COMPLETO", linhas={"comissoes_por_lojista.csv": [], "pendencias.csv": []})
    div = ResultadoParte(fontes=("ponte", "contratos_remessa", "regras"), relatorios=("divergencias_taxa.csv", "pendencias.csv"),
        implementado=True, situacao="COMPLETO", linhas={"divergencias_taxa.csv": [], "pendencias.csv": []})
    grupos, cobrancas, cadastro, acompanhamento = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    por_ref = defaultdict(list)
    for e in sorted(operacoes, key=lambda e: (e.origem.arquivo, e.origem.linha)):
        por_ref[e.origem.ref].append(e)
    calculadas = pendentes = div_calculadas = div_pendentes = 0
    refs_invalidas = {p.origem.ref for p in falhas}

    def revisar(e, motivo, parte=com, decisor="Financeiro", categoria="DADOS"):
        pendencia(parte, f"REVISAO_PONTE:{e.origem.arquivo}:L{e.origem.linha}:{e.origem.ref}:{'DIV' if parte is div else 'COM'}",
            "DADO_PONTE_A_CONFERIR", [(e, None, None)], motivo, "NAO_INFORMADO", decisor=decisor,
            proximo="Confirmar os dados/contrato na origem, anexar aprovação quando necessária e reprocessar; não cobrar valor desconhecido.",
            categoria=categoria)

    for ref, repetidas in por_ref.items():
        e = repetidas[0]
        # Reconhecer a natureza do ajuste precede regras de negativos e de repetição.
        chave = lambda op: (op.contratacao, op.competencia, op.cnpj, op.spread_brl, op.spread_pct, op.ptax,
                            op.valor_me, referencia_ajuste(op).group(1) if referencia_ajuste(op) else "",
                            "APROVADO" if op.status in {"APROVADO", "APROVADO C/ RESSALVA"} else op.status)
        if ref in refs_invalidas or any(chave(op) != chave(e) for op in repetidas[1:]):
            for op in repetidas:
                revisar(op, "Nº Operação repetido com conteúdo financeiro conflitante; nenhuma ocorrência escolhida")
            pendentes += len(repetidas); div_pendentes += len(repetidas)
            div.situacao = "PROVISORIO"
            div.motivos.append(f"{ref}: conflito financeiro entre ocorrências")
            continue
        for duplicada in repetidas[1:]:
            pendencia(com, f"DUPLICATA_PONTE:{duplicada.origem.arquivo}:L{duplicada.origem.linha}:{ref}",
                "RELATORIO_PONTE_DUPLICADO", [(duplicada, duplicada.spread_brl, None)],
                "RN-34: operação repetida calculada uma vez; solicitar correção do relatório à Ponte.", "SPREAD_REPORTADO_DUPLICADO")
        pendentes += len(repetidas) - 1; div_pendentes += len(repetidas) - 1
        if e.status not in {"APROVADO", "APROVADO C/ RESSALVA"}:
            revisar(e, "Status Compliance não reconhecido; não supor aprovação")
            pendentes += 1; div_pendentes += 1
            div.situacao = "PROVISORIO"
            continue
        contrato, motivo = resolver(e, contratos)
        if contratos is not None and not any(c.cnpj == e.cnpj for c in contratos):
            cadastro[e.cnpj].append((e, e.spread_brl, None))
        ajustada = referencia_ajuste(e)
        if e.observacao.upper().startswith("AJUSTE REF"):
            if not ajustada or ajustada.group(1) == ref or e.spread_brl >= 0:
                revisar(e, "Ajuste sem referência original válida, com mesmo Nº da original ou sem Spread R$ negativo")
                pendentes += 1; div_pendentes += 1
                div.situacao = "PROVISORIO"
                continue
            original = ajustada.group(1)
            conhecidas = por_ref.get(original, [])
            if conhecidas and (any(o.cnpj != e.cnpj or o.contratacao > e.contratacao or referencia_ajuste(o) for o in conhecidas)
                               or any(chave(o) != chave(conhecidas[0]) for o in conhecidas)):
                revisar(e, "Ajuste referencia operação incompatível ou conflitante")
                pendentes += 1; div_pendentes += 1
                div.situacao = "PROVISORIO"
                continue
            valor = centavos(e.spread_brl * fracao)
            arquivo_original = conhecidas[0].origem.arquivo if conhecidas else ""
            pendencia(com, f"AJUSTE_D10:{e.origem.arquivo}:L{e.origem.linha}:{ref}", "AJUSTE_PONTE_D10_PENDENTE",
                [(e, valor, None)], "D-10: time usa participação sobre Spread R$ negativo; natureza do ajuste ainda aguarda confirmação financeira.",
                "PARTICIPACAO_AJUSTE_D10", proximo="Financeiro deve confirmar se Spread R$ representa spread integral ou participação; revisar antes de liberar.",
                reportado=e.spread_brl, ref_original=original, arquivo_original=arquivo_original)
            regra = "D-10_PENDENTE_FINANCEIRO"
        elif e.spread_brl < 0:
            # D-11 usa o spread realizado do relatório, não recalcula esse valor pelo %.
            try:
                pedido = (centavos(e.spread_brl - contrato.spread * e.ptax * e.valor_me)
                          if contrato and e.ptax is not None and e.ptax > 0 and e.valor_me is not None and e.valor_me > 0 else None)
            except DecimalException:
                pedido = None
            pendencia(com, f"SPREAD_NEGATIVO:{e.origem.arquivo}:L{e.origem.linha}:{ref}", "CONTESTACAO_SPREAD_NEGATIVO",
                [(e, pedido, contrato)], "RN-35/D-11: spread negativo excluído da comissão; pedido = realizado menos spread do contrato. "
                + ("Contrato/PTAX/valor ME indisponível; pedido desconhecido, sem estimativa." if pedido is None else "Dois valores identificados para revisão."),
                "DIFERENCA_ATE_CONTRATO", reportado=e.spread_brl, solicitado=pedido)
            pendentes += 1; div_pendentes += 1
            continue
        else:
            valor, original, arquivo_original, regra = centavos(e.spread_brl * fracao), "", "", "RN-31_REALIZADO"
            if contrato is None or e.spread_pct is None or e.ptax is None or e.ptax <= 0 or e.valor_me is None or e.valor_me <= 0:
                revisar(e, motivo or "Spread %/PTAX/valor ME indisponível; comparação contratual não estimada", div,
                        decisor="Comercial" if contrato is None else "Financeiro",
                        categoria="NEGOCIO" if contrato is None else "DADOS")
                div_pendentes += 1
            else:
                try:
                    div_calculadas += 1
                    delta = e.spread_pct - contrato.spread
                    if abs(delta) > tolerancia:
                        diferenca = centavos(delta * e.ptax * e.valor_me)
                        identificador = f"DIVERGENCIA:REMESSA:{e.origem.arquivo}:{ref}"
                        div.linhas["divergencias_taxa.csv"].append(dict(id_saida=identificador, cnpj=e.cnpj, linha_negocio="REMESSA",
                            ref_origem=ref, taxa_contratada_pct=format(contrato.spread * 100, "f"),
                            taxa_aplicada_pct=format(e.spread_pct * 100, "f"), diferenca_brl=format(diferenca, ".2f")))
                        div.rastro.append(rastro(e, identificador, diferenca, "DIVERGENCIA_SPREAD", "RN-28_D-02_D-05", contrato))
                        cobrancas[e.competencia, e.cnpj].append((e, diferenca, contrato))
                except DecimalException:
                    div_calculadas -= 1
                    div_pendentes += 1
                    revisar(e, "Valores contratuais fora da precisão suportada; comissão realizada preservada", div)
        competencia = e.competencia
        grupos[competencia, e.cnpj].append((e, valor, regra, original, arquivo_original))
        acompanhamento[competencia, e.cnpj].append((e, valor, None))
        calculadas += 1
        if ajustada:
            div_calculadas += 1  # ajuste explicado; não é divergência de taxa nova
    for (competencia, cnpj), itens in sorted(grupos.items()):
        identificador = f"REMESSA:{competencia}:{cnpj}"
        com.linhas["comissoes_por_lojista.csv"].append(dict(id_saida=identificador, cnpj=cnpj, lojista=itens[0][0].cliente,
            linha_negocio="REMESSA", comissao_brl=format(sum((v for _, v, _, _, _ in itens), Decimal(0)), ".2f")))
        com.rastro.extend(rastro(e, identificador, v, "PARTICIPACAO_REALIZADA", regra,
                                ref_original=original, arquivo_original=arquivo) for e, v, regra, original, arquivo in itens)
        pendencia(com, f"ACOMPANHAMENTO_PONTE:{competencia}:{cnpj}", "ACOMPANHAMENTO_REPASSE_PONTE",
            acompanhamento[competencia, cnpj], "RN-39: conferir o repasse efetivo quando cair, sem supor desconto pela Ponte; valor é participação calculada, não TED estimado.",
            "PARTICIPACAO_A_CONFERIR", proximo="Financeiro deve conferir o TED efetivo com a participação validada; não registrar recebimento estimado.")
    for cnpj, itens in sorted(cadastro.items()):
        pendencia(com, f"CADASTRO_PONTE:{cnpj}", "CADASTRO_REMESSA_PENDENTE", itens,
            "RN-40: CNPJ sem cadastro contratual disponível; participação pelo realizado preservada.", "SPREAD_REPORTADO_CADASTRO",
            decisor="Comercial", proximo="Confirmar cadastro e spread vigente; anexar aprovação e reprocessar a comparação.")
    for (competencia, cnpj), itens in sorted(cobrancas.items()):
        pendencia(div, f"CONTESTACAO_PONTE:{competencia}:{cnpj}", "CONTESTACAO_SPREAD_CONTRATUAL", itens,
            "RN-28/RN-36/D-05: diferença pelo percentual e valor cheio; participação continua pelo realizado. Dentro do prazo (RN-41).",
            "DIFERENCA_SPREAD_CONTRATUAL")
    for p in falhas:
        identificador = f"LEITURA_PONTE:{p.origem.arquivo}:L{p.origem.linha}:{p.origem.ref}"
        com.linhas["pendencias.csv"].append(dict(id_saida=identificador, tipo="DADO_PONTE_INVALIDO", ref_origem=p.origem.ref,
            valor_brl="", motivo=p.motivo, quem_decide="Financeiro", proximo_passo="Corrigir a linha do anexo e reprocessar.",
            arquivo_origem=p.origem.arquivo, linha_origem=str(p.origem.linha), cnpj="", categoria="DADOS", natureza_valor="NAO_INFORMADO"))
    if falhas:
        com.situacao = div.situacao = "PROVISORIO"
        com.motivos.append("Há linhas inválidas no anexo Ponte")
        div.motivos.append("Comparação limitada às operações legíveis")
    if div.situacao == "PROVISORIO" and not div.motivos:
        div.motivos.append("Há operações não comparadas; consultar pendências e revisar os dados da Ponte")
    com.cobertura = dict(linhas_lidas=quantidade, calculadas=calculadas, pendentes=pendentes + len(falhas), bloqueadas=0)
    div.cobertura = dict(linhas_lidas=quantidade, calculadas=div_calculadas, pendentes=div_pendentes + len(falhas), bloqueadas=0)
    return com, div
