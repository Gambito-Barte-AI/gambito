"""Contrato global dos seis CSVs, independente do motor e dos exemplos."""

from collections import defaultdict
from datetime import date
from decimal import Decimal
import re

from validar_saida import exigir, dinheiro

VALORES = {"comissoes_por_lojista.csv": "comissao_brl", "divergencias_taxa.csv": "diferenca_brl",
           "notas_a_emitir.csv": "valor_brl", "lancamentos_classificados.csv": "valor", "pendencias.csv": "valor_brl"}
PRODUTORES = {
    "CHECKOUT:": "CHECKOUT", "REMESSA:": "REMESSAS", "PENDENCIA:": "PENDENCIAS_CHECKOUT",
    "DIVERGENCIA:CHECKOUT:": "DIVERGENCIAS_CHECKOUT", "CONTESTACAO_ORBE:": "DIVERGENCIAS_CHECKOUT",
    "REVISAO_DIVERGENCIA:": "DIVERGENCIAS_CHECKOUT", "DEVOLUCAO_CHECKOUT:": "DEVOLUCAO_CASA",
    "REVISAO_DEVOLUCAO:": "DEVOLUCAO_CASA", "DIVERGENCIA:REMESSA:": "DIVERGENCIAS_REMESSA",
    "CONTESTACAO_PONTE:": "DIVERGENCIAS_REMESSA", "DUPLICATA_PONTE:": "REMESSAS", "SPREAD_NEGATIVO:": "REMESSAS",
    "AJUSTE_D10:": "REMESSAS", "ACOMPANHAMENTO_PONTE:": "REMESSAS", "CADASTRO_PONTE:": "REMESSAS", "LEITURA_PONTE:": "REMESSAS",
    "NOTA:CHECKOUT:": "NOTAS_CHECKOUT", "SEM_NOTA:CHECKOUT:": "NOTAS_CHECKOUT",
    "NOTA:REMESSA:": "NOTAS_REMESSA", "SEM_NOTA:REMESSA:": "NOTAS_REMESSA",
    "AURORA:": "EXTRATO_AURORA", "PENDENCIA_AURORA:": "EXTRATO_AURORA",
    "MERIDIANO:": "EXTRATO_MERIDIANO", "PENDENCIA_MERIDIANO:": "EXTRATO_MERIDIANO",
}


def verificar(m, arquivos):
    valores, desconhecidos, destinos = {}, set(), set()
    for arquivo, campo in VALORES.items():
        for l in arquivos[arquivo]:
            ident = l["id_saida"]
            exigir(ident and ident not in destinos, "ID de saída ausente ou duplicado entre relatórios")
            destinos.add(ident)
            produtor = next((p for prefixo,p in PRODUTORES.items() if ident.startswith(prefixo)), None)
            if ident.startswith("REVISAO_PONTE:"):
                produtor = "DIVERGENCIAS_REMESSA" if ident.endswith(":DIV") else "REMESSAS" if ident.endswith(":COM") else None
            exigir(produtor and produtor in m["resultados"][arquivo]["partes"]
                   and m["partes"][produtor]["rastro_validado"], "Saída sem produtor validado no contrato interno")
            if arquivo == "pendencias.csv":
                exigir(all(l.get(c) for c in ("tipo", "ref_origem", "motivo", "quem_decide", "proximo_passo")), "Pendência incompleta (RN-58)")
                exigir(l.get("categoria") in {"DADOS", "NEGOCIO"}, "Categoria de pendência inválida")
                if l[campo] == "":
                    exigir(l.get("natureza_valor") == "NAO_INFORMADO", "Valor desconhecido sem natureza explícita")
                    desconhecidos.add(ident)
                else:
                    valores[ident] = dinheiro(l[campo])
            else:
                valores[ident] = dinheiro(l[campo])
            for c in ("cnpj", "tomador_cnpj"):
                if c in l and (arquivo != "pendencias.csv" or l[c]):
                    exigir(re.fullmatch(r"[0-9]{14}", l[c]), "CNPJ fora do contrato")
            if "linha_negocio" in l:
                exigir(l["linha_negocio"] in {"CHECKOUT", "REMESSA"}, "Linha de negócio fora do domínio")
            for c in ("taxa_contratada_pct", "taxa_aplicada_pct"):
                if c in l:
                    exigir(re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", l[c]), "Percentual fora do formato decimal")
            if arquivo == "notas_a_emitir.csv":
                exigir(valores[ident] > 0 and l["tomador"] and l["discriminacao"], "Proposta de nota inválida")
            if arquivo == "lancamentos_classificados.csv":
                exigir(l["banco"] in {"AURORA", "MERIDIANO"} and l["metodo"] in {"REGRA", "IA", "HUMANO"}, "Banco/método fora do domínio")
                exigir(re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", l["confianca"]) and 0 <= Decimal(l["confianca"]) <= 1, "Confiança fora do domínio")
                exigir(re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", l["data"]), "Data fora do formato ISO")
                date.fromisoformat(l["data"])
                exigir(l["ref_origem"] and l["descricao"] and re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", l["conta_codigo"]), "Lançamento sem referência, descrição ou conta válida")
    somas, origens = defaultdict(lambda: Decimal(0)), set()
    for r in arquivos["rastro.csv"]:
        ident = r["id_saida"]
        exigir(ident in valores and ident not in desconhecidos, "Rastro sem destino monetário conhecido")
        chave = ident, r["arquivo_origem"], r["ref_origem"]
        exigir(all(chave) and chave not in origens, "Origem do rastro duplicada ou ausente")
        origens.add(chave)
        somas[ident] += dinheiro(r["valor"])
    exigir(set(somas) == set(valores) and all(somas[k] == v for k,v in valores.items()), "Soma do rastro não fecha no conjunto integrado")
    return dict(destinos=len(destinos), monetarios=len(valores), desconhecidos=len(desconhecidos), rastros=len(arquivos["rastro.csv"]))
