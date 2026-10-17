"""Configuração explícita de vínculos e condições, com origem documentada."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
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
                           ("devolucoes_checkout", ("cnpj", "isencao", "politica_estornos")),
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
            if not all(isinstance(linha.get(k), str) and linha[k].strip()
                       for k in ("aprovador", "aprovado_em", "natureza")):
                raise ErroEntrada(f"{caminho}: {linha['id']} exige aprovador, aprovado_em e natureza (RN-61)")
            if linha["natureza"] not in {"FINANCEIRA", "DECISAO_TIME", "INTERPRETACAO_TECNICA"}:
                raise ErroEntrada(f"{caminho}: natureza inválida em {linha['id']}")
            if linha["aprovado_em"] != "NAO_INFORMADO":
                try:
                    datetime.fromisoformat(linha["aprovado_em"])
                except ValueError as exc:
                    raise ErroEntrada(f"{caminho}: data de aprovação inválida em {linha['id']}") from exc
            if tabela == "vinculos" and not re.fullmatch(r"[0-9]+", linha["ec"]):
                raise ErroEntrada(f"{caminho}: EC inválido no vínculo {linha['id']}")
            if tabela == "isencoes":
                if any(type(linha.get(k)) is not date for k in ("inicio", "fim")) or linha["inicio"] > linha["fim"]:
                    raise ErroEntrada(f"{caminho}: isenção exige datas TOML início/fim válidas e ordenadas")
            if tabela == "devolucoes_checkout":
                if linha["politica_estornos"] != "VENDA_ORIGINAL_ISENTA":
                    raise ErroEntrada(f"{caminho}: estornos da devolução exigem venda original elegível à isenção (RN-64)")
                if not any(i["id"] == linha["isencao"] and i["cnpj"] == linha["cnpj"] for i in regras.get("isencoes", [])):
                    raise ErroEntrada(f"{caminho}: devolução sem isenção correspondente")
    decisoes = regras.get("decisoes_pendentes", [])
    if not isinstance(decisoes, list) or any(
        not isinstance(d, dict) or not all(isinstance(d.get(k), str) and d[k].strip()
                                          for k in ("id", "descricao"))
        or not isinstance(d.get("tratamento_atual", d.get("tratamento_entrega_1")), str)
        for d in decisoes
    ):
        raise ErroEntrada(f"{caminho}: registro de decisões pendentes inválido")
    return regras


def parametros_remessa(regras):
    parametros = regras.get("remessas", {})
    if not all(isinstance(parametros.get(k), str) and parametros[k].strip() for k in
               ("id", "fonte", "aprovacao", "aprovador", "aprovado_em", "natureza")):
        raise ErroEntrada("A3: parâmetros de remessa exigem fonte e aprovação (RN-61)")
    if parametros["natureza"] not in {"FINANCEIRA", "DECISAO_TIME", "INTERPRETACAO_TECNICA"}:
        raise ErroEntrada("A3: natureza dos parâmetros de remessa inválida")
    if parametros["aprovado_em"] != "NAO_INFORMADO":
        try:
            datetime.fromisoformat(parametros["aprovado_em"])
        except ValueError as exc:
            raise ErroEntrada("A3: data de aprovação inválida") from exc
    try:
        if not all(isinstance(parametros.get(k), str) for k in
                   ("participacao_fracao", "spread_padrao_fracao", "tolerancia_pp")):
            raise ValueError("parâmetros decimais devem ser strings TOML")
        participacao = Decimal(parametros["participacao_fracao"])
        padrao = Decimal(parametros["spread_padrao_fracao"])
        tolerancia = Decimal(parametros["tolerancia_pp"])
        if (not all(v.is_finite() for v in (participacao, padrao, tolerancia))
                or not 0 < participacao <= 1 or not 0 <= padrao <= 1 or tolerancia < 0):
            raise ValueError("frações/tolerância inválidas")
    except (KeyError, InvalidOperation, ValueError, TypeError) as exc:
        raise ErroEntrada("A3: participação, spread padrão ou tolerância inválidos") from exc
    vigencias = regras.get("vigencias_spread", [])
    if not isinstance(vigencias, list):
        raise ErroEntrada("A3: vigências de spread devem ser lista")
    for regra in vigencias:
        if (not isinstance(regra, dict) or type(regra.get("inicio")) is not date
                or not re.fullmatch(r"[0-9]{14}", str(regra.get("cnpj", "")))
                or not all(isinstance(regra.get(k), str) and regra[k].strip() for k in
                           ("id", "fonte", "aprovacao", "aprovador", "aprovado_em", "natureza"))):
            raise ErroEntrada("A3: vigência de spread exige CNPJ, data e fonte/aprovação")
        if regra["aprovado_em"] != "NAO_INFORMADO":
            try:
                datetime.fromisoformat(regra["aprovado_em"])
            except ValueError as exc:
                raise ErroEntrada("A3: data de aprovação de spread inválida") from exc
    return parametros
