"""Auditoria E3 pelas fontes CSV/XLSX/TOML, sem importar o motor."""

from collections import defaultdict
import csv
from datetime import datetime
from decimal import Decimal
from io import StringIO
import re

from auditoria_a3 import planilhas, normalizar
from validar_saida import exigir, dinheiro


def verificar(m, arquivos, config, pasta):
    parte = m["partes"]["ALERTAS_ANTECIPACAO"]
    ps = [p for p in arquivos["pendencias.csv"] if p["id_saida"].startswith("ALERTA_ANTECIPACAO:")]
    rs = [r for r in arquivos["rastro.csv"] if r["id_saida"].startswith("ALERTA_ANTECIPACAO:")]
    if m["escopo_comando"] != "alvo" or not parte["rastro_validado"]:
        exigir(not ps and not rs, "Alerta publicado fora do escopo ou sem validação")
        return
    criterio = config["extras"]["alertas"]
    exigir(m.get("criterio_alertas") == criterio and criterio["metodo"] == "SALDO_FIM_DIA"
           and criterio["sem_valor_minimo"] is True and criterio["elegibilidade"] == "CONTRATOS_BLOQUEADOS",
           "Critério de alerta omitido/alterado")
    cnpjs, por_ec = set(), defaultdict(set)
    f = m["fontes"]["taxas"]["arquivo"]
    abas = [config["entrada"]["aba_taxas"], *config["entrada"].get("abas_identidade", [])]
    for aba, linhas in planilhas((pasta/f).read_bytes()):
        if aba not in abas:
            continue
        colunas = None
        for _, linha in linhas:
            normalizadas = {normalizar(v): k for k,v in linha.items()}
            if "cnpj" in normalizadas and "lojista" in normalizadas:
                colunas = normalizadas; continue
            if not colunas:
                continue
            cnpj = re.sub(r"\D", "", linha.get(colunas["cnpj"], ""))
            if not cnpj:
                continue
            cnpj = cnpj.zfill(14); cnpjs.add(cnpj)
            ec = re.sub(r"\D", "", linha.get(colunas.get("ec orbe", ""), ""))
            if ec and aba == config["entrada"]["aba_taxas"]:
                por_ec[ec].add(cnpj)
    for v in config.get("vinculos", []):
        if v["cnpj"] in cnpjs:
            por_ec[v["ec"]].add(v["cnpj"])
    bloqueados = {b["cnpj"] for b in config.get("contratos_bloqueados", [])}
    todos = defaultdict(list)
    for fonte in sorted(m["fontes"]["orbe"]["arquivos"], key=lambda f:f["arquivo"]):
        if fonte["situacao"] != "DISPONIVEL":
            continue
        raw=(pasta/fonte["arquivo"]).read_bytes()
        try: texto=raw.decode("utf-8-sig")
        except UnicodeDecodeError: texto=raw.decode("cp1252")
        leitor=csv.DictReader(StringIO(texto), delimiter=";"); anterior=1
        for linha in leitor:
            fisica=anterior+1;anterior=leitor.line_num
            try:
                data=datetime.strptime(linha["data_movimento"],"%d/%m/%Y").date()
                if data.strftime("%Y-%m")!=m["competencia"]:continue
                linha=dict(linha, arquivo=fonte["arquivo"], linha=fisica, dia=data)
                todos[linha["id_transacao"]].append(linha)
            except (ValueError,KeyError):continue
    unicos={}
    for ref, repetidos in todos.items():
        assinaturas={tuple(sorted((k,v) for k,v in e.items() if k not in {"arquivo","linha","dia"})) for e in repetidos}
        if len(assinaturas)==1:unicos[ref]=repetidos[0]
    grupos=defaultdict(list)
    for e in unicos.values():
        ids=por_ec[e["cod_estabelecimento"]]
        if len(ids)==1 and next(iter(ids)) in bloqueados and e["tipo_lancamento"] in {"ANTECIPACAO","REVERSAO ANTECIPACAO"}:
            grupos[next(iter(ids))].append(e)
    esperados={};traces={}
    for cnpj,itens in grupos.items():
        antecs=[e for e in itens if e["tipo_lancamento"]=="ANTECIPACAO"]
        if not antecs:continue
        dias=defaultdict(list);reversoes=[]
        for e in itens:
            v=Decimal(e["valor_bruto"].replace(".","").replace(",","."))
            abatida=e["tipo_lancamento"]=="ANTECIPACAO" or e["id_referencia"] in unicos
            if abatida:dias[e["dia"]].append((e,v))
            if e["tipo_lancamento"]=="REVERSAO ANTECIPACAO":reversoes.append((e,v,abatida))
        saldo=Decimal(0);pico=None
        for dia in sorted(dias):
            saldo+=sum((v for _,v in dias[dia]),Decimal(0))
            if pico is None or saldo>pico:pico=saldo;data_pico=dia
        ident=f"ALERTA_ANTECIPACAO:{m['competencia']}:{cnpj}"
        esperados[ident]=(pico,data_pico,sum((Decimal(e['valor_bruto'].replace('.','').replace(',','.')) for e in antecs),Decimal(0)),reversoes)
        traces[ident]={(e["arquivo"],e["id_transacao"]):v for dia,vs in dias.items() if dia<=data_pico for e,v in vs}
    exigir({p['id_saida'] for p in ps}==set(esperados),"Cobertura dos alertas de lojistas divergente")
    for p in ps:
        pico,dia,total,reversoes=esperados[p['id_saida']]
        exigir(dinheiro(p['valor_brl'])==pico and p['tipo']=='ALERTA_ANTECIPACAO'
               and p['quem_decide']=='Financeiro e Comercial' and p['proximo_passo'],"Pico/tipo/responsável de alerta incorreto")
        exigir(dia.isoformat() in p['motivo'] and format(total,'.2f') in p['motivo']
               and 'anterior ao período desconhecida' in p['motivo'],"Motivo de alerta omite data, total ou limitação")
        for e,v,abatida in reversoes:
            exigir(all(s in p['motivo'] for s in (e['id_transacao'],e['id_referencia'],e['dia'].isoformat(),format(v,'.2f'))),"Reversão omitida do alerta")
            if not abatida:exigir('não abatida' in p['motivo'],"Reversão fora do período não identificada")
        reais={(r['arquivo_origem'],r['ref_origem']):dinheiro(r['valor']) for r in rs if r['id_saida']==p['id_saida']}
        exigir(reais==traces[p['id_saida']],"Rastro do pico não corresponde aos movimentos até o fim do dia")
