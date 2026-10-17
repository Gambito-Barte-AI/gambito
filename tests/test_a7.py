"""Aceite integrado com todos os formatos, sem dados oficiais como pré-requisito."""

from contextlib import redirect_stdout
from copy import deepcopy
import csv
from decimal import Decimal
from io import StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from auditoria_integrada import verificar as integridade_global
from cenarios_a7 import criar
from validar_saida import CONTRATO, ErroAceite, ler_csv, verificar
from tarvo.__main__ import main
from tarvo.execucao import executar
from tarvo.exportacao import publicar


class A7Test(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.raiz=Path(self.tmp.name);self.dados,self.regras=criar(self.raiz)
        self.saida=self.raiz/'saida'

    def rodar(self):
        r=executar(self.dados,self.regras);m=publicar(r,self.saida,'alvo')
        verificar(self.dados,self.saida,self.regras)
        return r,m

    def artefato(self):
        return ({n:ler_csv(self.saida/n,c) for n,c in CONTRATO.items()},
                json.loads((self.saida/'manifesto.json').read_text(encoding='utf-8')))

    def test_outubro_sintetico_todos_resultados_rn64_d10_e_cobertura(self):
        r,m=self.rodar()
        self.assertEqual(m['fechamento']['situacao'],'COMPLETO')
        self.assertEqual(r.competencia,'2032-10')
        self.assertEqual(r.partes['CHECKOUT'].cobertura,dict(linhas_lidas=7,calculadas=6,pendentes=1,bloqueadas=0))
        self.assertEqual([x['comissao_brl'] for x in r.partes['CHECKOUT'].linhas['comissoes_por_lojista.csv']],['10.00','-0.10'])
        devolucao=r.partes['DEVOLUCAO_CASA']
        self.assertEqual(devolucao.linhas['pendencias.csv'][0]['valor_brl'],'1.00')
        self.assertEqual({x['ref_origem'] for x in devolucao.rastro},{'VENDA-ISENTA','ESTORNO-ISENTO'})
        nota=r.partes['NOTAS_REMESSA'].linhas['notas_a_emitir.csv'][0]
        self.assertEqual(nota['valor_brl'],'4.00');self.assertIn('D-10',nota['discriminacao'])
        self.assertEqual(len(r.partes['EXTRATO_AURORA'].linhas['lancamentos_classificados.csv']),2)
        self.assertEqual(len(r.partes['EXTRATO_MERIDIANO'].linhas['lancamentos_classificados.csv']),2)

    def test_chegada_tardia_publica_novo_estado_sem_reusar_resultados_anteriores(self):
        tardio=self.dados/'chegada_tardia.csv';bruto=tardio.read_bytes();tardio.unlink()
        self.rodar();antes=(self.saida/'comissoes_por_lojista.csv').read_bytes()
        tardio.write_bytes(bruto);r,m=self.rodar()
        self.assertNotEqual(antes,(self.saida/'comissoes_por_lojista.csv').read_bytes())
        self.assertEqual(m['cobertura']['linhas_lidas'],7)
        self.assertEqual(r.partes['DEVOLUCAO_CASA'].linhas['pendencias.csv'][0]['valor_brl'],'1.00')

    def test_resumo_informa_metodo_por_banco_e_d10(self):
        buffer=StringIO()
        with redirect_stdout(buffer):
            codigo=main(['--dados',str(self.dados),'--regras',str(self.regras),'--saida',str(self.saida),'--escopo','alvo'])
        self.assertEqual(codigo,0)
        self.assertIn('CLASSIFICAÇÃO AURORA: 2 movimentos; REGRA=2',buffer.getvalue())
        self.assertIn('CLASSIFICAÇÃO MERIDIANO: 2 movimentos; REGRA=2',buffer.getvalue())
        self.assertIn('DECISÃO PENDENTE D-10',buffer.getvalue())

    def test_auditoria_global_rejeita_id_duplicado_entre_relatorios(self):
        self.rodar();arquivos,m=self.artefato()
        arquivos['pendencias.csv'][0]['id_saida']=arquivos['notas_a_emitir.csv'][0]['id_saida']
        with self.assertRaisesRegex(ErroAceite,'duplicado'):integridade_global(m,arquivos)

    def test_auditoria_global_rejeita_saida_e_rastro_sem_produtor_conhecido(self):
        self.rodar();arquivos,m=self.artefato()
        p=deepcopy(arquivos['pendencias.csv'][0]);p['id_saida']='SEM_PRODUTOR:EXTRA';p['valor_brl']='1.00'
        arquivos['pendencias.csv'].append(p)
        arquivos['rastro.csv'].append(dict(id_saida=p['id_saida'],arquivo_origem='fonte.csv',ref_origem='A',valor='1.00'))
        with self.assertRaisesRegex(ErroAceite,'produtor'):integridade_global(m,arquivos)

    def test_auditoria_global_rejeita_rastro_orfao_ou_duplicado(self):
        self.rodar();arquivos,m=self.artefato()
        for duplicar in (False,True):
            a=deepcopy(arquivos);r=deepcopy(a['rastro.csv'][0])
            if not duplicar:r['id_saida']='SEM_DESTINO'
            a['rastro.csv'].append(r)
            with self.assertRaises(ErroAceite):integridade_global(m,a)

    def test_auditoria_global_confere_dominios_datas_e_precisao(self):
        self.rodar();arquivos,m=self.artefato()
        for campo,valor in [('data','2032-10-99'),('data','02/10/2032'),('valor','1,23'),('confianca','1.01'),('metodo','INFERIDO')]:
            a=deepcopy(arquivos);a['lancamentos_classificados.csv'][0][campo]=valor
            with self.assertRaises(ValueError):integridade_global(m,a)

    def test_fonte_perdida_remove_resultados_antigos_sem_apagar_os_independentes(self):
        self.rodar();(self.dados/'mensagem_nova.eml').unlink();r,m=self.rodar()
        self.assertEqual(m['fechamento']['situacao'],'PROVISORIO')
        self.assertEqual(r.partes['NOTAS_REMESSA'].situacao,'BLOQUEADO')
        arquivos,_=self.artefato()
        self.assertFalse(any(l['linha_negocio']=='REMESSA' for l in arquivos['notas_a_emitir.csv']))
        self.assertEqual(len(arquivos['lancamentos_classificados.csv']),4)

    def test_evento_nao_suportado_deixa_parcial_sem_estimar_taxa(self):
        with (self.dados/'primeira_origem.csv').open('a',encoding='utf-8',newline='') as f:
            csv.writer(f,delimiter=';').writerow(['TREZE-X','04/10/2032','900','VENDA','CREDITO PARCELADO','13','1,00','','','2','0,02'])
        r,m=self.rodar()
        self.assertEqual(r.partes['CHECKOUT'].situacao,'PROVISORIO')
        self.assertEqual(r.partes['EXTRATO_AURORA'].situacao,'COMPLETO')
        self.assertEqual(m['fechamento']['situacao'],'PROVISORIO')
        self.assertTrue(any(p.origem.ref=='TREZE-X' for p in r.pendencias))

    def test_falha_de_rastro_integrada_preserva_partes_independentes(self):
        dependentes={'CHECKOUT':{'NOTAS_CHECKOUT'},'REMESSAS':{'NOTAS_REMESSA'}}
        for nome in ('CHECKOUT','DIVERGENCIAS_CHECKOUT','DEVOLUCAO_CASA','REMESSAS',
                     'NOTAS_CHECKOUT','NOTAS_REMESSA','EXTRATO_AURORA','EXTRATO_MERIDIANO'):
            with self.subTest(parte=nome):
                r=executar(self.dados,self.regras);p=r.partes[nome]
                p.rastro[0]['valor']=format(Decimal(p.rastro[0]['valor'])+Decimal('0.01'),'.2f')
                m=publicar(r,self.saida,'alvo')
                bloqueadas={n for n,p in m['partes'].items() if p['situacao']=='BLOQUEADO'}
                self.assertEqual(bloqueadas,{nome}|dependentes.get(nome,set()))
                verificar(self.dados,self.saida,self.regras)

    def test_bloqueio_transitorio_windows_na_publicacao_mantem_artefato_valido(self):
        original=os.replace;tentativas=[]
        def substituir(src,dst):
            if Path(src).name=='manifesto.json':
                tentativas.append(1)
                if len(tentativas)==1:
                    erro=PermissionError('Bloqueio sintético de arquivo');erro.winerror=5;raise erro
            original(src,dst)
        with patch('tarvo.exportacao.os',SimpleNamespace(name='nt',replace=substituir)),patch('tarvo.exportacao.time.sleep') as pausa:
            self.rodar()
        self.assertEqual(len(tentativas),2);pausa.assert_called_once_with(0.05)

    def test_bloqueio_persistente_windows_nao_libera_publicacao(self):
        original=os.replace;tentativas=[]
        def substituir(src,dst):
            if Path(src).name=='manifesto.json':
                tentativas.append(1);erro=PermissionError('Bloqueio sintético persistente');erro.winerror=5;raise erro
            original(src,dst)
        with patch('tarvo.exportacao.os',SimpleNamespace(name='nt',replace=substituir)),patch('tarvo.exportacao.time.sleep') as pausa:
            with self.assertRaises(PermissionError):self.rodar()
        self.assertEqual(len(tentativas),4);self.assertEqual(pausa.call_count,3)
        m=json.loads((self.saida/'manifesto.json').read_text(encoding='utf-8'))
        self.assertFalse(m['publicacao_concluida']);self.assertEqual(m['situacao_comando'],'BLOQUEADO')
        self.assertFalse(verificar(self.dados,self.saida,self.regras)['publicacao_concluida'])

    def test_erro_nao_transitorio_nao_e_repetido(self):
        from tarvo.exportacao import _substituir
        with patch('tarvo.exportacao.os.replace',side_effect=OSError('Falha sintética')),patch('tarvo.exportacao.time.sleep') as pausa:
            with self.assertRaises(OSError):_substituir('origem','destino')
        pausa.assert_not_called()
