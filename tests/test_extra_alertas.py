"""E3: decisões aprovadas de fim de dia, isoladas dos valores financeiros."""

from copy import deepcopy
from dataclasses import replace
from datetime import date
from decimal import Decimal
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cenarios_a7 import criar
from tarvo.modelos import Evento, Origem, ErroEntrada
from tarvo.extras import alertas
from tarvo.execucao import executar
from tarvo.exportacao import publicar
from tarvo.validacao import validar_parte
from validar_saida import verificar, ErroAceite


def config():
    return dict(habilitado=True,id="REGRA_SINTETICA",metodo="SALDO_FIM_DIA",sem_valor_minimo=True,
        elegibilidade="CONTRATOS_BLOQUEADOS",reversao_fora_periodo="LISTAR_SEM_ABATER",
        exposicao_anterior="DESCONHECIDA",fonte="Fixture E3",aprovacao="Somente teste",
        aprovador="Teste",aprovado_em="2033-01-01",natureza="DECISAO_TIME")


def evento(ref="A",dia=1,valor="100.00",original="",dia_original=1,ec="901"):
    return Evento(Origem("qualquer.csv",ref,dia+1),date(2033,1,dia),ec,
        "REVERSAO ANTECIPACAO" if original else "ANTECIPACAO","",None,Decimal(valor),original,
        date(2033,1,dia_original) if original else None)


def elegiveis(ec="901",cnpj="11111111000111"):
    return {ec:dict(cnpj=cnpj,bloqueio=dict(id="BLOQUEIO_TESTE",cnpj=cnpj,fonte="Fixture E3",
        aprovacao="Somente teste",aprovador="Teste",aprovado_em="2033-01-01"))}


class AlertasTest(unittest.TestCase):
    def analisar(self,es,els=None,cfg=None):
        return alertas.analisar_antecipacoes(es,elegiveis() if els is None else els,config() if cfg is None else cfg)

    def test_pico_acumulado_diario_e_reversoes_posteriores(self):
        es=[evento("A",1,"100.00"),evento("B",1,"50.00"),evento("R",2,"-100.00","A"),evento("C",3,"130.00")]
        p=self.analisar(es);r=p['registros'][0]
        self.assertEqual((r['pico_brl'],r['data_pico'],r['total_antecipado_brl'],r['saldo_final_brl']),
                         ('180.00','2033-01-03','280.00','180.00'))
        self.assertIn('R em 2033-01-02: -100.00',r['texto'])
        self.assertEqual(sum(Decimal(c['valor_brl']) for c in r['contribuicoes_pico']),Decimal('180.00'))

    def test_mesmo_dia_independe_da_ordem_e_alerta_zero(self):
        es=[evento(),evento('R',1,'-100.00','A')]
        p=self.analisar(es);self.assertEqual(p,self.analisar(es[::-1]))
        self.assertEqual(p['registros'][0]['pico_brl'],'0.00')
        parte=alertas.calcular_parte(dict(eventos=es,elegiveis=elegiveis(),config=config()))
        validar_parte(parte)
        self.assertEqual(len(parte.rastro),2)

    def test_pico_nao_e_apagado_por_reversao_no_dia_seguinte(self):
        r=self.analisar([evento(),evento('R',2,'-100.00','A')])['registros'][0]
        self.assertEqual((r['pico_brl'],r['saldo_final_brl']),('100.00','0.00'))
        self.assertEqual(len(r['contribuicoes_pico']),1)

    def test_sem_limiar_alerta_um_centavo(self):
        self.assertEqual(self.analisar([evento(valor='0.01')])['registros'][0]['pico_brl'],'0.01')

    def test_nao_deduz_sem_historico_ou_sem_contrato_de_dados_ausentes(self):
        self.assertEqual(self.analisar([evento()],{})['registros'],[])
        p=self.analisar([evento()],{'901':dict(erro='Identidade não resolvida')})
        self.assertEqual(p['situacao'],'PARCIAL');self.assertEqual(p['registros'],[])

    def test_reversao_sem_original_listada_sem_abater(self):
        e=replace(evento('R',2,'-300.00','FORA'),data_original=date(2032,12,30))
        r=self.analisar([evento(),e])['registros'][0]
        self.assertEqual((r['pico_brl'],r['saldo_final_brl']),('100.00','100.00'))
        self.assertIn('não abatida',r['texto']);self.assertIn('anterior ao período desconhecida',r['texto'])

    def test_reversao_sozinha_nao_gera_alerta(self):
        self.assertEqual(self.analisar([evento('R',2,'-100.00','FORA')])['registros'],[])

    def test_duplicidade_ou_vinculo_invalido_nao_gera_numero(self):
        casos=[[evento(),evento()], [evento(),evento('R',2,'-90.00','A')],
               [evento(),evento('R',2,'-100.00','A'),evento('S',3,'-100.00','A')],
               [evento(valor='-1.00')]]
        for es in casos:
            with self.subTest(es=es):
                p=self.analisar(es);self.assertEqual(p['registros'],[]);self.assertTrue(p['motivos'])

    def test_cnpjs_distintos_e_dois_ecs_mesmo_cnpj(self):
        els=elegiveis();els.update(elegiveis('902'))
        self.assertEqual(len(self.analisar([evento(),evento('B',ec='902')],els)['registros']),1)
        els.update(elegiveis('902','22222222000122'))
        self.assertEqual(len(self.analisar([evento(),evento('B',ec='902')],els)['registros']),2)

    def test_empate_pico_fica_primeira_data(self):
        es=[evento(),evento('R',2,'-100.00','A'),evento('B',3,'100.00')]
        self.assertEqual(self.analisar(es)['registros'][0]['data_pico'],'2033-01-01')

    def test_criterio_ou_evidencia_ausente_bloqueia_sem_inventar(self):
        for cfg in ({},dict(config(),limiar_brl='1000.00'),dict(config(),metodo='MAXIMO_INDIVIDUAL')):
            self.assertEqual(self.analisar([evento()],cfg=cfg)['situacao'],'BLOQUEADO')
        els=elegiveis();els['901']['bloqueio']['cnpj']='22222222000122'
        self.assertEqual(self.analisar([evento()],els)['situacao'],'BLOQUEADO')

    def test_sem_mutacao_e_determinismo_json(self):
        es=[evento()];els=elegiveis();cfg=config();antes=deepcopy((es,els,cfg))
        p=self.analisar(es,els,cfg)
        self.assertEqual((es,els,cfg),antes);self.assertEqual(json.loads(json.dumps(p)),p)

    def test_assinatura_e0_por_palavra_chave(self):
        p=alertas.analisar_antecipacoes(eventos=[evento()],elegibilidade=elegiveis(),config=config())
        self.assertEqual(p['situacao'],'COMPLETO')

    def test_continuidade_legada_permanece_legivel_sem_tratar_d10_como_pendente_atual(self):
        from test_extra_continuidade import resultado, resselar
        from tarvo.extras.continuidade import exportar_pendencias, ler_pendencias
        p=exportar_pendencias(resultado(),{})
        self.assertIn('D-10 confirmada',p['limitacoes_financeiras'][1])
        p['limitacoes_financeiras'][1]='D-10: natureza do ajuste da Ponte permanece pendente de confirmação financeira; nenhuma regra alterada.'
        self.assertEqual(ler_pendencias(resselar(p)),p) # Texto histórico, não nova decisão.

    def test_rastro_adulterado_bloqueia_parte(self):
        ctx=dict(eventos=[evento()],elegiveis=elegiveis(),config=config())
        p=alertas.calcular_parte(ctx);p.rastro[0]['valor']='99.00'
        with self.assertRaises(ErroEntrada):alertas.validar(p,ctx)


class IntegracaoAlertasTest(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.raiz=Path(self.tmp.name);self.dados,self.regras=criar(self.raiz)
        cfg=config()
        with self.regras.open('a',encoding='utf-8') as f:
            f.write('\n[extras.alertas]\n')
            for k,v in cfg.items():f.write(k+' = '+json.dumps(v,ensure_ascii=False)+'\n')
        with (self.dados/'primeira_origem.csv').open('a',encoding='utf-8',newline='') as f:
            csv.writer(f,delimiter=';').writerow(['ADIANT-NOVO','04/10/2032','902','ANTECIPACAO','','','50,00','','04/10/2032','2,1','1,05'])

    def rodar(self,nome='saida',escopo='alvo'):
        r=executar(self.dados,self.regras);p=self.raiz/nome;m=publicar(r,p,escopo)
        verificar(self.dados,p,self.regras)
        return r,m,p

    def test_pipeline_e_auditor_outro_mes_sem_constantes(self):
        r,m,p=self.rodar()
        a=r.partes[alertas.NOME].linhas['pendencias.csv'][0]
        self.assertEqual(a['valor_brl'],'50.00');self.assertIn('2032-10-04',a['motivo'])
        self.assertEqual(m['versao'],9);self.assertEqual(m['situacao_comando'],'COMPLETO')
        import tomllib
        self.assertEqual(m['decisoes_financeiras_pendentes'],
            tomllib.loads(self.regras.read_text(encoding='utf-8')).get('decisoes_pendentes',[]))

    def test_minimo_nao_publica_alertas(self):
        r,m,p=self.rodar(escopo='checkout')
        self.assertNotIn('ALERTA_ANTECIPACAO:',(p/'pendencias.csv').read_text(encoding='utf-8'))

    def test_sem_taxas_nao_inventa_elegibilidade(self):
        for p in self.dados.glob('*.xlsx'):p.unlink()
        r,m,p=self.rodar()
        self.assertEqual(m['partes'][alertas.NOME]['situacao'],'BLOQUEADO')
        self.assertTrue(m['partes']['EXTRATO_MERIDIANO']['rastro_validado'])

    def test_fonte_ponte_ausente_preserva_alerta(self):
        for p in self.dados.glob('*.eml'):p.unlink()
        r,m,p=self.rodar()
        self.assertTrue(m['partes'][alertas.NOME]['rastro_validado'])

    def test_criterio_sem_aprovador_bloqueia_apenas_alerta(self):
        inicio,criterio=self.regras.read_text(encoding='utf-8').split('[extras.alertas]',1)
        self.regras.write_text(inicio+'[extras.alertas]'+criterio.replace('aprovador =','aprovador_omitido =',1),encoding='utf-8')
        r,m,p=self.rodar()
        self.assertEqual(m['partes'][alertas.NOME]['situacao'],'BLOQUEADO')
        self.assertTrue(m['partes']['CHECKOUT']['rastro_validado'])

    def test_alerta_adulterado_rejeitado_por_auditor_independente(self):
        r,m,p=self.rodar()
        from auditoria_e3 import verificar as auditar
        from validar_saida import ler_csv,CONTRATO
        import tomllib
        arquivos={n:ler_csv(p/n,c) for n,c in CONTRATO.items()}
        alvo=next(x for x in arquivos['pendencias.csv'] if x['tipo']=='ALERTA_ANTECIPACAO')
        alvo['valor_brl']='49.00'
        with self.assertRaises(ErroAceite):auditar(m,arquivos,tomllib.loads(self.regras.read_text(encoding='utf-8')),self.dados)


class RegressaoPacoteAlertasTest(unittest.TestCase):
    @unittest.skipUnless((Path(__file__).resolve().parents[1]/'Tarvo_Data_Pack_set2026').is_dir(), 'Pack oficial local não disponível')
    def test_atlas_setembro_regressao_valores_confirmados_sem_constantes_no_motor(self):
        raiz=Path(__file__).resolve().parents[1]
        r=executar(raiz/'Tarvo_Data_Pack_set2026',raiz/'regras.toml')
        p=r.partes[alertas.NOME];self.assertTrue(p.validado)
        self.assertEqual(len(p.linhas['pendencias.csv']),1)
        a=p.linhas['pendencias.csv'][0]
        self.assertEqual(a['cnpj'],'39566044000119');self.assertEqual(a['valor_brl'],'183581.24')
        for texto in ('2026-09-24','235943.10','127230.96','AN88446030','AN88446660'):
            self.assertIn(texto,a['motivo'])
        self.assertEqual(len(p.rastro),6)
        self.assertEqual(sum(Decimal(x['valor']) for x in p.rastro),Decimal('183581.24'))
        self.assertNotIn('D-10',{d['id'] for d in r.decisoes_pendentes})


if __name__=='__main__':unittest.main()
