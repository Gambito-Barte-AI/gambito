"""Extrato Aurora: cabeçalho por conteúdo, referência pela linha física inicial."""

import csv
from io import StringIO
from pathlib import Path

from .orbe import texto_csv, dinheiro_br, data_br
from .taxas import normalizar
from ..modelos import ErroEntrada, MovimentoBanco, Origem

COLUNAS = {"data", "lancamento", "documento", "valor (r$)", "saldo (r$)"}


def descobrir(pasta: Path) -> Path:
    candidatos = []
    for p in sorted(pasta.glob("*.csv")):
        try:
            texto = texto_csv(p)
            leitor = csv.reader(StringIO(texto), delimiter=";", strict=True)
            if any(COLUNAS <= {normalizar(c) for c in linha} for linha in leitor):
                candidatos.append(p)
            elif normalizar(texto.splitlines()[0] if texto.splitlines() else "").startswith("banco aurora"):
                candidatos.append(p)  # fonte reconhecida com layout alterado: erro explícito no leitor
        except (OSError, UnicodeError, csv.Error):
            continue
    if len(candidatos) != 1:
        raise ErroEntrada(f"Aurora: esperado um CSV por conteúdo; encontrados {len(candidatos)}")
    return candidatos[0]


def ler(caminho: Path):
    try:
        leitor = csv.reader(StringIO(texto_csv(caminho), newline=""), delimiter=";", strict=True)
        cabecalho, movimentos, ignoradas = None, [], []
        while True:
            numero = leitor.line_num + 1
            try:
                linha = next(leitor)
            except StopIteration:
                break
            normalizada = [normalizar(c) for c in linha]
            if cabecalho is None:
                if COLUNAS <= set(normalizada):
                    if len(normalizada) != len(set(normalizada)):
                        raise ValueError(f"L{numero}: cabeçalho duplicado")
                    cabecalho = normalizada
                continue
            if not any(c.strip() for c in linha):
                ignoradas.append(dict(ref=f"L{numero}", motivo="LINHA_VAZIA"))
                continue
            campos = dict(zip(cabecalho, linha))
            descricao = campos.get("lancamento", "").strip()
            # Somente marcadores de saldo/rodapé conhecidos, sem valor de movimento.
            if (not campos.get("valor (r$)", "").strip()
                    and normalizar(descricao) in {"saldo anterior", "saldo final", "os lancamentos estao sujeitos a confirmacao."}
                    and len(linha) == len(cabecalho)):
                ignoradas.append(dict(ref=f"L{numero}", motivo="SALDO_OU_RODAPE"))
                continue
            erros, data, valor = [], None, None
            if len(linha) != len(cabecalho):
                erros.append("quantidade de campos incompatível com o cabeçalho")
            try:
                data = data_br(campos.get("data", "").strip())
            except ValueError:
                erros.append("data inválida")
            try:
                valor = dinheiro_br(campos.get("valor (r$)", "").strip())
            except ValueError:
                erros.append("valor de movimento inválido; não substituído por zero")
            if not descricao:
                erros.append("descrição ausente")
            movimentos.append(MovimentoBanco(Origem(caminho.name, f"L{numero}", numero), data,
                descricao, valor, "; ".join(erros)))
        if cabecalho is None:
            raise ValueError("cabeçalho Aurora não encontrado")
        return movimentos, dict(linhas_fisicas=leitor.line_num, ignoradas=ignoradas,
                               movimentos_lidos=len(movimentos))
    except (ValueError, OSError, UnicodeError, csv.Error) as exc:
        raise ErroEntrada(f"{caminho.name}: Aurora: {exc}") from exc
