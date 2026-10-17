"""CSV Orbe com ponto e vírgula, decimal brasileiro e referências estáveis."""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
import re

from ..modelos import ErroEntrada, Evento, Origem, Pendencia

COLUNAS = {
    "id_transacao", "data_movimento", "cod_estabelecimento", "tipo_lancamento",
    "modalidade", "qtd_parcelas", "valor_bruto", "id_referencia", "data_venda_original",
}


def texto_csv(caminho: Path) -> str:
    dados = caminho.read_bytes()
    try:
        return dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        return dados.decode("cp1252")


def descobrir(pasta: Path) -> Path:
    candidatos, falhas = [], []
    for caminho in sorted(pasta.glob("*.csv")):
        try:
            cabecalho = next(csv.reader(StringIO(texto_csv(caminho)), delimiter=";"), [])
        except (OSError, UnicodeError, csv.Error) as exc:
            falhas.append(f"{caminho.name}: leitura CSV falhou: {exc}")
            continue  # um CSV alheio ao checkout não bloqueia uma Orbe identificada
        if "id_transacao" in cabecalho:
            candidatos.append(caminho)
    if len(candidatos) != 1:
        nomes = ", ".join(p.name for p in candidatos) or "nenhum"
        detalhes = "; ".join(falhas)
        raise ErroEntrada(f"Orbe: esperado um CSV com coluna id_transacao; candidatos: {nomes}. {detalhes}")
    return candidatos[0]


def data_br(valor: str):
    return datetime.strptime(valor, "%d/%m/%Y").date()


def dinheiro_br(valor: str) -> Decimal:
    if not re.fullmatch(r"-?(?:\d+|\d{1,3}(?:\.\d{3})+),\d{2}", valor):
        raise ValueError("valor_bruto deve ter formato brasileiro com duas casas decimais")
    numero = Decimal(valor.replace(".", "").replace(",", "."))
    if not numero.is_finite():
        raise ValueError("valor_bruto não finito")
    return numero


def ler(caminho: Path) -> tuple[list[Evento], list[Pendencia], int]:
    try:
        leitor = csv.DictReader(StringIO(texto_csv(caminho)), delimiter=";", strict=True)
        cabecalho = leitor.fieldnames or []
        faltantes = COLUNAS - set(cabecalho)
        if faltantes or len(cabecalho) != len(set(cabecalho)):
            raise ErroEntrada(f"{caminho.name}: cabeçalho inválido; colunas ausentes: {sorted(faltantes)}")
        eventos, pendencias, vistos = [], [], set()
        quantidade = 0
        for linha in leitor:
            quantidade += 1
            fisica = leitor.line_num
            ref = (linha.get("id_transacao") or "").strip()
            if not ref or ref in vistos:
                raise ErroEntrada(f"{caminho.name}: L{fisica}: id_transacao ausente ou duplicado: {ref!r}")
            vistos.add(ref)
            origem = Origem(caminho.name, ref, fisica)
            try:
                if None in linha or any(linha[k] is None for k in COLUNAS):
                    raise ValueError("quantidade de campos diferente do cabeçalho")
                data = data_br(linha["data_movimento"].strip())
                ec = linha["cod_estabelecimento"].strip()
                if not re.fullmatch(r"[0-9]+", ec):
                    raise ValueError("EC ausente ou inválido")
                texto_parcelas = linha["qtd_parcelas"].strip()
                if texto_parcelas and not re.fullmatch(r"[0-9]+", texto_parcelas):
                    raise ValueError("qtd_parcelas deve ser inteiro não negativo ou vazio")
                parcelas = int(texto_parcelas) if texto_parcelas else None
                original = linha["data_venda_original"].strip()
                eventos.append(Evento(
                    origem, data, ec, linha["tipo_lancamento"].strip(),
                    linha["modalidade"].strip(), parcelas, dinheiro_br(linha["valor_bruto"].strip()),
                    linha["id_referencia"].strip(), data_br(original) if original else None,
                ))
            except (ValueError, InvalidOperation) as exc:
                pendencias.append(Pendencia(origem, f"Linha inválida: {exc}", "Financeiro"))
        return eventos, pendencias, quantidade
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ErroEntrada(f"{caminho.name}: CSV inválido: {exc}") from exc
