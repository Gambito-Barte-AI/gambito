"""Plano Fênix: identificação pelo cabeçalho e leitura sem alterar a fonte."""

import csv
from io import StringIO
from pathlib import Path
import re

from .orbe import texto_csv
from ..modelos import ContaContabil, ErroEntrada, Origem

COLUNAS = {"COD_CONTA", "DESCRICAO", "TIPO", "NATUREZA", "ACEITA_LANCTO", "COD_SUPERIOR", "DT_CRIACAO"}


def descobrir(pasta: Path) -> Path:
    candidatos = []
    for p in sorted(pasta.glob("*.csv")):
        try:
            cabecalho = next(csv.reader(StringIO(texto_csv(p)), delimiter=";"), [])
        except (OSError, UnicodeError, csv.Error):
            continue
        if "COD_CONTA" in cabecalho or len(COLUNAS.intersection(cabecalho)) >= 3:
            candidatos.append(p)
    if len(candidatos) != 1:
        raise ErroEntrada(f"Plano de contas: esperado um CSV por cabeçalho; encontrados {len(candidatos)}")
    return candidatos[0]


def ler(caminho: Path) -> dict[str, ContaContabil]:
    try:
        leitor = csv.DictReader(StringIO(texto_csv(caminho)), delimiter=";", strict=True)
        if (not COLUNAS <= set(leitor.fieldnames or [])
                or len(leitor.fieldnames) != len(set(leitor.fieldnames))):
            raise ValueError("cabeçalho do plano incompatível")
        contas = {}
        for linha in leitor:
            numero = leitor.line_num
            if None in linha or any(v is None for v in linha.values()):
                raise ValueError(f"L{numero}: quantidade de campos inválida")
            linha = {k: v.strip() for k, v in linha.items()}
            codigo = linha["COD_CONTA"]
            if (not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", codigo) or codigo in contas
                    or not linha["DESCRICAO"] or linha["TIPO"] not in {"SINTETICA", "ANALITICA"}
                    or linha["ACEITA_LANCTO"] not in {"S", "N"} or linha["NATUREZA"] not in {"D", "C"}):
                raise ValueError(f"L{numero}: conta inválida ou código repetido")
            contas[codigo] = ContaContabil(Origem(caminho.name, f"L{numero}", numero), codigo,
                linha["DESCRICAO"], linha["TIPO"], linha["ACEITA_LANCTO"] == "S")
        if not contas:
            raise ValueError("plano vazio")
        return contas
    except (ValueError, OSError, UnicodeError, csv.Error) as exc:
        raise ErroEntrada(f"{caminho.name}: plano de contas: {exc}") from exc
