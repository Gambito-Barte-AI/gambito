"""Auditoria A3 independente: MIME/XLSX com biblioteca padrão, sem importar tarvo."""

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from email import policy
from email.parser import BytesParser
from hashlib import sha256
from io import BytesIO
import re
import unicodedata
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from validar_saida import exigir, dinheiro

NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def normalizar(v):
    return " ".join(''.join(c for c in unicodedata.normalize("NFKD", str(v or "")) if not unicodedata.combining(c)).lower().split())


def planilhas(raw):
    with ZipFile(BytesIO(raw)) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = [''.join(s.itertext()) for s in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        livro = ET.fromstring(z.read("xl/workbook.xml"))
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        for aba in livro.find("x:sheets", NS):
            alvo = rels[aba.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
            alvo = alvo.lstrip("/") if alvo.startswith("/") else "xl/" + alvo
            linhas = []
            for linha in ET.fromstring(z.read(alvo)).findall("x:sheetData/x:row", NS):
                campos = {}
                for c in linha:
                    letra = re.match(r"[A-Z]+", c.attrib["r"])[0]
                    v = c.find("x:v", NS)
                    texto = v.text if v is not None else ""
                    if c.attrib.get("t") == "inlineStr":
                        texto = ''.join(t.text or "" for t in c.findall(".//x:t", NS))
                    elif c.attrib.get("t") == "s":
                        texto = strings[int(texto)]
                    elif c.attrib.get("t", "n") == "n" and texto:
                        # XLSX armazena números como double; normaliza a representação
                        # física antes da aritmética exclusivamente Decimal.
                        n = Decimal(str(float(texto)))
                        texto = format(n.to_integral_value() if n == n.to_integral_value() else n, "f")
                    if c.find("x:f", NS) is not None:
                        texto = "FORMULA_NAO_SUPORTADA"
                    campos[letra] = texto
                linhas.append((int(linha.attrib["r"]), campos))
            yield aba.attrib["name"], linhas


def tabelas(raw, assinatura):
    for aba, linhas in planilhas(raw):
        colunas = None
        for numero, campos in linhas:
            if colunas is None:
                nomes = {normalizar(v): k for k, v in campos.items()}
                if assinatura <= set(nomes):
                    colunas = nomes
            else:
                yield aba, numero, {n: campos.get(coluna, "") for n, coluna in colunas.items()}


def numero(s):
    s = str(s).strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return Decimal(s[:-1]) / 100 if s.endswith("%") else Decimal(s)


def data(s):
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except ValueError:
        return date(1899, 12, 30) + timedelta(days=int(numero(s)))


def centavos(v):
    return v.quantize(Decimal(".01"), ROUND_HALF_UP)


def verificar(m, arquivos, config, pasta):
    prefixos = ("REMESSA:", "DIVERGENCIA:REMESSA:", "CONTESTACAO_PONTE:", "REVISAO_PONTE:",
                "DUPLICATA_PONTE:", "SPREAD_NEGATIVO:", "AJUSTE_D10:", "ACOMPANHAMENTO_PONTE:",
                "CADASTRO_PONTE:", "LEITURA_PONTE:")
    saidas = [s for nome, linhas in arquivos.items() if nome != "rastro.csv" for s in linhas if s["id_saida"].startswith(prefixos)]
    rastros = [r for r in arquivos["rastro.csv"] if r["id_saida"].startswith(prefixos)]
    if m["escopo_comando"] == "checkout":
        exigir(not saidas and not rastros, "Ponte publicada fora do escopo solicitado")
        return
    fonte = m.get("fontes", {}).get("ponte", {})
    origens = {}
    periodos = {}
    exigir({p.name for p in pasta.glob("*.eml")} == {e["arquivo"] for e in fonte.get("arquivos", [])},
           "Fonte Ponte omite e-mail da pasta")
    for email in fonte.get("arquivos", []):
        caminho = pasta / email["arquivo"]
        exigir(caminho.name == email["arquivo"] and sha256(caminho.read_bytes()).hexdigest() == email["sha256"], "Fonte Ponte alterada")
        if email["situacao"] != "DISPONIVEL":
            continue
        mensagem = BytesParser(policy=policy.default).parsebytes(caminho.read_bytes())
        for parte in mensagem.walk():
            nome = (parte.get_filename() or "").replace("\\", "/").split("/")[-1]
            registrado = next((a for a in email["anexos"] if a["arquivo"] == nome), None)
            if registrado is None:
                continue
            raw = parte.get_payload(decode=True)
            exigir(sha256(raw).hexdigest() == registrado["sha256"], "Hash do anexo Ponte incorreto")
            for aba, linhas in planilhas(raw):
                for _, campos in linhas:
                    for valor in campos.values():
                        periodo = re.match(r"competencia:\s*(0[1-9]|1[0-2])/(\d{4})\b", normalizar(valor))
                        if periodo:
                            periodos[f"{email['arquivo']}::{nome}::{aba}"] = f"{periodo[2]}-{periodo[1]}"
            for aba, linha, e in tabelas(raw, {"no operacao", "data contratacao", "spread r$"}):
                if any(e.values()) and not normalizar(e.get("no operacao", "")).startswith(("total de operacoes", "spread total")):
                    try:
                        mes = data(e["data contratacao"]).strftime("%Y-%m")
                    except (ValueError, ArithmeticError, KeyError):
                        mes = fonte.get("competencia")
                    origem_arquivo = f"{email['arquivo']}::{nome}::{aba}"
                    if e.get("observacao", "").upper().startswith("AJUSTE REF"):
                        mes = periodos.get(origem_arquivo) or fonte.get("competencia") or mes
                    if fonte.get("competencia") and mes != fonte["competencia"]:
                        continue
                    origens[origem_arquivo, e.get("no operacao") or f"L{linha}", str(linha)] = e
    if not saidas:
        exigir(not rastros, "Rastro Ponte sem saída")
        exigir(not origens or not m["partes"]["REMESSAS"]["rastro_validado"], "Operações Ponte sem destino")
        return
    exigir(config.get("remessas"), "Ponte sem regras")
    parametros = config["remessas"]
    fracao = numero(parametros["participacao_fracao"])
    tolerancia = numero(parametros["tolerancia_pp"]) / 100
    por_saida = {s["id_saida"]: s for s in saidas}
    exigir(len(por_saida) == len(saidas), "ID Ponte repetido")
    somas, detalhes = defaultdict(Decimal), defaultdict(list)
    calculadas = set()
    fonte_contrato = m.get("fontes", {}).get("contratos_remessa", {})
    contratos = {}
    if fonte_contrato.get("situacao") == "DISPONIVEL":
        caminho = pasta / fonte_contrato["arquivo"]
        exigir(sha256(caminho.read_bytes()).hexdigest() == fonte_contrato["sha256"], "Contrato remessa alterado")
        contratos = {(aba, f"{aba}!L{linha}"): campos for aba, linha, campos in tabelas(caminho.read_bytes(),
                      {"cnpj", "spread remessa", "vigencia"})}
    for r in rastros:
        identificador = r["id_saida"]
        exigir(identificador in por_saida, "Rastro Ponte sem destino")
        chave = r["arquivo_origem"], r["ref_origem"], r.get("linha_origem")
        exigir(chave in origens, "Rastro Ponte sem linha física no anexo")
        e = origens[chave]
        spread = numero(e["spread r$"])
        cnpj = re.sub(r"[^0-9]", "", e["cnpj cliente"]).zfill(14)
        exigir(por_saida[identificador]["cnpj"] == cnpj, "CNPJ Ponte divergente da origem")
        exigir(r.get("data_base_taxa") == data(e["data contratacao"]).isoformat(), "Competência/data Ponte incorreta")
        valor = dinheiro(r["valor"])
        somas[identificador] += valor
        detalhes[identificador].append((r, e))
        if identificador.startswith("REMESSA:"):
            exigir(r["ref_origem"] not in calculadas, "Operação Ponte calculada duas vezes")
            calculadas.add(r["ref_origem"])
            mes = data(e["data contratacao"]).strftime("%Y-%m")
            if e.get("observacao", "").upper().startswith("AJUSTE REF"):
                mes = periodos.get(r["arquivo_origem"]) or fonte.get("competencia") or mes
            exigir(identificador == f"REMESSA:{mes}:{cnpj}", "Competência da comissão Ponte incorreta")
            exigir(valor == centavos(spread * fracao), "Comissão Ponte não corresponde à participação realizada")
            if spread < 0:
                ajuste = re.fullmatch(r"AJUSTE REF (PC-[A-Z0-9-]+)(?:\s.*)?", e.get("observacao", "").upper())
                exigir(ajuste and r.get("ref_original") == ajuste[1] and r.get("ref_evento_original") == ajuste[1]
                       and r.get("regra") == "D-10_PENDENTE_FINANCEIRO", "Negativo irregular/ajuste sem vínculo na comissão")
                exigir(any(s["tipo"] == "AJUSTE_PONTE_D10_PENDENTE" and s.get("ref_original") == ajuste[1]
                           for s in arquivos["pendencias.csv"]), "Ajuste sem D-10 explícita")
        elif identificador.startswith("DIVERGENCIA:REMESSA:") or identificador.startswith("SPREAD_NEGATIVO:"):
            s = por_saida[identificador]
            if r.get("ref_contrato"):
                campos = next((c for (_, ref), c in contratos.items() if ref == r["ref_contrato"]), None)
                exigir(campos is not None, "Referência de contrato Ponte inexistente")
                bruto = campos["spread remessa"]
                contratada = numero(parametros["spread_padrao_fracao"]) if normalizar(bruto) in {"", "padrao"} else numero(bruto)
                exigir(Decimal(r["taxa_contratada_fracao"]) == contratada, "Spread contratual Ponte adulterado")
                exigir(re.sub(r"[^0-9]", "", campos["cnpj"]).zfill(14) == cnpj, "Contrato de outro CNPJ na Ponte")
                d = data(e["data contratacao"])
                vigencia = normalizar(campos["vigencia"])
                if vigencia.startswith("ate "):
                    exigir(d <= data(vigencia[4:]), "Contrato Ponte fora da vigência")
                else:
                    exigir(d >= data(vigencia.removeprefix("a partir de ")), "Contrato Ponte fora da vigência")
                for regra in config.get("vigencias_spread", []):
                    if regra["cnpj"] == cnpj:
                        exigir(d >= regra["inicio"], "Spread aplicado antes da vigência confirmada")
                ptax_me = numero(e["ptax ref."]) * numero(e["valor me"])
                if identificador.startswith("DIVERGENCIA:"):
                    delta = numero(e["spread %"]) - contratada
                    exigir(spread >= 0 and abs(delta) > tolerancia and valor == centavos(delta * ptax_me), "Fórmula/tolerância da divergência Ponte incorreta")
                    exigir(Decimal(s["taxa_contratada_pct"]) == contratada * 100 and Decimal(s["taxa_aplicada_pct"]) == numero(e["spread %"]) * 100,
                           "Percentuais Ponte fora do contrato")
                else:
                    exigir(valor == centavos(spread - contratada * ptax_me), "Pedido de spread negativo incorreto")
                    exigir(dinheiro(s["valor_reportado_brl"]) == spread and dinheiro(s["valor_solicitado_brl"]) == valor,
                           "D-11 perdeu um dos dois valores")
    for s in saidas:
        identificador = s["id_saida"]
        campo = "comissao_brl" if identificador.startswith("REMESSA:") else "diferenca_brl" if identificador.startswith("DIVERGENCIA:") else "valor_brl"
        if s[campo] == "":
            exigir(s.get("natureza_valor") == "NAO_INFORMADO" and identificador not in detalhes, "Valor Ponte desconhecido virou rastro monetário")
        else:
            exigir(identificador in detalhes and somas[identificador] == dinheiro(s[campo]), "Soma do rastro Ponte não reconcilia")
        if campo == "valor_brl":
            exigir(s.get("proximo_passo") and s.get("quem_decide"), "Pendência Ponte sem próximo passo/responsável")
            if identificador.startswith("SPREAD_NEGATIVO:"):
                e = origens[s["arquivo_origem"], s["ref_origem"], s["linha_origem"]]
                exigir(dinheiro(s["valor_reportado_brl"]) == numero(e["spread r$"]), "Valor negativo reportado alterado")
                exigir(s["valor_solicitado_brl"] == s["valor_brl"], "Valor solicitado distinto do principal D-11")
    # As duas representações da contestação devem carregar exatamente os mesmos detalhes.
    for s in saidas:
        if s["id_saida"].startswith("CONTESTACAO_PONTE:"):
            esperados = {(r["arquivo_origem"], r["ref_origem"], r["valor"]) for r in rastros
                         if r["id_saida"].startswith("DIVERGENCIA:REMESSA:") and por_saida[r["id_saida"]]["cnpj"] == s["cnpj"]}
            obtidos = {(r["arquivo_origem"], r["ref_origem"], r["valor"]) for r, _ in detalhes[s["id_saida"]]}
            exigir(esperados == obtidos, "Contestação Ponte diverge das operações")
    if m["partes"]["REMESSAS"]["rastro_validado"]:
        destinos = [(r["arquivo_origem"], r["ref_origem"], r["linha_origem"]) for r in rastros if r["id_saida"].startswith("REMESSA:")]
        pendentes = [s for s in saidas if s["id_saida"].startswith(("DUPLICATA_PONTE:", "SPREAD_NEGATIVO:", "LEITURA_PONTE:"))
                     or (s["id_saida"].startswith("REVISAO_PONTE:") and s["id_saida"].endswith(":COM"))]
        destinos += [(s["arquivo_origem"], s["ref_origem"], s["linha_origem"]) for s in pendentes]
        exigir(Counter(destinos) == Counter(origens.keys()), "Cobertura física Ponte incompleta ou duplicada")
        cobertura = m["partes"]["REMESSAS"]["cobertura"]
        exigir(cobertura == dict(linhas_lidas=len(origens), calculadas=len(destinos) - len(pendentes),
                                 pendentes=len(pendentes), bloqueadas=0), "Cobertura Ponte declarada incorreta")
