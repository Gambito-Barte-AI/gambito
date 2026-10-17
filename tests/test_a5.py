"""A5: fontes sintéticas, classificação conservadora e isolamento das entregas."""

import csv
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import unittest

import test_aceite as amostras
from validar_saida import ErroAceite, verificar
from tarvo.execucao import executar
from tarvo.exportacao import publicar
from tarvo.leitores import aurora, plano_contas
from tarvo.modelos import ErroEntrada


class A5Test(unittest.TestCase):
    setUpBase = amostras.AceiteTest.setUp
    vendas = amostras.AceiteTest.vendas

    def setUp(self):
        self.setUpBase()
        self.plano = self.dados / "catalogo_sem_nome_fixo.csv"
        self.extrato = self.dados / "movimentos_nome_livre.csv"
        self.plano.write_text('COD_CONTA;DESCRICAO;TIPO;NATUREZA;ACEITA_LANCTO;COD_SUPERIOR;DT_CRIACAO\n'
            '1;Sintética;SINTETICA;D;N;;01/01/2032\n'
            '1.7;Créditos a identificar;ANALITICA;D;S;1;01/01/2032\n'
            '2.8;Obrigação trabalhista;ANALITICA;C;S;;01/01/2032\n'
            '4.9;Despesa de serviços;ANALITICA;D;S;;01/01/2032\n', encoding="latin-1")
        self.regras_banco = [self.regra("SALARIOS", r"^salarios\b", "DEBITO", "2.8"),
            self.regra("SERVICOS", r"^servico\b", "DEBITO", "4.9"),
            dict(self.regra("SEM_IDENTIFICACAO", r"^credito sem identificacao\b", "CREDITO", "1.7"),
                 pendencia_tipo="CREDITO_NAO_IDENTIFICADO", motivo="Pagador desconhecido, sem receita.",
                 proximo_passo="Identificar origem com o financeiro.", quem_decide="Financeiro")]
        self.base_regras = self.regras.read_text(encoding="utf-8")
        self.configurar(self.regras_banco)
        self.movimentos([("02/04/2032", "SALÁRIOS mês anterior", "", "-1.234,56", "-1.234,56"),
                         ("03/04/2032", "CRÉDITO SEM IDENTIFICAÇÃO", "", "123,45", "-1.111,11")])

    def regra(self, id, padrao, sinal, conta):
        return dict(id=id, padrao=padrao, sinal=sinal, conta_codigo=conta, fonte="Fonte sintética",
            aprovacao="Regra para teste", aprovador="Teste", aprovado_em="NAO_INFORMADO", natureza="INTERPRETACAO_TECNICA")

    def configurar(self, regras):
        texto = self.base_regras
        for r in regras:
            texto += '\n[[classificacao_aurora]]\n' + '\n'.join(f'{k} = {json.dumps(v, ensure_ascii=False)}' for k,v in r.items()) + '\n'
        self.regras.write_text(texto, encoding="utf-8")

    def movimentos(self, linhas, preambulo=6, encoding="utf-8", saldo=True):
        with self.extrato.open("w", encoding=encoding, newline="") as f:
            w = csv.writer(f, delimiter=";", lineterminator="\n")
            for _ in range(preambulo):
                w.writerow(["Banco Aurora S.A.", "", "", "", ""])
            w.writerow(["Data", "Lançamento", "Documento", "Valor (R$)", "Saldo (R$)"])
            if saldo:
                w.writerow(["31/03/2032", "SALDO ANTERIOR", "", "", "0,00"])
            w.writerows(linhas)
            w.writerow(["", "SALDO FINAL", "", "", "-1.111,11"])
            w.writerow(["", "Os lançamentos estão sujeitos a confirmação.", "", "", ""])

    def rodar(self, competencia=None, escopo="alvo"):
        r = executar(self.dados, self.regras, competencia)
        m = publicar(r, self.saida, escopo)
        verificar(self.dados, self.saida, self.regras)
        return r, m

    def test_fluxo_completo_l9_sinais_passivo_pendencia_e_rastro(self):
        r, m = self.rodar()
        p = r.partes["EXTRATO_AURORA"]
        self.assertTrue(p.validado)
        self.assertEqual(p.situacao, "COMPLETO")
        self.assertEqual(p.cobertura, dict(linhas_lidas=2, calculadas=2, pendentes=0, bloqueadas=0))
        linhas = p.linhas["lancamentos_classificados.csv"]
        self.assertEqual((linhas[0]["ref_origem"], linhas[0]["data"], linhas[0]["valor"], linhas[0]["conta_codigo"]), ("L9", "2032-04-02", "-1234.56", "2.8"))
        self.assertTrue(all(l["metodo"] == "REGRA" and l["confianca"] == "1" for l in linhas))
        self.assertEqual(len(p.linhas["pendencias.csv"]), 1)
        self.assertEqual(len(p.rastro), 3)
        self.assertEqual(m["fontes"]["plano_contas"]["contas_lidas"], 4)
        self.assertTrue(m["partes"]["EXTRATO_MERIDIANO"]["implementado"])
        self.assertEqual(m["partes"]["EXTRATO_MERIDIANO"]["situacao"], "BLOQUEADO")

    def test_referencia_muda_com_preambulo_sem_constante_l9(self):
        self.movimentos([("02/04/2032", "SALARIOS", "", "-0,01", "0,00")], preambulo=2, encoding="cp1252")
        r, _ = self.rodar()
        self.assertEqual(r.partes["EXTRATO_AURORA"].linhas["lancamentos_classificados.csv"][0]["ref_origem"], "L5")

    def test_descricao_multilinha_preserva_inicio_fisico_e_proxima_referencia(self):
        self.movimentos([("02/04/2032", "SERVICO\ncom complemento", "", "-1,00", "0,00"),
                         ("02/04/2032", "SALARIOS", "", "-2,00", "0,00")])
        r, _ = self.rodar()
        ls = r.partes["EXTRATO_AURORA"].linhas["lancamentos_classificados.csv"]
        self.assertEqual([l["ref_origem"] for l in ls], ["L9", "L11"])
        self.assertEqual(ls[0]["descricao"], "SERVICO\ncom complemento")

    def test_historico_desconhecido_sinal_oposto_e_zero_nao_viram_receita(self):
        self.movimentos([("02/04/2032", "DESCONHECIDO", "", "7,35", "0,00"),
                         ("02/04/2032", "SALARIOS", "", "1,00", "0,00"),
                         ("02/04/2032", "SERVICO", "", "0,00", "0,00")])
        r, _ = self.rodar()
        p = r.partes["EXTRATO_AURORA"]
        self.assertEqual(p.linhas["lancamentos_classificados.csv"], [])
        self.assertEqual(len(p.linhas["pendencias.csv"]), 3)
        self.assertEqual(p.cobertura["pendentes"], 3)
        self.assertEqual([x["valor"] for x in p.rastro], ["7.35", "1.00", "0.00"])

    def test_regras_sobrepostas_nao_escolhem_por_ordem(self):
        self.configurar(self.regras_banco + [self.regra("OUTRA", r"^salarios", "DEBITO", "4.9")])
        r, _ = self.rodar()
        p = r.partes["EXTRATO_AURORA"]
        self.assertEqual(len(p.linhas["lancamentos_classificados.csv"]), 1)
        self.assertTrue(any("várias regras" in x["motivo"] for x in p.linhas["pendencias.csv"]))

    def test_conta_ausente_sintetica_ou_sem_permissao_nao_classifica(self):
        original = self.plano.read_text(encoding="latin-1")
        for mudar in (lambda s:s.replace('2.8;', '2.99;'), lambda s:s.replace('Obrigação trabalhista;ANALITICA', 'Obrigação trabalhista;SINTETICA'),
                       lambda s:s.replace('Obrigação trabalhista;ANALITICA;C;S', 'Obrigação trabalhista;ANALITICA;C;N')):
            self.plano.write_text(mudar(original), encoding="latin-1")
            r, _ = self.rodar()
            p = r.partes["EXTRATO_AURORA"]
            self.assertEqual(p.situacao, "PROVISORIO")
            self.assertTrue(any(x["tipo"] == "CONTA_NAO_PERMITIDA" for x in p.linhas["pendencias.csv"]))

    def test_linha_invalida_preserva_conhecido_sem_criar_zero(self):
        self.movimentos([("inválida", "SALARIOS", "", "-12,34", "0,00"),
                         ("02/04/2032", "SERVICO", "", "???", "0,00"),
                         ("02/04/2032", "SALARIOS", "", "-1,00", "0,00", "extra")])
        r, _ = self.rodar()
        p = r.partes["EXTRATO_AURORA"]
        self.assertEqual(p.situacao, "PROVISORIO")
        self.assertEqual([v["valor_brl"] for v in p.linhas["pendencias.csv"]], ["-12.34", "", "-1.00"])
        self.assertEqual(len(p.rastro), 2)

    def test_rodape_desconhecido_nao_e_descartado(self):
        with self.extrato.open("a", encoding="utf-8") as f:
            f.write(';TEXTO NOVO;;;\n')
        r, _ = self.rodar()
        self.assertEqual(r.partes["EXTRATO_AURORA"].situacao, "PROVISORIO")
        self.assertEqual(r.partes["EXTRATO_AURORA"].cobertura["linhas_lidas"], 3)

    def test_multiplos_meses_exigem_escolha_e_usa_data_do_banco(self):
        self.movimentos([("02/04/2032", "SALARIOS", "", "-1,00", "0,00"),
                         ("02/05/2032", "SALARIOS", "", "-2,00", "0,00")])
        r, _ = self.rodar()
        self.assertEqual(r.partes["EXTRATO_AURORA"].situacao, "BLOQUEADO")
        r, _ = self.rodar("2032-05")
        ls = r.partes["EXTRATO_AURORA"].linhas["lancamentos_classificados.csv"]
        self.assertEqual([l["valor"] for l in ls], ["-2.00"])
        self.assertEqual(r.partes['CHECKOUT'].situacao, 'BLOQUEADO')  # Orbe sem movimentos no recorte
        self.assertEqual(r.partes['EXTRATO_AURORA'].situacao, 'COMPLETO')
        self.assertEqual(r.fontes["aurora"]["fora_competencia"], 1)

    def test_outro_mes_independente_da_competencia_checkout(self):
        self.movimentos([("02/01/2040", "SALARIOS", "", "-8,76", "0,00")])
        r, _ = self.rodar()
        self.assertEqual(r.competencia, "2032-04")
        self.assertEqual(r.fontes["aurora"]["competencia"], "2040-01")

    def test_ausencia_extrato_ou_plano_preserva_seis_csvs_minimo(self):
        self.rodar(escopo="checkout")
        antes = {p.name:p.read_bytes() for p in self.saida.glob('*.csv')}
        for p in (self.extrato, self.plano):
            dados = p.read_bytes(); p.unlink()
            r, _ = self.rodar(escopo="checkout")
            self.assertEqual(r.partes["EXTRATO_AURORA"].situacao, "BLOQUEADO")
            self.assertEqual(antes, {p.name:p.read_bytes() for p in self.saida.glob('*.csv')})
            p.write_bytes(dados)

    def test_ausencia_orbe_taxas_nao_bloqueia_aurora(self):
        for p in list(self.dados.iterdir()):
            if p not in {self.extrato, self.plano} and p.suffix.lower() in {'.xlsx', '.csv'}:
                p.unlink()
        r, _ = self.rodar()
        self.assertEqual(r.partes["CHECKOUT"].situacao, "BLOQUEADO")
        self.assertEqual(r.partes["EXTRATO_AURORA"].situacao, "COMPLETO")

    def test_plano_duplicado_ou_layout_invalido_bloqueiam_so_aurora(self):
        with self.plano.open('a',encoding='latin-1') as f:
            f.write('2.8;Duplicada;ANALITICA;C;S;;01/01/2032\n')
        r, _ = self.rodar()
        self.assertEqual(r.partes["EXTRATO_AURORA"].situacao, "BLOQUEADO")
        self.assertEqual(r.partes["CHECKOUT"].situacao, "COMPLETO")
        self.extrato.write_text('Banco Aurora\nLayout alterado\n',encoding='utf-8')
        with self.assertRaisesRegex(ErroEntrada,'cabeçalho'):
            aurora.ler(self.extrato)

    def test_multiplos_candidatos_nao_escolhem_arquivo_por_nome(self):
        copia = self.dados/'outro_banco.csv'; copia.write_bytes(self.extrato.read_bytes())
        with self.assertRaisesRegex(ErroEntrada, 'encontrados 2'):
            aurora.descobrir(self.dados)
        copia.unlink(); copia.write_bytes(self.plano.read_bytes())
        with self.assertRaisesRegex(ErroEntrada, 'encontrados 2'):
            plano_contas.descobrir(self.dados)

    def test_configuracao_invalida_isolada(self):
        self.configurar([dict(self.regras_banco[0], padrao='[')])
        r, _ = self.rodar()
        self.assertEqual(r.partes["EXTRATO_AURORA"].situacao, "BLOQUEADO")
        self.assertEqual(r.partes["CHECKOUT"].situacao, "COMPLETO")

    def test_metadados_obrigatorios_sem_inventar_aprovacao(self):
        for campo in ('fonte', 'aprovador', 'aprovacao', 'aprovado_em', 'natureza'):
            with self.subTest(campo=campo):
                regra = dict(self.regras_banco[0]); regra.pop(campo)
                self.configurar([regra])
                r, _ = self.rodar()
                self.assertEqual(r.partes['EXTRATO_AURORA'].situacao, 'BLOQUEADO')
                self.assertEqual(r.partes['CHECKOUT'].situacao, 'COMPLETO')

    def test_padrao_oficial_nao_presume_lojista_ou_conta_propria_desconhecida(self):
        import tomllib
        config = tomllib.loads(Path('regras.toml').read_text(encoding='utf-8'))
        self.configurar(config['classificacao_aurora'])
        self.movimentos([('02/04/2032', 'PIX ENVIADO DESTINATARIO DESCONHECIDO', '', '-1,00', '0,00'),
            ('02/04/2032', 'DEVOLUCAO PIX - DESTINATARIO DESCONHECIDO', '', '1,00', '0,00'),
            ('02/04/2032', 'TRANSF ENTRE CONTAS P/ BCO MERIDIANO AG 9999 CC 12345-0', '', '-1,00', '0,00')])
        r, _ = self.rodar()
        p = r.partes['EXTRATO_AURORA']
        self.assertEqual(p.linhas['lancamentos_classificados.csv'], [])
        self.assertEqual([l['tipo'] for l in p.linhas['pendencias.csv']], ['CLASSIFICACAO_NAO_RESOLVIDA'] * 3)

    def test_adulteracao_coerente_de_valor_ou_conta_bloqueia_so_aurora(self):
        for campo, valor in [('valor','-999.99'),('conta_codigo','1.7'),('data','2032-04-20')]:
            r = executar(self.dados,self.regras)
            p = r.partes['EXTRATO_AURORA']; l=p.linhas['lancamentos_classificados.csv'][0]
            l[campo] = valor
            if campo=='valor': p.rastro[0]['valor']=valor
            m=publicar(r,self.saida,'alvo')
            self.assertEqual(m['partes']['EXTRATO_AURORA']['situacao'],'BLOQUEADO')
            self.assertEqual(m['partes']['CHECKOUT']['situacao'],'COMPLETO')

    def test_auditor_rejeita_conta_adulterada_mesmo_com_hash_atualizado(self):
        self.rodar()
        p=self.saida/'lancamentos_classificados.csv'
        with p.open(encoding='utf-8',newline='') as f:
            leitor=csv.DictReader(f,delimiter=';'); campos=leitor.fieldnames; ls=list(leitor)
        ls[0]['conta_codigo']='1.7'
        with p.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=campos,delimiter=';'); w.writeheader(); w.writerows(ls)
        path=self.saida/'manifesto.json'; m=json.loads(path.read_text(encoding='utf-8'))
        m['arquivos'][p.name]=sha256(p.read_bytes()).hexdigest(); path.write_text(json.dumps(m),encoding='utf-8')
        with self.assertRaises(ErroAceite): verificar(self.dados,self.saida,self.regras)

    def test_determinismo_e_preservacao_das_fontes(self):
        antes={p.name:sha256(p.read_bytes()).hexdigest() for p in self.dados.iterdir() if p.is_file()}
        self.rodar(); outputs={p.name:p.read_bytes() for p in self.saida.iterdir() if p.is_file()}
        self.rodar()
        self.assertEqual(outputs,{p.name:p.read_bytes() for p in self.saida.iterdir() if p.is_file()})
        self.assertEqual(antes,{p.name:sha256(p.read_bytes()).hexdigest() for p in self.dados.iterdir() if p.is_file()})

    def test_mapeamentos_documentados_usam_valores_livres_e_contas_analiticas(self):
        import tomllib
        config=tomllib.loads(Path('regras.toml').read_text(encoding='utf-8'))
        self.configurar(config['classificacao_aurora'])
        codigos=sorted({r['conta_codigo'] for r in config['classificacao_aurora']})
        self.plano.write_text('COD_CONTA;DESCRICAO;TIPO;NATUREZA;ACEITA_LANCTO;COD_SUPERIOR;DT_CRIACAO\n'+
            ''.join(f'{c};Conta de teste;ANALITICA;D;S;;01/01/2032\n' for c in codigos),encoding='latin-1')
        casos=[('TED RECEBIDA 12.345.678/0001-00 ORBE ADQUIRENCIA SA','1.1.03.001','1,23'),
            ('PAGTO SALARIOS - FOLHA 03/2032','2.1.04.001','-1,23'),('GPS INSS 03/2032','2.1.04.002','-1,23'),
            ('GRF FGTS 03/2032','2.1.04.003','-1,23'),('PAGTO ISS TESTE','2.1.03.003','-1,23'),
            ('DEBITO DARF 0561 IRRF','2.1.03.004','-1,23'),('DEBITO DARF 8109 PIS','2.1.03.001','-1,23'),
            ('DEBITO DARF 2172 COFINS','2.1.03.002','-1,23'),('TAR PACOTE SERVICOS PJ','4.2.01','-1,23'),
            ('BOLETO CONDOMINIO NOVO','4.2.02','-1,23'),('DEB AUT AMAZON WEB SERVICES BR','4.2.03','-1,23'),
            ('CARTAO PJ - GOOGLE WORKSPACE','4.2.04','-1,23'),('PIX ENVIADO CONTABILIDADE NOVA','4.2.06','-1,23'),
            ('PIX ENVIADO ATLAS IDIOMAS LTDA','2.1.01.001','-1,23'),
            ('PIX RECEBIDO 12345678900000 SEM IDENTIFICACAO','1.1.09.002','1,23'),
            ('DEVOLUCAO PIX - MUNDO ABERTO INTERC','2.1.01.001','1,23'),
            ('TRANSF ENTRE CONTAS P/ BCO MERIDIANO AG 0091 CC 90233-5','1.1.09.001','-1,23')]
        self.movimentos([('02/04/2032',d,'',v,'0,00') for d,c,v in casos])
        r,_=self.rodar(); p=r.partes['EXTRATO_AURORA']
        self.assertEqual([l['conta_codigo'] for l in p.linhas['lancamentos_classificados.csv']],[c for d,c,v in casos])
        self.assertEqual(len(p.linhas['pendencias.csv']),2)
        self.assertEqual(len(p.linhas['lancamentos_classificados.csv']),len(casos))
