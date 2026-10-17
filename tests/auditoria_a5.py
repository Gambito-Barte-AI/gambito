"""Auditoria Aurora independente: relê fontes, regras e origens sem importar tarvo."""

import csv
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from io import StringIO
from pathlib import Path
import re
import unicodedata

from validar_saida import exigir, dinheiro


def norm(s):
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower().split())


def texto(p):
    raw = p.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def fonte(m, dados, nome):
    f = m["fontes"][nome]
    arquivo = f.get("arquivo", "")
    exigir(arquivo and Path(arquivo).name == arquivo, f"{nome}: caminho inválido")
    p = dados / arquivo
    exigir(sha256(p.read_bytes()).hexdigest() == f.get("sha256"), f"{nome}: hash da fonte difere")
    return p


def verificar(m, arquivos, config, dados, caminho_regras):
    classificados = [c for c in arquivos["lancamentos_classificados.csv"] if c["banco"] == "AURORA"]
    ps = [p for p in arquivos["pendencias.csv"] if p["id_saida"].startswith("PENDENCIA_AURORA:")]
    rs = [r for r in arquivos["rastro.csv"] if r["id_saida"].startswith(("AURORA:", "PENDENCIA_AURORA:"))]
    if m["escopo_comando"] == "checkout":
        exigir(not classificados and not ps and not rs, "Aurora fora do escopo escolhido")
        return
    parte = m["partes"]["EXTRATO_AURORA"]
    if not parte["rastro_validado"]:
        exigir(not classificados and not ps and not rs, "Aurora bloqueado publicou valores")
        return
    exigir(all(c["banco"] in ({"AURORA", "MERIDIANO"} if m["versao"] >= 8 else {"AURORA"}) for c in arquivos["lancamentos_classificados.csv"]), "Banco desconhecido na saída")
    exigir(sha256(caminho_regras.read_bytes()).hexdigest() == m["fontes"]["regras"]["sha256"], "Regras de classificação alteradas")
    regras = config.get("classificacao_aurora", [])
    exigir(regras and m["fontes"]["regras"].get("parametros_classificacao_aurora") == regras, "Regras Aurora sem proveniência")
    contas, plano = ler_plano(m, dados)
    extrato = fonte(m, dados, "aurora")
    leitor = csv.reader(StringIO(texto(extrato), newline=""), delimiter=";", strict=True)
    cabecalho, movimentos, ignoradas = None, [], []
    while True:
        n = leitor.line_num + 1
        try:
            l = next(leitor)
        except StopIteration:
            break
        if cabecalho is None:
            if {"data", "lancamento", "documento", "valor (r$)", "saldo (r$)"} <= set(map(norm, l)):
                cabecalho = list(map(norm, l))
            continue
        if not any(c.strip() for c in l):
            ignoradas.append(dict(ref=f"L{n}", motivo="LINHA_VAZIA")); continue
        c = dict(zip(cabecalho, l))
        descricao = c.get("lancamento", "").strip()
        if (len(l) == len(cabecalho) and not c.get("valor (r$)", "").strip()
                and norm(descricao) in {"saldo anterior", "saldo final", "os lancamentos estao sujeitos a confirmacao."}):
            ignoradas.append(dict(ref=f"L{n}", motivo="SALDO_OU_RODAPE")); continue
        data, valor = None, None
        try:
            data = datetime.strptime(c.get("data", "").strip(), "%d/%m/%Y").date()
        except ValueError:
            pass
        v = c.get("valor (r$)", "").strip()
        if re.fullmatch(r"-?(?:\d+|\d{1,3}(?:\.\d{3})+),\d{2}", v):
            valor = Decimal(v.replace(".", "").replace(",", "."))
        movimentos.append((f"L{n}", data, descricao, valor, len(l) == len(cabecalho) and data is not None and bool(descricao) and valor is not None, n))
    exigir(cabecalho is not None, "Cabeçalho Aurora ausente")
    f = m["fontes"]["aurora"]
    exigir(f["ingestao"] == dict(linhas_fisicas=leitor.line_num, movimentos_lidos=len(movimentos), ignoradas=ignoradas), "Inventário físico Aurora incorreto")
    todos = movimentos
    movimentos = [v for v in todos if v[1] is None or v[1].strftime("%Y-%m") == f["competencia"]]
    exigir(f["fora_competencia"] == len(todos)-len(movimentos), "Recorte Aurora incorreto")
    auditar_movimentos(parte, classificados, ps, rs, regras, contas, plano, extrato, movimentos)


def ler_plano(m, dados):
    plano = fonte(m, dados, "plano_contas")
    leitor = csv.DictReader(StringIO(texto(plano)), delimiter=";")
    contas = {}
    for l in leitor:
        codigo = l["COD_CONTA"].strip()
        exigir(codigo not in contas, "Conta duplicada no plano")
        contas[codigo] = (l["TIPO"].strip() == "ANALITICA" and l["ACEITA_LANCTO"].strip() == "S", f"L{leitor.line_num}")
    exigir(m["fontes"]["plano_contas"]["contas_lidas"] == len(contas), "Contagem de contas difere")
    return contas, plano


def auditar_movimentos(parte, classificados, ps, rs, regras, contas, plano, extrato, movimentos, banco="AURORA"):
    por_id = {l["id_saida"]: l for l in classificados + ps}
    exigir(len(por_id) == len(classificados)+len(ps), "ID Aurora repetido")
    rastros = {}
    for r in rs:
        exigir(r["id_saida"] not in rastros, "Rastro Aurora duplicado")
        rastros[r["id_saida"]] = r
    esperados, monetarios, calculadas, pendentes = set(), set(), 0, 0
    for ref, data, descricao, valor, valido, numero in movimentos:
        candidatas = [r for r in regras if valido and re.search(r["padrao"], norm(descricao))
            and ((valor > 0 and r["sinal"] == "CREDITO") or (valor < 0 and r["sinal"] == "DEBITO"))]
        regra = candidatas[0] if len(candidatas) == 1 else None
        conta = contas.get(regra["conta_codigo"]) if regra else None
        classificar = bool(valido and regra and conta and conta[0])
        if classificar:
            calculadas += 1
            ident = f"{banco}:{extrato.name}:{ref}"
            esperados.add(ident); monetarios.add(ident)
            exigir(ident in por_id, "Movimento elegível sem classificação")
            saida = por_id[ident]
            exigir(saida == dict(id_saida=ident, banco=banco, ref_origem=ref, data=data.isoformat(), descricao=descricao,
                valor=format(valor, ".2f"), conta_codigo=regra["conta_codigo"], metodo="REGRA", confianca="1"), "Classificação não corresponde à origem/regra/conta permitida")
            exigir(ident in rastros and rastros[ident]["regra"] == regra["id"]
                and rastros[ident]["contrato_origem"] == plano.name and rastros[ident]["ref_contrato"] == conta[1], "Conta/regra sem rastro")
        else:
            pendentes += 1
        if not classificar or "pendencia_tipo" in regra:
            ident = f"PENDENCIA_{banco}:{extrato.name}:{ref}" + (f":L{numero}" if banco == "MERIDIANO" else "")
            esperados.add(ident)
            exigir(ident in por_id and por_id[ident] in ps, "Movimento sem pendência obrigatória")
            p = por_id[ident]
            exigir(p["ref_origem"] == ref and p["arquivo_origem"] == extrato.name and p["linha_origem"] == str(numero)
                and p["valor_brl"] == (format(valor, ".2f") if valor is not None else "")
                and p["motivo"] and p["quem_decide"] and p["proximo_passo"], "Pendência Aurora incompleta/incorreta")
            exigir(p["natureza_valor"] == ("MOVIMENTO_BANCARIO" if valor is not None else "NAO_INFORMADO"), "Natureza da pendência Aurora inválida")
            tipo = (regra["pendencia_tipo"] if classificar else "MOVIMENTO_BANCARIO_INVALIDO" if not valido else
                    "CONTA_NAO_PERMITIDA" if regra else "CLASSIFICACAO_NAO_RESOLVIDA")
            exigir(p["tipo"] == tipo, "Tipo da pendência Aurora difere da causa")
            if classificar:
                exigir(all(p[k] == regra[k] for k in ("motivo", "quem_decide", "proximo_passo")), "Pendência da regra omitida/alterada")
            if valor is not None:
                monetarios.add(ident)
        for ident in (f"{banco}:{extrato.name}:{ref}", f"PENDENCIA_{banco}:{extrato.name}:{ref}" + (f":L{numero}" if banco == "MERIDIANO" else "")):
            if ident in monetarios:
                exigir(ident in rastros, "Valor Aurora sem rastro")
                r = rastros[ident]
                exigir(r["arquivo_origem"] == extrato.name and r["ref_origem"] == ref and r["linha_origem"] == str(numero)
                    and dinheiro(r["valor"]) == valor and r["natureza_valor"] == "MOVIMENTO_BANCARIO", "Rastro Aurora diverge do movimento")
    exigir(set(por_id) == esperados and set(rastros) == monetarios, "Aurora com destino extra, ausente ou valor desconhecido inventado")
    exigir(parte["cobertura"] == dict(linhas_lidas=len(movimentos), calculadas=calculadas, pendentes=pendentes, bloqueadas=0), "Cobertura Aurora incorreta")
