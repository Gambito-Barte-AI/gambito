"""Auditoria independente de notas e saldos sem nota; não importa o motor."""

from collections import Counter, defaultdict
from decimal import Decimal
import re

from validar_saida import exigir, dinheiro


def assinatura(r):
    return tuple((k, r[k]) for k in sorted(r) if k not in {"id_saida", "natureza_valor"})


def verificar(m, arquivos, config):
    notas = arquivos["notas_a_emitir.csv"]
    sem_nota = [p for p in arquivos["pendencias.csv"] if p["id_saida"].startswith("SEM_NOTA:")]
    rastros = [r for r in arquivos["rastro.csv"] if r["id_saida"].startswith(("NOTA:", "SEM_NOTA:"))]
    if m["escopo_comando"] == "checkout":
        exigir(not notas and not sem_nota and not rastros, "Notas publicadas fora do escopo escolhido")
        return
    destinos = notas + sem_nota
    exigir(len({d["id_saida"] for d in destinos}) == len(destinos), "ID de nota/pendência repetido")
    por_id = {d["id_saida"]: d for d in destinos}
    detalhes = defaultdict(list)
    for r in rastros:
        exigir(r["id_saida"] in por_id, "Rastro de notas sem destino")
        dinheiro(r["valor"])
        detalhes[r["id_saida"]].append(r)
    esperados = set()
    for negocio, nome, origem, tabela in (
        ("CHECKOUT", "NOTAS_CHECKOUT", "CHECKOUT", "notas_checkout"),
        ("REMESSA", "NOTAS_REMESSA", "REMESSAS", "notas_remessa")):
        disponivel = m["partes"][nome]["rastro_validado"]
        if not disponivel:
            exigir(not any(d["id_saida"].startswith((f"NOTA:{negocio}:", f"SEM_NOTA:{negocio}:")) for d in destinos),
                   "Notas bloqueadas publicaram valores")
            continue
        exigir(m["partes"][origem]["rastro_validado"], "Nota sem comissão validada")
        p = config.get(tabela, {})
        exigir(p and m.get("fontes", {}).get("regras", {}).get("parametros_notas", {}).get(nome) == p,
               "Regra de notas omitida/alterada no manifesto")
        if negocio == "REMESSA":
            exigir(re.fullmatch(r"[0-9]{14}", p.get("tomador_cnpj", "")), "Tomador remessa inválido")
        grupos = defaultdict(list)
        comissoes = [c for c in arquivos["comissoes_por_lojista.csv"] if c["linha_negocio"] == negocio]
        for c in comissoes:
            chave = re.fullmatch(rf"{negocio}:([0-9]{{4}}-(?:0[1-9]|1[0-2])):([0-9]{{14}})", c["id_saida"])
            exigir(chave and chave[2] == c["cnpj"], "Comissão de nota sem competência/identidade coerente")
            tomador = c["cnpj"] if negocio == "CHECKOUT" else p["tomador_cnpj"]
            grupos[chave[1], tomador].append(c)
        calculadas = pendentes = 0
        for (mes, cnpj), grupo in grupos.items():
            saldo = sum((dinheiro(c["comissao_brl"]) for c in grupo), Decimal(0))
            identificador = f"{'NOTA' if saldo > 0 else 'SEM_NOTA'}:{negocio}:{mes}:{cnpj}"
            esperados.add(identificador)
            exigir(identificador in por_id, "Saldo de comissão sem nota ou pendência correspondente")
            d = por_id[identificador]
            exigir(dinheiro(d["valor_brl"]) == saldo, "Nota/pendência difere do saldo validado, sem transporte entre meses")
            ids_origem = {c["id_saida"] for c in grupo}
            origens = [r for r in arquivos["rastro.csv"] if r["id_saida"] in ids_origem]
            obtidos = detalhes[identificador]
            exigir(origens and Counter(map(assinatura, origens)) == Counter(map(assinatura, obtidos)),
                   "Nota/pendência perdeu sinais, valores ou metadados das origens da comissão")
            exigir(sum((dinheiro(r["valor"]) for r in obtidos), Decimal(0)) == saldo, "Rastro não reconcilia com nota/pendência")
            if saldo > 0:
                calculadas += len(grupo)
                exigir(d in notas and d["linha_negocio"] == negocio and d["tomador_cnpj"] == cnpj,
                       "Nota com linha de negócio/tomador incorretos")
                exigir(d["tomador"] == (grupo[0]["lojista"] if negocio == "CHECKOUT" else p["tomador"]),
                       "Nome do tomador divergente da comissão/configuração")
                exigir(p["servico"] in d["discriminacao"] and mes in d["discriminacao"], "Discriminação sem serviço/competência")
                if any(r.get("regra") == "D-10_AJUSTE_PONTE" for r in origens):
                    exigir("D-10" in d["discriminacao"], "Nota com ajuste omitiu D-10")
                exigir(all(r["natureza_valor"] == "PROPOSTA_NOTA_COMISSAO" for r in obtidos), "Natureza do rastro da nota incorreta")
            else:
                pendentes += len(grupo)
                exigir(d in sem_nota and d["tipo"] == "SALDO_COMISSAO_NAO_POSITIVO" and d["cnpj"] == cnpj
                       and d["quem_decide"] == "Financeiro" and d["motivo"] and d["proximo_passo"],
                       "Saldo não positivo sem pendência financeira")
                exigir(d["ref_origem"] == origens[0]["ref_origem"] and d["arquivo_origem"] == origens[0]["arquivo_origem"],
                       "Pendência sem origem representativa do saldo")
                exigir(d["natureza_valor"] == "SALDO_COMISSAO_SEM_NOTA"
                       and all(r["natureza_valor"] == "SALDO_COMISSAO_SEM_NOTA" for r in obtidos), "Natureza de saldo sem nota incorreta")
        exigir(m["partes"][nome]["cobertura"] == dict(linhas_lidas=len(comissoes), calculadas=calculadas,
                                                     pendentes=pendentes, bloqueadas=0), "Cobertura de notas incorreta")
    exigir(esperados == set(por_id), "Nota extra, negativa/zero, complementar ou pendência de saldo indevida")
