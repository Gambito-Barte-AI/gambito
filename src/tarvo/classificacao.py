"""Classificação determinística por critérios configurados, sem I/O ou provisões."""

from datetime import datetime
import re

from .leitores.taxas import normalizar
from .modelos import ErroEntrada, ResultadoParte


def parametros(config, banco="AURORA"):
    tabela = "classificacao_" + banco.lower()
    linhas = config.get(tabela, [])
    if not isinstance(linhas, list) or not linhas:
        raise ErroEntrada(f"{tabela}: regras documentadas ausentes")
    ids = set()
    for r in linhas:
        campos = ("id", "padrao", "sinal", "conta_codigo", "fonte", "aprovacao", "aprovador", "aprovado_em", "natureza")
        if not isinstance(r, dict) or any(not isinstance(r.get(k), str) or not r[k].strip() for k in campos):
            raise ErroEntrada(f"{tabela}: critérios, conta e aprovação obrigatórios (RN-61)")
        if (r["id"] in ids or r["sinal"] not in {"CREDITO", "DEBITO"}
                or r["natureza"] not in {"FINANCEIRA", "DECISAO_TIME", "INTERPRETACAO_TECNICA"}
                or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", r["conta_codigo"])):
            raise ErroEntrada(f"{tabela}: ID, sinal, conta ou natureza inválidos")
        ids.add(r["id"])
        try:
            re.compile(r["padrao"])
            if r["aprovado_em"] != "NAO_INFORMADO":
                datetime.fromisoformat(r["aprovado_em"])
        except (ValueError, re.error) as exc:
            raise ErroEntrada(f"{r['id']}: padrão/data inválidos") from exc
        extras = [k for k in ("pendencia_tipo", "motivo", "proximo_passo", "quem_decide") if k in r]
        if extras and (len(extras) != 4 or any(not isinstance(r[k], str) or not r[k].strip() for k in extras)):
            raise ErroEntrada(f"{r['id']}: pendência incompleta (RN-58)")
    return linhas


def calcular(movimentos, contas, regras, banco="AURORA"):
    parte = ResultadoParte(fontes=(banco.lower(), "plano_contas", "regras"), implementado=True,
        relatorios=("lancamentos_classificados.csv", "pendencias.csv"), situacao="COMPLETO",
        linhas={"lancamentos_classificados.csv": [], "pendencias.csv": []})
    calculadas = pendentes = 0
    for m in sorted(movimentos, key=lambda m: (m.origem.arquivo, m.origem.linha)):
        regra, conta = None, None
        motivo, categoria, tipo = m.erro, "DADOS", "MOVIMENTO_BANCARIO_INVALIDO"
        if not motivo:
            candidatas = [r for r in regras if re.search(r["padrao"], normalizar(m.descricao))
                and ((m.valor > 0 and r["sinal"] == "CREDITO") or (m.valor < 0 and r["sinal"] == "DEBITO"))]
            if len(candidatas) != 1:
                categoria, tipo = "NEGOCIO", "CLASSIFICACAO_NAO_RESOLVIDA"
                motivo = "Histórico/sinal sem regra" if not candidatas else "Histórico corresponde a várias regras; não escolher por ordem"
            else:
                regra = candidatas[0]
                conta = contas.get(regra["conta_codigo"])
                if conta is None or conta.tipo != "ANALITICA" or not conta.aceita_lancamento:
                    motivo, tipo = "Conta da regra ausente, sintética ou sem permissão de lançamento (RN-51)", "CONTA_NAO_PERMITIDA"
        origem = dict(arquivo_origem=m.origem.arquivo, ref_origem=m.origem.ref,
                      linha_origem=m.origem.linha)
        valor = format(m.valor, ".2f") if m.valor is not None else ""
        if motivo:
            pendentes += 1
            pendencia = dict(tipo=tipo, motivo=motivo, quem_decide="Financeiro",
                proximo_passo="Revisar histórico, sinal e conta na fonte; aprovar uma regra documentada sem alterar o extrato original.")
            if categoria == "DADOS":
                parte.situacao = "PROVISORIO"
        else:
            calculadas += 1
            identificador = f"{banco}:{m.origem.arquivo}:{m.origem.ref}"
            parte.linhas["lancamentos_classificados.csv"].append(dict(id_saida=identificador, banco=banco,
                ref_origem=m.origem.ref, data=m.data.isoformat(), descricao=m.descricao, valor=valor,
                conta_codigo=conta.codigo, metodo="REGRA", confianca="1"))
            parte.rastro.append(dict(id_saida=identificador, **origem, valor=valor,
                regra=regra["id"], contrato_origem=conta.origem.arquivo, ref_contrato=conta.origem.ref,
                natureza_valor="MOVIMENTO_BANCARIO"))
            if "pendencia_tipo" not in regra:
                continue
            categoria = "NEGOCIO"
            pendencia = {k: regra[k] for k in ("motivo", "quem_decide", "proximo_passo")}
            pendencia["tipo"] = regra["pendencia_tipo"]
        identificador = f"PENDENCIA_{banco}:{m.origem.arquivo}:{m.origem.ref}" + (f":L{m.origem.linha}" if banco == "MERIDIANO" else "")
        parte.linhas["pendencias.csv"].append(dict(id_saida=identificador, **origem, **pendencia,
            valor_brl=valor, categoria=categoria,
            natureza_valor="MOVIMENTO_BANCARIO" if valor else "NAO_INFORMADO"))
        if valor:
            parte.rastro.append(dict(id_saida=identificador, **origem, valor=valor,
                natureza_valor="MOVIMENTO_BANCARIO", regra=regra["id"] if regra else "NAO_RESOLVIDA"))
    parte.cobertura = dict(linhas_lidas=len(movimentos), calculadas=calculadas, pendentes=pendentes, bloqueadas=0)
    if parte.situacao == "PROVISORIO":
        parte.motivos = ["Há movimentos inválidos ou conta indisponível; valores desconhecidos não foram estimados"]
    return parte


def validar(parte, contexto):
    if contexto is None:
        raise ErroEntrada("Extrato sem contexto normalizado para conferir contas e origens")
    esperado = calcular(**contexto)
    if parte.linhas != esperado.linhas or parte.rastro != esperado.rastro or parte.cobertura != esperado.cobertura:
        raise ErroEntrada("Classificação/pendências bancárias divergem dos movimentos, contas ou regras")
