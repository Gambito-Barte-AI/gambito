"""Auditoria OFX independente: HTMLParser padrão, sem importar o motor."""

from collections import Counter
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from html.parser import HTMLParser
import re

from auditoria_a5 import auditar_movimentos, fonte, ler_plano
from validar_saida import exigir


class Extrato(HTMLParser):
    def __init__(self, texto):
        super().__init__(convert_charrefs=True)
        self.registros, self.atual, self.campo = [], None, None
        self.conta, self.periodo = {}, {}
        self.em_conta = self.em_lista = False
        self.feed(texto)
        self.close()
        exigir(self.atual is None and not self.em_lista, "OFX truncado")

    def handle_starttag(self, tag, attrs):
        exigir(not attrs, "Atributo OFX não suportado")
        if tag == 'bankacctfrom': self.em_conta = True
        if tag == 'banktranlist':
            exigir(not self.em_lista, "Lista OFX aninhada")
            self.em_lista = True
        if tag == 'stmttrn':
            exigir(self.atual is None and self.em_lista, "Movimento OFX fora da lista/aninhado")
            self.atual = ({}, self.getpos()[0])
        self.campo = tag.upper()

    def handle_endtag(self, tag):
        if tag == 'stmttrn':
            exigir(self.atual is not None, "Fechamento OFX sem movimento")
            self.registros.append(self.atual); self.atual = None
        if tag == 'bankacctfrom': self.em_conta = False
        if tag == 'banktranlist': self.em_lista = False
        self.campo = None

    def handle_data(self, data):
        valor = data.strip()
        if not valor or self.campo is None: return
        destino = self.atual[0] if self.atual else self.conta if self.em_conta else self.periodo if self.em_lista else None
        if destino is not None:
            exigir(self.campo not in destino, "Folha OFX ambígua/repetida")
            destino[self.campo] = valor


def data_ofx(texto):
    if not re.fullmatch(r'[0-9]{8}(?:[0-9]{6}(?:\.[0-9]+)?)?(?:\[[+-]?[0-9]+(?:\.[0-9]+)?(?::[^\[\]\r\n]+)?\])?', texto):
        return None
    try:
        if len(re.match(r'[0-9]+', texto)[0]) == 14: datetime.strptime(texto[:14], '%Y%m%d%H%M%S')
        return datetime.strptime(texto[:8], '%Y%m%d').date()
    except ValueError:
        return None


def verificar(m, arquivos, config, dados, caminho_regras):
    classificados = [c for c in arquivos['lancamentos_classificados.csv'] if c['banco'] == 'MERIDIANO']
    ps = [p for p in arquivos['pendencias.csv'] if p['id_saida'].startswith('PENDENCIA_MERIDIANO:')]
    rs = [r for r in arquivos['rastro.csv'] if r['id_saida'].startswith(('MERIDIANO:', 'PENDENCIA_MERIDIANO:'))]
    exigir(all(c['banco'] in {'AURORA','MERIDIANO'} for c in arquivos['lancamentos_classificados.csv']), 'Banco sem contrato')
    parte = m['partes']['EXTRATO_MERIDIANO']
    if m['escopo_comando'] == 'checkout' or not parte['rastro_validado']:
        exigir(not classificados and not ps and not rs, 'Meridiano indisponível/fora do escopo publicou valores')
        return
    exigir(sha256(caminho_regras.read_bytes()).hexdigest() == m['fontes']['regras']['sha256'], 'Regras alteradas')
    regras = config.get('classificacao_meridiano', [])
    exigir(regras and m['fontes']['regras'].get('parametros_classificacao_meridiano') == regras, 'Regras Meridiano sem proveniência')
    contas, plano = ler_plano(m, dados)
    extrato = fonte(m, dados, 'meridiano')
    raw = extrato.read_bytes().removeprefix(b'\xef\xbb\xbf'); cabecalho = raw.split(b'<',1)[0].decode('ascii')
    encoding = 'cp1252' if re.search(r'(?im)^CHARSET\s*:\s*(?:1252|WINDOWS-1252)\s*$', cabecalho) else 'utf-8'
    texto = raw.decode('cp1252' if encoding == 'cp1252' else 'utf-8-sig')
    parser = Extrato(texto)
    ids = Counter(c.get('FITID','') for c,n in parser.registros if c.get('FITID',''))
    tipos = {'CREDIT','DEBIT','INT','DIV','FEE','SRVCHG','DEP','ATM','POS','XFER','CHECK','PAYMENT','CASH','DIRECTDEP','DIRECTDEBIT','REPEATPMT','OTHER'}
    movimentos = []
    for c,n in parser.registros:
        ref = c.get('FITID','')
        data = data_ofx(c.get('DTPOSTED',''))
        texto_valor = c.get('TRNAMT','')
        valor = Decimal(texto_valor).quantize(Decimal('0.01')) if re.fullmatch(r'[+-]?[0-9]+(?:\.[0-9]{1,2})?', texto_valor) else None
        descricao = c.get('MEMO') or c.get('NAME','')
        tipo = c.get('TRNTYPE','').upper()
        valido = (bool(ref) and not any(ord(ch)<32 for ch in ref) and ids[ref] == 1 and data is not None
                  and valor is not None and bool(descricao) and tipo in tipos
                  and not ((tipo == 'CREDIT' and valor < 0) or (tipo == 'DEBIT' and valor > 0)))
        movimentos.append((ref if ref and not any(ord(ch)<32 for ch in ref) else f'L{n}', data, descricao, valor, valido, n))
    f = m['fontes']['meridiano']; i = f['ingestao']
    exigir(i == dict(encoding=encoding, conta=parser.conta, inicio=data_ofx(parser.periodo['DTSTART']).isoformat(),
        fim=data_ofx(parser.periodo['DTEND']).isoformat(), movimentos_lidos=len(movimentos),
        fitids_repetidos=sorted(k for k,v in ids.items() if v>1), fitids_ausentes=sum(not c.get('FITID','') for c,n in parser.registros)), 'Inventário OFX incorreto')
    selecionados = [v for v in movimentos if v[1] is None or v[1].strftime('%Y-%m') == f['competencia']]
    exigir(f['fora_competencia'] == len(movimentos)-len(selecionados), 'Recorte Meridiano incorreto')
    auditar_movimentos(parte, classificados, ps, rs, regras, contas, plano, extrato, selecionados, 'MERIDIANO')
