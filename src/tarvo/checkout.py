"""Checkout: eventos assinados, vigência original e reversões por referência."""

from collections import Counter, defaultdict
from dataclasses import replace
from decimal import Decimal, ROUND_HALF_UP

from .cadastro import identificar, resolver
from .modelos import Cadastro, Contribuicao, Evento, Pendencia


def selecionar_faixa(evento: Evento, modalidades: dict) -> str | None:
    if evento.tipo in {"ANTECIPACAO", "REVERSAO ANTECIPACAO"}:
        return "antecipacao"
    faixa = modalidades.get(evento.modalidade)
    if faixa == "parcelado":
        if evento.parcelas is not None and 2 <= evento.parcelas <= 6:
            return "parcelado_2_6"
        if evento.parcelas is not None and 7 <= evento.parcelas <= 12:
            return "parcelado_7_12"
        return None
    return faixa if evento.parcelas in (0, 1) else None


def conferir_estorno(evento: Evento, por_ref: dict, totais_estornados: dict) -> str:
    if not evento.referencia or evento.data_original is None:
        return "Estorno sem referência ou data da venda original"
    if evento.data_original > evento.data:
        return "Data da venda original posterior ao estorno"
    original = por_ref.get(evento.referencia)
    if original is None:
        # O case inclui vendas do mês anterior que não estão no arquivo atual.
        if evento.data_original.strftime("%Y-%m") == evento.data.strftime("%Y-%m"):
            return "Venda referenciada do mês ausente; não foi possível conferir a relação"
        return ""
    if original.tipo != "VENDA" or original.ec != evento.ec or original.bruto <= 0:
        return "Estorno referencia evento de tipo, lojista ou sinal incompatível"
    if original.data != evento.data_original:
        return "Data original do estorno difere da venda referenciada"
    if totais_estornados[evento.referencia] > original.bruto:
        return "Total estornado excede a venda referenciada; conferir possíveis duplicidades"
    return ""


def calcular(eventos: list[Evento], cadastro: Cadastro, regras: dict):
    contribuicoes, pendencias = [], []
    por_ref = {e.origem.ref: e for e in eventos}
    quantidades_reversao = Counter(e.referencia for e in eventos if e.tipo == "REVERSAO ANTECIPACAO")
    totais_estornados = defaultdict(lambda: Decimal(0))
    for evento in eventos:
        if evento.tipo == "ESTORNO" and evento.bruto < 0:
            totais_estornados[evento.referencia] += -evento.bruto
    antecipacoes_calculadas = {}
    # Original primeiro, sem depender da posição física no arquivo.
    ordenados = [e for e in eventos if e.tipo != "REVERSAO ANTECIPACAO"]
    ordenados += [e for e in eventos if e.tipo == "REVERSAO ANTECIPACAO"]
    for evento in ordenados:
        identidade, problema_identidade = identificar(evento.ec, cadastro, regras)

        def pendente(motivo, responsavel="Financeiro"):
            pendencias.append(Pendencia(
                evento.origem, motivo, responsavel, evento.bruto,
                identidade.cnpj if identidade else None, identidade.origem if identidade else None,
                identidade.vinculo if identidade else "",
            ))

        bloqueios = [b for b in regras.get("contratos_bloqueados", [])
                     if identidade and b["cnpj"] == identidade.cnpj]
        if bloqueios:
            pendente("; ".join(b["motivo"] for b in bloqueios), "Comercial")
            continue
        if evento.tipo not in {"VENDA", "ESTORNO", "ANTECIPACAO", "REVERSAO ANTECIPACAO"}:
            pendente("Tipo de evento não reconhecido no checkout")
            continue
        if identidade is None:
            pendente(problema_identidade, "Comercial")
            continue
        negativo = evento.tipo in {"ESTORNO", "REVERSAO ANTECIPACAO"}
        if (negativo and evento.bruto >= 0) or (not negativo and evento.bruto <= 0):
            pendente("Sinal do valor bruto incompatível com o tipo de evento")
            continue
        if evento.tipo == "REVERSAO ANTECIPACAO":
            original = por_ref.get(evento.referencia)
            calculada = antecipacoes_calculadas.get(evento.referencia)
            if not evento.referencia or original is None:
                pendente("Antecipação referenciada ausente; reversão não reconstruída por estimativa")
            elif quantidades_reversao[evento.referencia] != 1:
                pendente("Múltiplas reversões da mesma antecipação; requer decisão humana")
            elif original.tipo != "ANTECIPACAO" or original.ec != evento.ec:
                pendente("Reversão referencia tipo ou lojista incompatível")
            elif evento.data_original != original.data or original.data > evento.data:
                pendente("Data original da reversão ausente ou incompatível com a antecipação")
            elif evento.bruto != -original.bruto:
                pendente("Reversão não corresponde ao bruto integral da antecipação; caso parcial não confirmado")
            elif calculada is None:
                pendente("Antecipação referenciada não pôde ser calculada; reversão também pendente")
            else:
                contribuicoes.append(replace(
                    calculada, origem=evento.origem, competencia=evento.data.strftime("%Y-%m"),
                    valor=-calculada.valor, tipo=evento.tipo, ref_original=original.origem.ref,
                    arquivo_original=original.origem.arquivo,
                ))
            continue
        faixa = selecionar_faixa(evento, regras["modalidades"])
        if faixa is None:
            pendente("Modalidade ou faixa não suportada (acima de 12x ou parcelas inconsistentes)")
            continue
        if evento.tipo == "ESTORNO":
            problema = conferir_estorno(evento, por_ref, totais_estornados)
            data_base = evento.data_original
        else:
            problema = ""
            data_base = evento.data
            if evento.referencia or (evento.data_original is not None and evento.data_original != evento.data):
                problema = "Evento positivo com referência temporal não suportada; requer esclarecimento"
        if problema:
            pendente(problema)
            continue
        contrato, motivo = resolver(identidade, data_base, cadastro, regras)
        if contrato is None:
            pendente(motivo, "Comercial")
            continue
        contratada = contrato.taxas.get(faixa)
        isencoes = [i for i in regras.get("isencoes", []) if i["cnpj"] == identidade.cnpj
                    and i["inicio"] <= data_base <= i["fim"]]
        if len(isencoes) > 1:
            pendente("Isenções sobrepostas", "Comercial")
            continue
        regra = isencoes[0]["id"] if isencoes else "PLANILHA"
        if isencoes:
            contratada = Decimal(0)
        if contratada is None:
            pendente("Taxa contratada ausente ou com formato não reconhecido", "Comercial")
            continue
        valor = (evento.bruto * contratada).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        original = por_ref.get(evento.referencia)
        contribuicao = Contribuicao(
            evento.origem, contrato.origem, identidade.cnpj, identidade.nome,
            evento.data.strftime("%Y-%m"), contratada, valor, faixa, regra, identidade.vinculo,
            evento.tipo, data_base, evento.referencia, original.origem.arquivo if original else "",
        )
        contribuicoes.append(contribuicao)
        if evento.tipo == "ANTECIPACAO":
            antecipacoes_calculadas[evento.origem.ref] = contribuicao
    return contribuicoes, pendencias
