"""Configuração explícita de vínculos e condições, com origem documentada."""

from datetime import date
from pathlib import Path
import re
import tomllib

from .modelos import ErroEntrada


def carregar(caminho: Path) -> dict:
    try:
        with caminho.open("rb") as arquivo:
            regras = tomllib.load(arquivo)
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ErroEntrada(f"{caminho}: configuração inválida: {exc}") from exc
    if type(regras.get("versao")) is not int or regras["versao"] != 1 or not isinstance(regras.get("fonte"), str) or not regras["fonte"].strip():
        raise ErroEntrada(f"{caminho}: versão ou fonte da configuração ausente/inválida")
    entrada = regras.get("entrada", {})
    if not isinstance(entrada, dict) or not isinstance(entrada.get("aba_taxas"), str) or not entrada["aba_taxas"].strip():
        raise ErroEntrada(f"{caminho}: entrada.aba_taxas é obrigatória")
    abas = entrada.get("abas_identidade", [])
    if not isinstance(abas, list) or any(not isinstance(a, str) or not a.strip() for a in abas):
        raise ErroEntrada(f"{caminho}: entrada.abas_identidade deve ser lista de nomes")
    if entrada["aba_taxas"] in abas:
        raise ErroEntrada(f"{caminho}: separar aba contratual de abas apenas de identidade")
    modalidades = regras.get("modalidades", {})
    permitidas = {"DEBITO": "debito", "CREDITO A VISTA": "credito_vista", "PIX": "pix",
                  "CREDITO PARCELADO": "parcelado"}
    if not isinstance(modalidades, dict) or not modalidades or any(permitidas.get(k) != v for k, v in modalidades.items()):
        raise ErroEntrada(f"{caminho}: modalidade fora do escopo das vendas de checkout")
    ids = set()
    for tabela, campos in (("vinculos", ("ec", "cnpj")), ("isencoes", ("cnpj",)),
                           ("contratos_bloqueados", ("cnpj", "motivo")),
                           ("observacoes_esclarecidas", ("cnpj", "texto"))):
        linhas = regras.get(tabela, [])
        if not isinstance(linhas, list):
            raise ErroEntrada(f"{caminho}: {tabela} deve ser lista de tabelas")
        for linha in linhas:
            obrigatorios = ("id", "fonte", "aprovacao", *campos)
            if not isinstance(linha, dict) or any(
                not isinstance(linha.get(k), str) or not linha[k].strip() for k in obrigatorios
            ):
                raise ErroEntrada(f"{caminho}: {tabela} exige identificação, fonte e registro de aprovação")
            if linha["id"] in ids or not re.fullmatch(r"[0-9]{14}", linha["cnpj"]):
                raise ErroEntrada(f"{caminho}: regra duplicada ou CNPJ inválido em {tabela}")
            ids.add(linha["id"])
            if tabela == "vinculos" and not re.fullmatch(r"[0-9]+", linha["ec"]):
                raise ErroEntrada(f"{caminho}: EC inválido no vínculo {linha['id']}")
            if tabela == "isencoes":
                if any(type(linha.get(k)) is not date for k in ("inicio", "fim")) or linha["inicio"] > linha["fim"]:
                    raise ErroEntrada(f"{caminho}: isenção exige datas TOML início/fim válidas e ordenadas")
    decisoes = regras.get("decisoes_pendentes", [])
    if not isinstance(decisoes, list) or any(
        not isinstance(d, dict) or not all(isinstance(d.get(k), str) and d[k].strip()
                                          for k in ("id", "descricao"))
        or not isinstance(d.get("tratamento_atual", d.get("tratamento_entrega_1")), str)
        for d in decisoes
    ):
        raise ErroEntrada(f"{caminho}: registro de decisões pendentes inválido")
    return regras
