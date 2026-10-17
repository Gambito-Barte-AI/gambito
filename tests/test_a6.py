"""A6: OFX sintético, FITID, classificação, falhas isoladas e regressão."""

import csv
from hashlib import sha256
import json
from pathlib import Path
import unittest

import test_aceite as amostras
from validar_saida import ErroAceite, verificar
from tarvo.execucao import executar
from tarvo.exportacao import publicar
from tarvo.leitores import meridiano
from tarvo.modelos import ErroEntrada


class A6Test(unittest.TestCase):
    vendas = amostras.AceiteTest.vendas

    def setUp(self):
        amostras.AceiteTest.setUp(self)
        self.plano = self.dados/'catalogo_livre.csv'
        self.plano.write_text('COD_CONTA;DESCRICAO;TIPO;NATUREZA;ACEITA_LANCTO;COD_SUPERIOR;DT_CRIACAO\n'
            '1.7;Recursos de clientes;ANALITICA;C;S;;01/01/2032\n'
            '1.9;Comissão a receber;ANALITICA;D;S;;01/01/2032\n'
            '2.8;Tarifas;ANALITICA;D;S;;01/01/2032\n',encoding='latin-1')
        self.extrato = self.dados/'arquivo_sem_nome_mensal.ofx'
        self.base = self.regras.read_text(encoding='utf-8')
        self.rs = [self.regra('RECURSO',r'^pix receb recurso livre','CREDITO','1.7'),
                   self.regra('LIQUIDACAO',r'^ted enviada liquidacao','DEBITO','1.7'),
                   self.regra('TARIFA',r'^tarifa','DEBITO','2.8')]
        self.configurar(self.rs)
        self.ofx([{},dict(FITID='OUTRA',TRNTYPE='DEBIT',TRNAMT='-12.34',MEMO='TARIFA')])

    def regra(self,id,padrao,sinal,conta):
        return dict(id=id,padrao=padrao,sinal=sinal,conta_codigo=conta,fonte='Fonte sintética',
                    aprovacao='Critério para teste',aprovador='Teste',aprovado_em='NAO_INFORMADO',natureza='INTERPRETACAO_TECNICA')

    def configurar(self, regras):
        s=self.base
        for r in regras:
            s+='\n[[classificacao_meridiano]]\n'+'\n'.join(f'{k} = {json.dumps(v,ensure_ascii=False)}' for k,v in r.items())+'\n'
        self.regras.write_text(s,encoding='utf-8')

    def ofx(self, registros, encoding='cp1252', fechados=False):
        s=f'OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:{"UTF-8" if encoding.startswith("utf-8") else "USASCII"}\nCHARSET:{"65001" if encoding.startswith("utf-8") else "1252"}\n\n'
        folha=lambda k,v:f'<{k}>{v}'+(f'</{k}>' if fechados else '')+'\n'
        s+='<OFX>\n<BANKMSGSRSV1>\n<STMTTRNRS>\n<STATUS>\n'+folha('CODE','0')+'<SEVERITY>INFO\n</STATUS>\n<STMTRS>\n'+folha('CURDEF','BRL')
        s+='<BANKACCTFROM>\n'+''.join(folha(k,v) for k,v in dict(BANKID='1234',ACCTID='LIVRE-1',ACCTTYPE='CHECKING').items())+'</BANKACCTFROM>\n<BANKTRANLIST>\n'+folha('DTSTART','20320401000000[-3:BRT]')+folha('DTEND','20320531235959[-3:BRT]')
        for r in registros:
            c=dict(TRNTYPE='CREDIT',DTPOSTED='20320402120000[-3:BRT]',TRNAMT='123.45',FITID='FITID-LIVRE',MEMO='PIX RECEB RECURSO LIVRE')
            c.update(r)
            s+='<STMTTRN>\n'+''.join(folha(k,v) for k,v in c.items() if v is not None)+'</STMTTRN>\n'
        s+='</BANKTRANLIST>\n<LEDGERBAL>\n'+folha('BALAMT','999.99')+folha('DTASOF','20320430235959[-3:BRT]')+'</LEDGERBAL>\n</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>\n'
        self.extrato.write_text(s,encoding=encoding,newline='\n')

    def rodar(self, competencia=None, escopo='alvo'):
        r=executar(self.dados,self.regras,competencia)
        m=publicar(r,self.saida,escopo)
        verificar(self.dados,self.saida,self.regras)
        return r,m

    def test_fluxo_ofx_fitid_e_sinais_sem_depender_de_aurora_ou_ponte(self):
        r,m=self.rodar();p=r.partes['EXTRATO_MERIDIANO']
        self.assertEqual(p.situacao,'COMPLETO')
        self.assertEqual(p.cobertura,dict(linhas_lidas=2,calculadas=2,pendentes=0,bloqueadas=0))
        ls=p.linhas['lancamentos_classificados.csv']
        self.assertEqual([l['ref_origem'] for l in ls],['FITID-LIVRE','OUTRA'])
        self.assertEqual([l['valor'] for l in ls],['123.45','-12.34'])
        self.assertTrue(all(l['banco']=='MERIDIANO' and l['metodo']=='REGRA' and l['confianca']=='1' for l in ls))
        self.assertEqual(ls[0]['data'],'2032-04-02')
        self.assertEqual(m['fontes']['meridiano']['ingestao']['conta']['ACCTID'],'LIVRE-1')
        self.assertEqual(r.partes['EXTRATO_AURORA'].situacao,'BLOQUEADO')

    def test_encoding_acentos_e_folhas_com_fechamento_opcional(self):
        for encoding in ('cp1252','utf-8-sig'):
            self.ofx([dict(MEMO='PIX RECEB RECURSO LIVRE CÂMBIO ÊXITO',FITID='REF-CÂMBIO')],encoding,True)
            r,_=self.rodar();l=r.partes['EXTRATO_MERIDIANO'].linhas['lancamentos_classificados.csv'][0]
            self.assertEqual(l['descricao'],'PIX RECEB RECURSO LIVRE CÂMBIO ÊXITO')
            self.assertEqual(l['ref_origem'],'REF-CÂMBIO')

    def test_data_ofx_preserva_dia_local_sem_deslocamento_utc(self):
        self.ofx([dict(DTPOSTED='20320430235959.123[-3:BRT]')])
        r,_=self.rodar()
        self.assertEqual(r.partes['EXTRATO_MERIDIANO'].linhas['lancamentos_classificados.csv'][0]['data'],'2032-04-30')

    def test_fitid_nao_depende_da_ordem_dos_registros(self):
        self.ofx([dict(FITID='B'),dict(FITID='A',TRNAMT='77.89')])
        r,_=self.rodar(); ls=r.partes['EXTRATO_MERIDIANO'].linhas['lancamentos_classificados.csv']
        antes={l['ref_origem']:(l['id_saida'],l['valor']) for l in ls}
        self.ofx([dict(FITID='A',TRNAMT='77.89'),dict(FITID='B')])
        r,_=self.rodar(); ls=r.partes['EXTRATO_MERIDIANO'].linhas['lancamentos_classificados.csv']
        self.assertEqual(antes,{l['ref_origem']:(l['id_saida'],l['valor']) for l in ls})

    def test_fitid_duplicado_igual_ou_conflitante_deixa_todas_ocorrencias_pendentes(self):
        for v in ('123.45','999.99'):
            self.ofx([{},dict(TRNAMT=v)])
            r,_=self.rodar();p=r.partes['EXTRATO_MERIDIANO']
            self.assertEqual(p.situacao,'PROVISORIO')
            self.assertEqual(p.linhas['lancamentos_classificados.csv'],[])
            ps=p.linhas['pendencias.csv']
            self.assertEqual(len(ps),2)
            self.assertNotEqual(ps[0]['id_saida'],ps[1]['id_saida'])
            self.assertTrue(all(l['ref_origem']=='FITID-LIVRE' and 'FITID repetido' in l['motivo'] for l in ps))
            self.assertEqual(p.cobertura['pendentes'],2)

    def test_duplicata_em_outro_mes_nao_e_escolhida_pelo_recorte(self):
        self.ofx([{},dict(DTPOSTED='20320502120000[-3:BRT]')])
        r,_=self.rodar('2032-04');p=r.partes['EXTRATO_MERIDIANO']
        self.assertEqual(p.situacao,'PROVISORIO')
        self.assertEqual(p.cobertura['pendentes'],1)
        self.assertEqual(r.fontes['meridiano']['fora_competencia'],1)

    def test_fitid_ausente_fica_em_diagnostico_fisico_sem_falso_classificado(self):
        self.ofx([dict(FITID=None)])
        r,_=self.rodar();p=r.partes['EXTRATO_MERIDIANO']
        self.assertEqual(p.linhas['lancamentos_classificados.csv'],[])
        x=p.linhas['pendencias.csv'][0]
        self.assertTrue(x['ref_origem'].startswith('L'))
        self.assertIn('somente para diagnóstico',x['motivo'])
        self.assertEqual(x['valor_brl'],'123.45')

    def test_campos_invalidos_preservam_valor_conhecido_sem_zero_inventado(self):
        self.ofx([dict(FITID='A',DTPOSTED='inválida'),dict(FITID='B',TRNAMT='NaN'),
                  dict(FITID='C',TRNAMT='0.001'),dict(FITID='D',TRNTYPE='DEBIT'),dict(FITID='E',MEMO=None)])
        r,_=self.rodar();p=r.partes['EXTRATO_MERIDIANO']
        self.assertEqual(p.situacao,'PROVISORIO')
        self.assertEqual([l['valor_brl'] for l in p.linhas['pendencias.csv']],['123.45','','','123.45','123.45'])
        self.assertEqual(len(p.rastro),3)

    def test_nome_como_descricao_e_precisao_monetaria_sem_float(self):
        self.ofx([dict(MEMO=None,NAME='PIX RECEB RECURSO LIVRE',TRNAMT='+0.01'),
                  dict(FITID='B',TRNAMT='1.2')])
        r,_=self.rodar()
        self.assertEqual([l['valor'] for l in r.partes['EXTRATO_MERIDIANO'].linhas['lancamentos_classificados.csv']],['0.01','1.20'])

    def test_historico_novo_e_sinal_inverso_sao_pendencias_sem_receita(self):
        self.ofx([dict(MEMO='PIX RECEB PAGADOR NOVO'),dict(FITID='B',TRNTYPE='DEBIT',TRNAMT='-12.34')])
        r,_=self.rodar();p=r.partes['EXTRATO_MERIDIANO']
        self.assertEqual(len(p.linhas['pendencias.csv']),2)
        self.assertEqual(p.linhas['lancamentos_classificados.csv'],[])

    def test_conta_sem_permissao_nao_e_usada(self):
        self.plano.write_text(self.plano.read_text(encoding='latin-1').replace('Recursos de clientes;ANALITICA;C;S','Recursos de clientes;ANALITICA;C;N'),encoding='latin-1')
        r,_=self.rodar();p=r.partes['EXTRATO_MERIDIANO']
        self.assertEqual(p.situacao,'PROVISORIO')
        self.assertEqual(p.linhas['pendencias.csv'][0]['tipo'],'CONTA_NAO_PERMITIDA')

    def test_mes_independente_e_escolha_explicita(self):
        self.ofx([{},dict(FITID='B',DTPOSTED='20320502120000[-3:BRT]')])
        r,_=self.rodar();self.assertEqual(r.partes['EXTRATO_MERIDIANO'].situacao,'BLOQUEADO')
        r,_=self.rodar('2032-05')
        self.assertEqual(r.partes['EXTRATO_MERIDIANO'].situacao,'COMPLETO')
        self.assertEqual(r.partes['CHECKOUT'].situacao,'BLOQUEADO')
        self.assertEqual(r.fontes['meridiano']['fora_competencia'],1)

    def test_ofx_truncado_erro_status_ou_moeda_invalida_bloqueiam_so_meridiano(self):
        raw=self.extrato.read_text(encoding='cp1252')
        for s in (raw.replace('</STMTTRN>','',1),raw.replace('<CODE>0','<CODE>999'),
                  raw.replace('<CURDEF>BRL','<CURDEF>USD'),raw.replace('</STMTRS>',''),raw.replace('</OFX>','')):
            self.extrato.write_text(s,encoding='cp1252')
            r,_=self.rodar()
            self.assertEqual(r.partes['EXTRATO_MERIDIANO'].situacao,'BLOQUEADO')
            self.assertEqual(r.partes['CHECKOUT'].situacao,'COMPLETO')

    def test_mais_de_um_ofx_nao_escolhe_pelo_nome(self):
        (self.dados/'outro.ofx').write_bytes(self.extrato.read_bytes())
        with self.assertRaisesRegex(ErroEntrada,'encontrados 2'):meridiano.descobrir(self.dados)

    def test_metadados_ou_regex_invalidos_nao_bloqueiam_minimo(self):
        for r in (dict(self.rs[0],padrao='['),dict(self.rs[0],aprovador='')):
            self.configurar([r]);resultado,_=self.rodar()
            self.assertEqual(resultado.partes['EXTRATO_MERIDIANO'].situacao,'BLOQUEADO')
            self.assertEqual(resultado.partes['CHECKOUT'].situacao,'COMPLETO')

    def test_sobreposicao_nao_escolhe_regra_pela_ordem(self):
        self.configurar(self.rs+[self.regra('CONFLITO',r'^pix receb','CREDITO','1.9')])
        r,_=self.rodar()
        self.assertIn('várias regras',r.partes['EXTRATO_MERIDIANO'].linhas['pendencias.csv'][0]['motivo'])

    def test_minimo_permanece_identico_sem_meridiano(self):
        self.rodar(escopo='checkout');antes={p.name:p.read_bytes() for p in self.saida.glob('*.csv')}
        self.extrato.unlink();r,_=self.rodar(escopo='checkout')
        self.assertEqual(antes,{p.name:p.read_bytes() for p in self.saida.glob('*.csv')})
        self.assertEqual(r.partes['EXTRATO_MERIDIANO'].situacao,'BLOQUEADO')

    def test_meridiano_sem_orbe_taxas_ponte_e_aurora(self):
        for p in list(self.dados.iterdir()):
            if p not in {self.plano,self.extrato} and p.suffix.lower() in {'.csv','.xlsx','.eml'}:p.unlink()
        r,_=self.rodar()
        self.assertEqual(r.partes['EXTRATO_MERIDIANO'].situacao,'COMPLETO')
        self.assertEqual(r.partes['CHECKOUT'].situacao,'BLOQUEADO')

    def test_adulteracao_coerente_bloqueia_so_meridiano(self):
        r=executar(self.dados,self.regras);p=r.partes['EXTRATO_MERIDIANO']
        p.linhas['lancamentos_classificados.csv'][0]['valor']='999.99';p.rastro[0]['valor']='999.99'
        m=publicar(r,self.saida,'alvo')
        self.assertEqual(m['partes']['EXTRATO_MERIDIANO']['situacao'],'BLOQUEADO')
        self.assertEqual(m['partes']['CHECKOUT']['situacao'],'COMPLETO')

    def test_falha_do_rastro_de_um_banco_preserva_o_outro(self):
        p=self.dados/'aurora_sintetico.csv'
        p.write_text('Data;Lançamento;Documento;Valor (R$);Saldo (R$)\n02/04/2032;TARIFA;;-1,23;0,00\n',encoding='utf-8')
        with self.regras.open('a',encoding='utf-8') as f:
            f.write('\n[[classificacao_aurora]]\n'+'\n'.join(f'{k} = {json.dumps(v)}' for k,v in self.rs[2].items())+'\n')
        for falha, outro in [('AURORA','MERIDIANO'),('MERIDIANO','AURORA')]:
            r=executar(self.dados,self.regras)
            self.assertEqual(r.partes['EXTRATO_'+outro].situacao,'COMPLETO')
            r.partes['EXTRATO_'+falha].rastro[0]['valor']='999.99'
            m=publicar(r,self.saida,'alvo')
            self.assertEqual(m['partes']['EXTRATO_'+falha]['situacao'],'BLOQUEADO')
            self.assertEqual(m['partes']['EXTRATO_'+outro]['situacao'],'COMPLETO')
            verificar(self.dados,self.saida,self.regras)

    def test_auditor_rejeita_troca_de_fitid_apos_publicacao_com_hash_novo(self):
        self.rodar();p=self.saida/'lancamentos_classificados.csv'
        with p.open(encoding='utf-8',newline='') as f:
            leitor=csv.DictReader(f,delimiter=';');colunas=leitor.fieldnames;ls=list(leitor)
        ls[0]['ref_origem']='OUTRA'
        with p.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=colunas,delimiter=';');w.writeheader();w.writerows(ls)
        pmanifesto=self.saida/'manifesto.json';m=json.loads(pmanifesto.read_text(encoding='utf-8'))
        m['arquivos'][p.name]=sha256(p.read_bytes()).hexdigest();pmanifesto.write_text(json.dumps(m),encoding='utf-8')
        with self.assertRaises(ErroAceite):verificar(self.dados,self.saida,self.regras)

    def test_determinismo_e_fontes_preservadas(self):
        antes={p.name:sha256(p.read_bytes()).hexdigest() for p in self.dados.iterdir() if p.is_file()}
        self.rodar();saidas={p.name:p.read_bytes() for p in self.saida.iterdir() if p.is_file()}
        self.rodar()
        self.assertEqual(saidas,{p.name:p.read_bytes() for p in self.saida.iterdir() if p.is_file()})
        self.assertEqual(antes,{p.name:sha256(p.read_bytes()).hexdigest() for p in self.dados.iterdir() if p.is_file()})

    def test_mapeamento_documentado_sem_usar_valores_datas_ou_fitids_do_exemplo(self):
        import tomllib
        config=tomllib.loads(Path('regras.toml').read_text(encoding='utf-8'))
        self.configurar(config['classificacao_meridiano'])
        codigos=sorted({r['conta_codigo'] for r in config['classificacao_meridiano']})
        self.plano.write_text('COD_CONTA;DESCRICAO;TIPO;NATUREZA;ACEITA_LANCTO;COD_SUPERIOR;DT_CRIACAO\n'+''.join(f'{c};Conta teste;ANALITICA;D;S;;01/01/2032\n' for c in codigos),encoding='latin-1')
        casos=[('PIX RECEB PONTE AEREA ESTUDANTIL L','CREDIT','2.1.02.001'),
            ('PIX RECEB CASA DO ESTUDANTE VIAGEN','CREDIT','2.1.02.001'),
            ('TED ENVIADA PONTE CAMBIO SA LIQ OPERACOES','DEBIT','2.1.02.001'),
            ('TED RECEB PONTE CAMBIO SA REPASSE COMISSAO 03/2032','CREDIT','1.1.03.002'),
            ('TED RECEBIDA TARVO PAGAMENTOS LTDA - MESMA TITULARIDADE','CREDIT','1.1.09.001'),
            ('APLICACAO AUTOMATICA CDB DI','DEBIT','1.1.02.001'),('RESGATE AUTOMATICO CDB DI','CREDIT','1.1.02.001'),
            ('RENDIMENTO APLIC AUTOMATICA','CREDIT','3.2.01'),('TARIFA MANUTENCAO CONTA PJ','DEBIT','4.2.01'),
            ('SEGURO EMPRESARIAL PARC 01/12','DEBIT','4.2.05'),('IOF S/ OPERACAO CREDITO','DEBIT','4.3.01')]
        self.ofx([dict(FITID=f'ID-{i}',MEMO=d,TRNTYPE=t,TRNAMT='1.23' if t=='CREDIT' else '-1.23') for i,(d,t,c) in enumerate(casos)])
        r,_=self.rodar()
        self.assertEqual([l['conta_codigo'] for l in r.partes['EXTRATO_MERIDIANO'].linhas['lancamentos_classificados.csv']],[c for d,t,c in casos])
