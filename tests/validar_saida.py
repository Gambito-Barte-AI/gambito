"""Auditoria independente das saídas do mínimo; usa somente a biblioteca padrão."""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
import tomllib


class ErroAceite(ValueError):
    """Artefato incompatível com as entradas ou com o contrato de saída."""


def exigir(condicao, mensagem):
    if not condicao:
        raise ErroAceite(mensagem)


def dinheiro(texto):
    exigir(isinstance(texto, str) and re.fullmatch(r"-?[0-9]+\.[0-9]{2}", texto),
           f"Valor monetário fora do formato: {texto!r}")
    return Decimal(texto)


def ler_csv(caminho, obrigatorias):
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";", strict=True)
        colunas = leitor.fieldnames or []
        exigir(obrigatorias <= set(colunas) and len(colunas) == len(set(colunas)),
               f"{caminho.name}: cabeçalho inválido")
        linhas = list(leitor)
        exigir(all(None not in l and all(v is not None for v in l.values()) for l in linhas),
               f"{caminho.name}: linha com quantidade de campos incorreta")
        return linhas


def verificar(dados: Path, saida: Path, regras: Path, esperar=None):
    manifesto = json.loads((saida / "manifesto.json").read_text(encoding="utf-8"))
    exigir(isinstance(manifesto, dict), "Manifesto não é objeto")
    situacao = manifesto.get("situacao")
    exigir(situacao in {"COMPLETO", "PROVISORIO", "BLOQUEADO"}, "Situação não reconhecida")
    if esperar:
        exigir(situacao == esperar, f"Esperado {esperar}, encontrado {situacao}")
    configuracao = tomllib.loads(regras.read_text(encoding="utf-8"))
    exigir(manifesto.get("decisoes_financeiras_pendentes") == configuracao.get("decisoes_pendentes", []),
           "Decisões financeiras pendentes foram omitidas ou alteradas")
    if situacao == "BLOQUEADO":
        exigir(manifesto.get("arquivos") == {} and manifesto.get("rastro_validado") is False
               and manifesto.get("total_parcial_brl") is None and manifesto.get("motivos"),
               "Bloqueio apresenta arquivos ou valores como válidos")
        return {"situacao": situacao, "motivos": manifesto["motivos"], "arquivos_validos": 0}

    nomes = {"comissoes_por_lojista.csv", "rastro.csv"}
    exigir(set(manifesto.get("arquivos", {})) == nomes, "Lista de arquivos diferente do mínimo")
    exigir(manifesto.get("rastro_validado") is True, "Rastro não marcado como validado")
    for nome, digest in manifesto["arquivos"].items():
        exigir(sha256((saida / nome).read_bytes()).hexdigest() == digest, f"Hash de {nome} não confere")
    fontes = manifesto.get("fontes", {})
    exigir(set(fontes) == {"orbe", "taxas", "regras"}, "Dependências do mínimo não identificadas")
    for nome, fonte in fontes.items():
        arquivo = fonte.get("arquivo", "")
        exigir(arquivo and Path(arquivo).name == arquivo and fonte.get("situacao") == "DISPONIVEL",
               f"Fonte inválida: {nome}")
        caminho = regras if nome == "regras" else dados / arquivo
        exigir(sha256(caminho.read_bytes()).hexdigest() == fonte.get("sha256"), f"Fonte {nome} mudou")

    arquivo_orbe = fontes["orbe"]["arquivo"]
    original = dados / arquivo_orbe
    bruto = original.read_bytes()
    try:
        texto = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = bruto.decode("cp1252")
    from io import StringIO
    origem = list(csv.DictReader(StringIO(texto), delimiter=";", strict=True))
    ids_origem = [l.get("id_transacao", "").strip() for l in origem]
    exigir(all(ids_origem) and len(set(ids_origem)) == len(ids_origem), "IDs de entrada ausentes/duplicados")
    por_ref = dict(zip(ids_origem, origem))
    comissoes = ler_csv(saida / "comissoes_por_lojista.csv",
                        {"id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"})
    rastros = ler_csv(saida / "rastro.csv", {"id_saida", "arquivo_origem", "ref_origem", "valor"})
    pendencias = manifesto.get("pendencias", [])
    exigir(isinstance(pendencias, list), "Pendências inválidas")
    for p in pendencias:
        exigir(all(p.get(k) for k in ("ref_origem", "motivo", "quem_decide"))
               and p.get("arquivo_origem") == arquivo_orbe, "Pendência sem origem, motivo ou responsável")

    destinos = [l["ref_origem"] for l in rastros] + [p["ref_origem"] for p in pendencias]
    exigir(Counter(destinos) == Counter(ids_origem), "Entrada sem destino, duplicada ou com referência inventada")
    cobertura = manifesto.get("cobertura", {})
    exigir(cobertura == {"linhas_lidas": len(origem), "calculadas": len(rastros),
                         "pendentes": len(pendencias), "bloqueadas": 0}, "Cobertura declarada não corresponde aos arquivos")
    exigir((situacao == "PROVISORIO") == bool(pendencias), "Situação omite pendências ou as declara sem registros")
    ids = [l["id_saida"] for l in comissoes]
    exigir(len(set(ids)) == len(ids), "IDs de saída duplicados")
    exigir(len({l["cnpj"] for l in comissoes}) == len(comissoes), "CNPJ duplicado nas comissões do mês")
    por_saida = {l["id_saida"]: l for l in comissoes}
    somas = defaultdict(lambda: Decimal(0))
    por_rastro = {l["ref_origem"]: l for l in rastros}
    competencia = manifesto.get("competencia")
    exigir(isinstance(competencia, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}", competencia),
           "Competência inválida")
    for linha in comissoes:
        exigir(re.fullmatch(r"[0-9]{14}", linha["cnpj"]) and linha["lojista"].strip()
               and linha["linha_negocio"] == "CHECKOUT", "Domínio da comissão inválido")
        dinheiro(linha["comissao_brl"])
    for linha in rastros:
        exigir(linha["arquivo_origem"] == arquivo_orbe and linha["id_saida"] in por_saida,
               "Rastro aponta para arquivo ou saída inexistentes")
        somas[linha["id_saida"]] += dinheiro(linha["valor"])
        evento = por_ref[linha["ref_origem"]]
        exigir(linha.get("tipo_lancamento") == evento["tipo_lancamento"], "Rastro mudou tipo de evento")
        movimento = datetime.strptime(evento["data_movimento"], "%d/%m/%Y").date()
        exigir(movimento.strftime("%Y-%m") == competencia, "Competência não corresponde ao movimento de origem")
        if evento["tipo_lancamento"] in {"ESTORNO", "REVERSAO ANTECIPACAO"}:
            exigir(linha.get("ref_evento_original") == evento["id_referencia"], "Referência original perdida")
        if evento["tipo_lancamento"] == "REVERSAO ANTECIPACAO":
            anterior = por_rastro.get(evento["id_referencia"])
            exigir(anterior is not None and anterior["tipo_lancamento"] == "ANTECIPACAO"
                   and anterior["id_saida"] == linha["id_saida"]
                   and dinheiro(anterior["valor"]) + dinheiro(linha["valor"]) == 0,
                   "Reversão não anula sua antecipação")
        base = (datetime.strptime(evento["data_venda_original"], "%d/%m/%Y").date()
                if evento["tipo_lancamento"] in {"ESTORNO", "REVERSAO ANTECIPACAO"} else movimento)
        exigir(linha.get("data_base_taxa") and date.fromisoformat(linha["data_base_taxa"]) == base,
               "Data base não corresponde ao evento de origem")
    exigir(set(somas) == set(ids), "Comissão sem rastro ou rastro sem comissão")
    exigir(all(somas[l["id_saida"]] == dinheiro(l["comissao_brl"]) for l in comissoes),
           "Soma do rastro não corresponde à comissão")
    total = sum((dinheiro(l["comissao_brl"]) for l in comissoes), Decimal(0))
    exigir(total == dinheiro(manifesto.get("total_parcial_brl")), "Total do manifesto não confere")
    return {"situacao": situacao, "competencia": manifesto.get("competencia"),
            "cobertura": cobertura, "comissoes": len(comissoes), "total_brl": format(total, ".2f"),
            "rastro_exato": True, "fontes_e_hashes": True, "decisoes_preservadas": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", required=True, type=Path)
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--regras", required=True, type=Path)
    parser.add_argument("--esperar", choices=["COMPLETO", "PROVISORIO", "BLOQUEADO"])
    args = parser.parse_args()
    try:
        resultado = verificar(args.dados, args.saida, args.regras, args.esperar)
    except (ValueError, OSError, KeyError, TypeError, csv.Error) as exc:
        parser.exit(1, f"ACEITE REPROVADO: {exc}\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
