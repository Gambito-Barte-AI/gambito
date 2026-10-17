"""CSV Orbe com ponto e vírgula, decimal brasileiro e referências estáveis."""

import csv
from collections import defaultdict
from dataclasses import replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from hashlib import sha256
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


def descobrir(pasta: Path) -> list[Path]:
    candidatos, falhas = [], []
    for caminho in sorted(pasta.glob("*.csv")):
        try:
            cabecalho = next(csv.reader(StringIO(texto_csv(caminho)), delimiter=";"), [])
        except (OSError, UnicodeError, csv.Error) as exc:
            falhas.append(f"{caminho.name}: leitura CSV falhou: {exc}")
            continue  # um CSV alheio ao checkout não bloqueia uma Orbe identificada
        if "id_transacao" in cabecalho or len(COLUNAS.intersection(cabecalho)) >= 3:
            candidatos.append(caminho)
    if not candidatos:
        nomes = ", ".join(p.name for p in candidatos) or "nenhum"
        detalhes = "; ".join(falhas)
        raise ErroEntrada(f"Orbe: esperado CSV com coluna id_transacao; candidatos: {nomes}. {detalhes}")
    return candidatos


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
                if None in linha or any(v is None for v in linha.values()):
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
                    dinheiro_br(linha["valor_taxa"].strip()) if (linha.get("valor_taxa") or "").strip() else None,
                ))
            except (ValueError, InvalidOperation) as exc:
                pendencias.append(Pendencia(origem, f"Linha inválida: {exc}", "Financeiro"))
        return eventos, pendencias, quantidade
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ErroEntrada(f"{caminho.name}: CSV inválido: {exc}") from exc


def ler_pasta(pasta: Path, competencia: str | None = None):
    """Une fontes antes das referências; conflitos nunca escolhem um valor financeiro."""
    eventos, pendencias, arquivos, avisos = [], [], [], []
    recebidas = fora_competencia = 0
    for caminho in descobrir(pasta):
        fonte = {"arquivo": caminho.name, "sha256": sha256(caminho.read_bytes()).hexdigest()}
        try:
            lidos, problemas, quantidade = ler(caminho)
            recebidas += quantidade
            selecionados = [e for e in lidos if competencia is None or e.data.strftime("%Y-%m") == competencia]
            fora_competencia += len(lidos) - len(selecionados)
            eventos.extend(selecionados)
            pendencias.extend(problemas)
            fonte.update(situacao="DISPONIVEL", linhas=quantidade)
        except (ErroEntrada, OSError) as exc:
            fonte.update(situacao="BLOQUEADO", motivo=str(exc))
            avisos.append(str(exc))
        arquivos.append(fonte)
    fonte = {"situacao": "PROVISORIO" if avisos else "DISPONIVEL", "arquivos": arquivos}
    if not any(a["situacao"] == "DISPONIVEL" for a in arquivos):
        fonte["situacao"] = "BLOQUEADO"
    competencias = sorted({e.data.strftime("%Y-%m") for e in eventos})
    grupos = defaultdict(list)
    for evento in eventos:
        grupos[evento.origem.ref].append(evento)
    invalidos = {p.origem.ref for p in pendencias}
    conflitos, unicos = set(invalidos), []
    duplicadas = 0
    for ref, grupo in sorted(grupos.items()):
        primeiro = grupo[0]
        conflitante = ref in invalidos or any(replace(e, origem=primeiro.origem) != primeiro for e in grupo[1:])
        if conflitante:
            conflitos.add(ref)
        else:
            unicos.append(primeiro)
        repetidos = grupo if conflitante else grupo[1:]
        duplicadas += len(grupo) - 1
        origens = ", ".join(f"{e.origem.arquivo}:L{e.origem.linha}" for e in grupo)
        for evento in repetidos:
            pendencias.append(Pendencia(
                evento.origem, f"ID duplicado {'com conteúdo conflitante' if conflitante else 'idêntico, contado uma vez'}: {origens}",
                "Financeiro", evento.bruto, tipo="DUPLICIDADE",
                proximo_passo="Confirmar o registro válido com a Orbe; remover a duplicidade ou corrigir o conflito e reprocessar.",
                valor_orbe=evento.valor_taxa,
            ))
    # Não tratar uma referência conflitante como venda histórica simplesmente ausente.
    eventos = []
    for evento in unicos:
        if evento.referencia in conflitos:
            pendencias.append(Pendencia(
                evento.origem, "Referência original com ID conflitante entre arquivos", "Financeiro", evento.bruto,
                tipo="REFERENCIA_CONFLITANTE", valor_orbe=evento.valor_taxa,
            ))
        else:
            eventos.append(evento)
    ingestao = {"linhas_recebidas": recebidas, "fora_competencia": fora_competencia,
                "competencias": competencias,
                "ocorrencias_duplicadas": duplicadas, "ids_conflitantes": sorted(conflitos)}
    return eventos, pendencias, recebidas - fora_competencia, fonte, avisos, ingestao
