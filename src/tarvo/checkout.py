"""Entrega 2: vendas por faixa e vigência; outros eventos ainda são pendências."""

from decimal import Decimal, ROUND_HALF_UP

from .cadastro import identificar, resolver
from .modelos import Cadastro, Contribuicao, Evento, Pendencia


def calcular(eventos: list[Evento], cadastro: Cadastro, regras: dict):
    contribuicoes, pendencias = [], []
    for evento in eventos:
        motivo, responsavel = "", "Financeiro"
        identidade, problema_identidade = identificar(evento.ec, cadastro, regras)
        faixa = regras["modalidades"].get(evento.modalidade)
        if faixa == "parcelado":
            faixa = ("parcelado_2_6" if evento.parcelas is not None and 2 <= evento.parcelas <= 6
                     else "parcelado_7_12" if evento.parcelas is not None and 7 <= evento.parcelas <= 12 else None)
        elif evento.parcelas not in (0, 1):
            faixa = None
        bloqueios = [b for b in regras.get("contratos_bloqueados", [])
                     if identidade and b["cnpj"] == identidade.cnpj]
        if bloqueios:
            motivo, responsavel = "; ".join(b["motivo"] for b in bloqueios), "Comercial"
        elif evento.tipo != "VENDA":
            motivo = "Tipo de evento reservado às próximas entregas do mínimo"
        elif faixa is None:
            motivo = "Modalidade ou faixa não suportada (acima de 12x ou parcelas inconsistentes)"
        elif evento.bruto <= 0 or evento.referencia or (
            evento.data_original is not None and evento.data_original != evento.data
        ):
            motivo = "Venda com sinal ou referência temporal não suportados nesta entrega"
        elif identidade is None:
            motivo, responsavel = problema_identidade, "Comercial"
        else:
            contrato, motivo = resolver(identidade, evento.data, cadastro, regras)
            responsavel = "Comercial"
            if contrato is not None:
                contratada = contrato.taxas[faixa]
                isencoes = [i for i in regras.get("isencoes", []) if i["cnpj"] == identidade.cnpj
                            and i["inicio"] <= evento.data <= i["fim"]]
                if len(isencoes) > 1:
                    pendencias.append(Pendencia(evento.origem, "Isenções sobrepostas", "Comercial",
                                                evento.bruto, identidade.cnpj, identidade.origem, identidade.vinculo))
                    continue
                regra = isencoes[0]["id"] if isencoes else "PLANILHA"
                if isencoes:
                    contratada = Decimal(0)
                if contratada is None:
                    motivo = "Taxa contratada ausente ou com formato não reconhecido"
                else:
                    valor = (evento.bruto * contratada).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    contribuicoes.append(Contribuicao(
                        evento.origem, contrato.origem, identidade.cnpj, identidade.nome,
                        evento.data.strftime("%Y-%m"), contratada, valor, faixa, regra, identidade.vinculo,
                    ))
                    continue
        pendencias.append(Pendencia(
            evento.origem, motivo, responsavel, evento.bruto,
            identidade.cnpj if identidade else None, identidade.origem if identidade else None,
            identidade.vinculo if identidade else "",
        ))
    return contribuicoes, pendencias
