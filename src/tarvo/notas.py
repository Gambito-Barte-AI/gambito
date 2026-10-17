"""A4: propostas de notas derivadas de comissões validadas, sem emissão fiscal."""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, DecimalException
import re

from . import regras
from .modelos import ErroEntrada, ResultadoParte

DEPENDENCIAS = {"NOTAS_CHECKOUT": "CHECKOUT", "NOTAS_REMESSA": "REMESSAS"}


def parametros(config, nome):
    tabela = "notas_checkout" if nome == "NOTAS_CHECKOUT" else "notas_remessa"
    p = config.get(tabela, {})
    exigidos = ["id", "servico", "fonte", "aprovacao", "aprovador", "aprovado_em", "natureza"]
    if nome == "NOTAS_REMESSA":
        exigidos += ["tomador_cnpj", "tomador"]
    if not isinstance(p, dict) or any(not isinstance(p.get(k), str) or not p[k].strip() for k in exigidos):
        raise ErroEntrada(f"{tabela}: parâmetros e fonte/aprovação obrigatórios (RN-61)")
    if p["natureza"] not in {"FINANCEIRA", "DECISAO_TIME", "INTERPRETACAO_TECNICA"}:
        raise ErroEntrada(f"{tabela}: natureza de aprovação inválida")
    if p["aprovado_em"] != "NAO_INFORMADO":
        try:
            datetime.fromisoformat(p["aprovado_em"])
        except ValueError as exc:
            raise ErroEntrada(f"{tabela}: data de aprovação inválida") from exc
    if nome == "NOTAS_REMESSA" and not re.fullmatch(r"[0-9]{14}", p["tomador_cnpj"]):
        raise ErroEntrada(f"{tabela}: tomador exige CNPJ numérico com 14 dígitos")
    return p


def calcular(nome, origem, p):
    anterior = DEPENDENCIAS[nome]
    parte = ResultadoParte(fontes=("regras",), depende_de=(anterior,),
        relatorios=("notas_a_emitir.csv", "pendencias.csv"), implementado=True,
        motivos=[f"Comissões {anterior} ainda não validadas"])
    if not origem.validado or origem.situacao == "BLOQUEADO":
        return parte
    parte.situacao, parte.motivos = origem.situacao, []
    parte.linhas = {"notas_a_emitir.csv": [], "pendencias.csv": []}
    negocio = "CHECKOUT" if nome == "NOTAS_CHECKOUT" else "REMESSA"
    grupos = defaultdict(list)
    comissoes = origem.linhas.get("comissoes_por_lojista.csv", [])
    for linha in sorted(comissoes, key=lambda l: l["id_saida"]):
        chave = re.fullmatch(rf"{negocio}:([0-9]{{4}}-(?:0[1-9]|1[0-2])):([0-9]{{14}})", linha["id_saida"])
        if not chave or linha["linha_negocio"] != negocio or linha["cnpj"] != chave[2]:
            raise ErroEntrada("Comissão sem competência/identidade coerente no contrato interno")
        tomador = linha["cnpj"] if negocio == "CHECKOUT" else p["tomador_cnpj"]
        grupos[chave[1], tomador].append(linha)
    calculadas = pendentes = 0
    for (mes, cnpj), linhas in sorted(grupos.items()):
        ids = {l["id_saida"] for l in linhas}
        detalhes = [r for r in origem.rastro if r["id_saida"] in ids]
        valor = sum((Decimal(l["comissao_brl"]) for l in linhas), Decimal(0))
        tem_ajuste = any(r.get("regra") == "D-10_PENDENTE_FINANCEIRO" for r in detalhes)
        if tem_ajuste:
            parte.motivos.append("D-10: valor derivado da decisão do time; natureza do ajuste aguarda confirmação financeira antes da liberação")
        if valor > 0:
            identificador = f"NOTA:{negocio}:{mes}:{cnpj}"
            discriminacao = f"{p['servico']} - competência {mes}"
            if tem_ajuste:
                discriminacao += "; ajuste D-10 pendente de confirmação financeira"
            parte.linhas["notas_a_emitir.csv"].append(dict(id_saida=identificador,
                tomador_cnpj=cnpj, tomador=linhas[0]["lojista"] if negocio == "CHECKOUT" else p["tomador"],
                linha_negocio=negocio, valor_brl=format(valor, ".2f"), discriminacao=discriminacao))
            natureza = "PROPOSTA_NOTA_COMISSAO"
            calculadas += len(linhas)
        else:
            if not detalhes:
                raise ErroEntrada("Saldo sem origens para explicar a não emissão")
            identificador = f"SEM_NOTA:{negocio}:{mes}:{cnpj}"
            primeira = detalhes[0]
            parte.linhas["pendencias.csv"].append(dict(id_saida=identificador,
                tipo="SALDO_COMISSAO_NAO_POSITIVO", ref_origem=primeira["ref_origem"],
                valor_brl=format(valor, ".2f"), motivo=f"RN-43: saldo {negocio} de {mes} zero ou negativo; sem nota e sem transporte para o mês seguinte.",
                quem_decide="Financeiro", proximo_passo="Revisar o saldo e suas origens; não emitir nota nem transportar automaticamente para outra competência.",
                arquivo_origem=primeira["arquivo_origem"], linha_origem=primeira.get("linha_origem", ""),
                cnpj=cnpj, categoria="NEGOCIO", natureza_valor="SALDO_COMISSAO_SEM_NOTA"))
            natureza = "SALDO_COMISSAO_SEM_NOTA"
            pendentes += len(linhas)
        # Replica contribuições já arredondadas, com sinais e referências originais.
        # Não recalcula taxa, participação nem aplica novamente o percentual do ajuste.
        parte.rastro.extend(dict(r, id_saida=identificador, natureza_valor=natureza) for r in detalhes)
    parte.cobertura = dict(linhas_lidas=len(comissoes), calculadas=calculadas, pendentes=pendentes, bloqueadas=0)
    parte.motivos = list(dict.fromkeys(parte.motivos))
    return parte


def preparar(resultado, caminho):
    try:
        config = regras.carregar(caminho)
    except (ErroEntrada, OSError):
        config = {}
    for nome, anterior in DEPENDENCIAS.items():
        parte = ResultadoParte(fontes=("regras",), depende_de=(anterior,),
            relatorios=("notas_a_emitir.csv", "pendencias.csv"), implementado=True)
        try:
            p = parametros(config, nome)
            resultado.parametros_notas[nome] = p
            fonte = resultado.fontes.get("regras", {})
            fonte.setdefault("parametros_notas", {})[nome] = dict(p)
            if p["aprovado_em"] == "NAO_INFORMADO":
                fonte.setdefault("metadados_incompletos", []).append(
                    dict(id=p["id"], campo="aprovado_em", valor="NAO_INFORMADO"))
            parte = calcular(nome, resultado.partes[anterior], p)
        except (ErroEntrada, ValueError, KeyError, TypeError, DecimalException) as exc:
            parte.motivos = [f"{nome}: {exc}"]
        resultado.partes[nome] = parte


def validar(nome, parte, origem, p):
    """Reconfere a derivação na publicação, sem reparar adulterações silenciosamente."""
    if not p:
        raise ErroEntrada("Nota sem parâmetros aprovados")
    esperado = calcular(nome, origem, p)
    if (parte.linhas != esperado.linhas or parte.rastro != esperado.rastro
            or parte.cobertura != esperado.cobertura):
        raise ErroEntrada("Propostas/pendências de notas divergem das comissões e origens validadas")
