"""Coordena somente checkout; fontes futuras não são dependências desta entrega."""

from hashlib import sha256
from decimal import Decimal, DecimalException
from pathlib import Path
import re
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError

from . import checkout, divergencias, remessas, regras, validacao
from .leitores import orbe, ponte, taxas
from .modelos import Cadastro, ErroEntrada, Resultado, ResultadoParte
from .partes import preparar_partes


def executar(pasta: Path, configuracao: Path, competencia: str | None = None) -> Resultado:
    resultado = _executar_checkout(pasta, configuracao, competencia)
    _executar_remessas(resultado, pasta, configuracao, competencia)
    preparar_partes(resultado)
    return resultado


def _executar_checkout(pasta: Path, configuracao: Path, competencia: str | None = None) -> Resultado:
    resultado = Resultado()
    bloqueios = []
    config = None
    try:
        config = regras.carregar(configuracao)
        resultado.decisoes_pendentes = config.get("decisoes_pendentes", [])
        resultado.decisoes_documentadas = config.get("decisoes_documentadas", [])
        resultado.fontes["regras"] = {
            "arquivo": configuracao.name, "situacao": "DISPONIVEL",
            "sha256": sha256(configuracao.read_bytes()).hexdigest(),
            "metadados_incompletos": [
                {"id": r["id"], "campo": "aprovado_em", "valor": "NAO_INFORMADO"}
                for tabela in ("vinculos", "isencoes", "contratos_bloqueados", "observacoes_esclarecidas", "devolucoes_checkout", "decisoes_documentadas", "decisoes_pendentes")
                for r in config.get(tabela, []) if r.get("aprovado_em") == "NAO_INFORMADO"
            ],
        }
    except (ErroEntrada, OSError) as exc:
        bloqueios.append(str(exc))
        resultado.fontes["regras"] = {"situacao": "BLOQUEADO", "motivo": str(exc)}
    if competencia is not None and not re.fullmatch(r"[0-9]{4}-(?:0[1-9]|1[0-2])", competencia):
        resultado.motivos = ["Competência deve ter formato AAAA-MM com mês válido"]
        return resultado
    cadastro = Cadastro()
    for nome, descobrir, ler in (
        ("orbe", None, None),
        ("taxas", taxas.descobrir, taxas.ler),
    ):
        try:
            if not pasta.is_dir():
                raise ErroEntrada(f"Pasta de dados inexistente ou inválida: {pasta}")
            if nome == "orbe":
                (resultado.eventos, resultado.pendencias, resultado.linhas_lidas,
                 resultado.fontes[nome], resultado.avisos, resultado.ingestao) = orbe.ler_pasta(pasta, competencia)
                if resultado.fontes[nome]["situacao"] == "BLOQUEADO":
                    bloqueios.extend(resultado.avisos)
                continue
            caminho = descobrir(pasta)
            if config is None:
                raise ErroEntrada("Taxas: leitura bloqueada por configuração inválida")
            else:
                cadastro = ler(caminho, config["entrada"]["aba_taxas"], config["entrada"].get("abas_identidade", []))
            resultado.fontes[nome] = {
                "arquivo": caminho.name, "situacao": "DISPONIVEL",
                "sha256": sha256(caminho.read_bytes()).hexdigest(),
            }
        except (ErroEntrada, OSError) as exc:
            bloqueios.append(str(exc))
            resultado.fontes[nome] = {"situacao": "BLOQUEADO", "motivo": str(exc)}
    competencias = resultado.ingestao.get("competencias", [])
    if len(competencias) == 1:
        resultado.competencia = competencias[0]
    else:
        bloqueios.append("Orbe: competência única não identificada; arquivo vazio, inválido ou com múltiplos meses")
    if bloqueios:
        resultado.motivos = bloqueios
        return resultado
    resultado.contribuicoes, pendencias = checkout.calcular(
        resultado.eventos, cadastro, config,
    )
    resultado.calculo_executado = True
    resultado.pendencias.extend(pendencias)
    resultado.pendencias.sort(key=lambda p: (p.origem.arquivo, p.origem.linha))
    (resultado.partes["DIVERGENCIAS_CHECKOUT"], resultado.partes["DEVOLUCAO_CASA"]) = divergencias.calcular(
        resultado.eventos, resultado.contribuicoes, resultado.pendencias, config,
        resultado.linhas_lidas, resultado.avisos,
    )
    validacao.consolidar(resultado)
    try:
        validacao.validar(resultado)
    except ErroEntrada as exc:
        resultado.motivos = [str(exc)]
        return resultado
    dados_pendentes = any(p.categoria == "DADOS" for p in resultado.pendencias)
    resultado.situacao = "PROVISORIO" if dados_pendentes or resultado.avisos else "COMPLETO"
    resultado.motivos.extend(resultado.avisos)
    if dados_pendentes:
        resultado.motivos.append("Há linhas não calculadas; os CSVs representam somente os eventos de checkout validados")
    return resultado


def _executar_remessas(resultado, pasta, configuracao, competencia):
    # A comissão realizada não depende de Orbe nem de contratos disponíveis.
    for nome, fontes, relatorios in (
        ("REMESSAS", ("ponte", "regras"), ("comissoes_por_lojista.csv", "pendencias.csv")),
        ("DIVERGENCIAS_REMESSA", ("ponte", "contratos_remessa", "regras"), ("divergencias_taxa.csv", "pendencias.csv"))):
        resultado.partes[nome] = ResultadoParte(fontes=fontes, relatorios=relatorios, implementado=True,
            motivos=["Análise Ponte não concluída"])
    if competencia is not None and not re.fullmatch(r"[0-9]{4}-(?:0[1-9]|1[0-2])", competencia):
        resultado.fontes["ponte"] = dict(situacao="BLOQUEADO", motivo="Competência inválida")
        return
    try:
        ops, ps, qtd, fonte = ponte.ler_pasta(pasta, competencia)
        resultado.fontes["ponte"] = fonte
        if fonte["situacao"] == "BLOQUEADO":
            raise ErroEntrada(fonte["motivo"])
        if competencia is None and resultado.competencia and fonte["competencia"] != resultado.competencia:
            raise ErroEntrada("Ponte e checkout com competências distintas; informe --competencia")
        config = regras.carregar(configuracao)
        parametros = regras.parametros_remessa(config)
        resultado.fontes["regras"]["parametros_remessa"] = parametros
        if parametros["aprovado_em"] == "NAO_INFORMADO":
            resultado.fontes["regras"]["metadados_incompletos"].append(
                dict(id=parametros["id"], campo="aprovado_em", valor="NAO_INFORMADO"))
        # Datas TOML de condições são convertidas só na serialização de metadados.
        resultado.fontes["regras"]["vigencias_spread"] = [dict(v, inicio=v["inicio"].isoformat()) for v in config.get("vigencias_spread", [])]
        contratos = None
        try:
            caminho = taxas.descobrir(pasta)
            contratos = taxas.ler_remessas(caminho, config["entrada"]["aba_taxas"],
                Decimal(parametros["spread_padrao_fracao"]), config.get("vigencias_spread", []))
            resultado.fontes["contratos_remessa"] = dict(situacao="DISPONIVEL", arquivo=caminho.name,
                sha256=sha256(caminho.read_bytes()).hexdigest())
        except (ErroEntrada, ValueError, OSError, KeyError, BadZipFile, ParseError) as exc:
            resultado.fontes["contratos_remessa"] = dict(situacao="BLOQUEADO", motivo=str(exc))
        resultado.partes["REMESSAS"], resultado.partes["DIVERGENCIAS_REMESSA"] = remessas.calcular(ops, ps, qtd, contratos, config)
    except (ErroEntrada, ValueError, OSError, KeyError, TypeError, DecimalException) as exc:
        resultado.fontes.setdefault("ponte", dict(situacao="BLOQUEADO", motivo=str(exc)))
        for nome in ("REMESSAS", "DIVERGENCIAS_REMESSA"):
            resultado.partes[nome].motivos = [f"Ponte: {exc}"]
