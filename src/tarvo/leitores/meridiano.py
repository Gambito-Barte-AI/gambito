"""OFX SGML local: FITID preservado; registros inseguros viram diagnóstico."""

from collections import Counter
from datetime import datetime
from decimal import Decimal, DecimalException
from html import unescape
from pathlib import Path
import re

from ..modelos import ErroEntrada, MovimentoBanco, Origem

TRANSACAO = re.compile(r"<STMTTRN\s*>(.*?)</STMTTRN\s*>", re.I | re.S)
TIPOS = {"CREDIT", "DEBIT", "INT", "DIV", "FEE", "SRVCHG", "DEP", "ATM", "POS", "XFER",
         "CHECK", "PAYMENT", "CASH", "DIRECTDEP", "DIRECTDEBIT", "REPEATPMT", "OTHER"}


def descobrir(pasta: Path) -> Path:
    candidatos = sorted(p for p in pasta.glob("*") if p.is_file() and p.suffix.lower() == ".ofx")
    if len(candidatos) != 1:
        raise ErroEntrada(f"Meridiano: esperado um OFX; encontrados {len(candidatos)}")
    return candidatos[0]


def decodificar(raw):
    raw = raw.removeprefix(b"\xef\xbb\xbf")
    cabecalho = raw.split(b"<", 1)[0].decode("ascii", errors="strict")
    if not re.search(r"(?im)^DATA\s*:\s*OFXSGML\s*$", cabecalho):
        raise ValueError("esperado OFX SGML; outro formato exige leitor compatível")
    if re.search(r"(?im)^CHARSET\s*:\s*(?:1252|WINDOWS-1252)\s*$", cabecalho):
        return raw.decode("cp1252"), "cp1252"
    if re.search(r"(?im)^(?:ENCODING|CHARSET)\s*:\s*(?:UTF-8|UTF8|65001)\s*$", cabecalho):
        return raw.decode("utf-8-sig"), "utf-8"
    raise ValueError("OFX SGML exige encoding declarado cp1252 ou UTF-8")


def campos(texto):
    """Lê folhas SGML com fechamento opcional, sem rede nem execução de conteúdo."""
    folhas, fechamentos = {}, []
    tokens = list(re.finditer(r"<(/?)([A-Za-z0-9_]+)\s*>([^<]*)", texto))
    if re.sub(r"<(/?)([A-Za-z0-9_]+)\s*>([^<]*)", "", texto).strip():
        raise ValueError("tag SGML ou texto fora do contrato")
    for t in tokens:
        fecha, nome, valor = t.groups(); nome = nome.upper()
        if fecha:
            if valor.strip() or not fechamentos or fechamentos[-1] != nome:
                raise ValueError("fechamento de campo inconsistente")
            fechamentos.pop()
        else:
            # Em SGML a próxima folha pode encerrar implicitamente a anterior.
            fechamentos = [nome]
            if nome in folhas:
                raise ValueError(f"campo {nome} repetido")
            folhas[nome] = unescape(valor.strip())
    return folhas


def data_ofx(texto):
    if not re.fullmatch(r"[0-9]{8}(?:[0-9]{6}(?:\.[0-9]+)?)?(?:\[[+-]?[0-9]+(?:\.[0-9]+)?(?::[^\[\]\r\n]+)?\])?", texto):
        raise ValueError("DTPOSTED inválido")
    if len(re.match(r"[0-9]+", texto)[0]) == 14:
        datetime.strptime(texto[:14], "%Y%m%d%H%M%S")
    return datetime.strptime(texto[:8], "%Y%m%d").date()  # data local declarada, sem conversão UTC


def ler(caminho: Path):
    try:
        texto, encoding = decodificar(caminho.read_bytes())
        corpo = texto[texto.index("<"):]
        if re.search(r"<!|<\?", corpo) or len(re.findall(r"<OFX\s*>", corpo, re.I)) != 1 or not re.search(r"</OFX\s*>\s*$", corpo, re.I):
            raise ValueError("estrutura OFX SGML não suportada ou truncada")
        agregados = {"OFX", "SIGNONMSGSRSV1", "SONRS", "STATUS", "BANKMSGSRSV1", "STMTTRNRS",
                     "STMTRS", "BANKACCTFROM", "BANKTRANLIST", "STMTTRN", "LEDGERBAL", "AVAILBAL"}
        pilha = []
        for tag in re.finditer(r"<(/?)([A-Za-z0-9_]+)\s*>", corpo):
            fecha, nome = tag[1], tag[2].upper()
            if nome in agregados:
                if fecha:
                    if not pilha or pilha.pop() != nome:
                        raise ValueError("agregado OFX truncado ou fora de ordem")
                else:
                    pilha.append(nome)
        if pilha:
            raise ValueError("agregado OFX não encerrado")
        if len(re.findall(r"<STMTRS\s*>", corpo, re.I)) != 1:
            raise ValueError("esperado um único extrato/conta no OFX")
        moeda = re.findall(r"<CURDEF\s*>([^<]+)", corpo, re.I)
        if len(moeda) != 1 or moeda[0].strip().upper() != "BRL":
            raise ValueError("moeda do extrato deve ser BRL; sem conversão presumida")
        for status in re.findall(r"<STATUS\s*>(.*?)</STATUS\s*>", corpo, re.I | re.S):
            if campos(status).get("CODE") != "0":
                raise ValueError("OFX contém status de erro do banco")
        contas = re.findall(r"<BANKACCTFROM\s*>(.*?)</BANKACCTFROM\s*>", corpo, re.I | re.S)
        if len(contas) != 1:
            raise ValueError("conta bancária ausente ou repetida")
        conta = campos(contas[0])
        if not all(conta.get(k) for k in ("BANKID", "ACCTID", "ACCTTYPE")):
            raise ValueError("identificação da conta incompleta")
        listas = list(re.finditer(r"<BANKTRANLIST\s*>(.*?)</BANKTRANLIST\s*>", corpo, re.I | re.S))
        if len(listas) != 1:
            raise ValueError("lista de movimentos ausente, múltipla ou truncada")
        lista = listas[0]; trecho = lista[1]; registros = list(TRANSACAO.finditer(trecho))
        if (len(registros) != len(re.findall(r"<STMTTRN\s*>", corpo, re.I))
                or len(registros) != len(re.findall(r"</STMTTRN\s*>", corpo, re.I))):
            raise ValueError("registro de movimento truncado, aninhado ou fora da lista")
        periodo = campos(TRANSACAO.sub("", trecho))
        if set(periodo) != {"DTSTART", "DTEND"}:
            raise ValueError("período ou conteúdo da lista incompatível")
        inicio, fim = data_ofx(periodo["DTSTART"]), data_ofx(periodo["DTEND"])
        if inicio > fim:
            raise ValueError("período OFX invertido")
        normalizados = []
        for t in registros:
            numero = texto.count("\n", 0, texto.index("<") + lista.start(1) + t.start()) + 1
            erros, data, valor = [], None, None
            try:
                c = campos(t[1])
            except ValueError as exc:
                # Campos repetidos são ambíguos: não escolher silenciosamente um valor/FITID.
                raise ValueError(f"L{numero}: {exc}") from exc
            ref = c.get("FITID", "")
            if not ref or any(ord(ch) < 32 for ch in ref):
                erros.append("FITID ausente ou inválido; referência física usada somente para diagnóstico")
                ref = f"L{numero}"
            try:
                data = data_ofx(c.get("DTPOSTED", ""))
            except ValueError:
                erros.append("DTPOSTED inválido")
            quantia = c.get("TRNAMT", "")
            if re.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]{1,2})?", quantia):
                valor = Decimal(quantia).quantize(Decimal("0.01"))
            else:
                erros.append("TRNAMT inválido; não substituído por zero nem arredondado")
            tipo = c.get("TRNTYPE", "").upper()
            if tipo not in TIPOS or (valor is not None and ((tipo == "CREDIT" and valor < 0) or (tipo == "DEBIT" and valor > 0))):
                erros.append("TRNTYPE ausente, desconhecido ou incompatível com o sinal")
            descricao = c.get("MEMO") or c.get("NAME", "")
            if not descricao:
                erros.append("histórico MEMO/NAME ausente")
            normalizados.append((ref, data, descricao, valor, erros, numero, c.get("FITID", "")))
        ids = Counter(v[6] for v in normalizados if v[6])
        movimentos = []
        for ref, data, descricao, valor, erros, numero, original in normalizados:
            if original and ids[original] > 1:
                erros.append("FITID repetido no extrato; ocorrências pendentes, sem escolher nem somar uma delas")
            movimentos.append(MovimentoBanco(Origem(caminho.name, ref, numero), data, descricao, valor, "; ".join(erros)))
        return movimentos, dict(encoding=encoding, conta=conta, inicio=inicio.isoformat(), fim=fim.isoformat(),
            movimentos_lidos=len(movimentos), fitids_repetidos=sorted(k for k,v in ids.items() if v > 1),
            fitids_ausentes=sum(not r[6] for r in normalizados))
    except (ValueError, OSError, UnicodeError, DecimalException) as exc:
        raise ErroEntrada(f"{caminho.name}: Meridiano: {exc}") from exc
