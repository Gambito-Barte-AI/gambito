"""Regressões das decisões financeiras sobre movimentos sintéticos."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tarvo import checkout, classificacao, regras
from tarvo.leitores import orbe
from tarvo.modelos import ContaContabil, MovimentoBanco, Origem


CONFIG = Path(__file__).resolve().parents[1] / "regras.toml"


class RegrasFinanceirasAtuaisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = regras.carregar(CONFIG)

    def classificar(self, banco, entradas, codigos):
        contas = {
            codigo: ContaContabil(Origem("plano_sintetico.csv", codigo, n), codigo,
                                  "Conta analítica", "ANALITICA", True)
            for n, codigo in enumerate(codigos, 1)
        }
        movimentos = [
            MovimentoBanco(Origem("extrato_sintetico", f"REF-{n}", n), date(2032, 4, 3),
                           descricao, Decimal(valor))
            for n, (descricao, valor) in enumerate(entradas, 1)
        ]
        parametros = classificacao.parametros(self.config, banco)
        return classificacao.calcular(movimentos, contas, parametros, banco)

    def test_aurora_pix_sem_pagador_e_pix_de_terceiro(self):
        parte = self.classificar("AURORA", [
            ("PIX RECEBIDO 12345678000190 SEM IDENTIFICACAO", "91.37"),
            ("PIX ENVIADO ROTA GLOBAL INTERCAMBIO", "-83.42"),
            ("PIX ENVIADO DESTINATARIO NOVO", "-74.53"),
        ], {"1.1.09.002", "2.1.01.001"})
        linhas = parte.linhas["lancamentos_classificados.csv"]
        self.assertEqual([linha["conta_codigo"] for linha in linhas],
                         ["1.1.09.002", "2.1.01.001"])
        pendencias = parte.linhas["pendencias.csv"]
        self.assertEqual([p["tipo"] for p in pendencias],
                         ["CREDITO_NAO_IDENTIFICADO", "CLASSIFICACAO_NAO_RESOLVIDA"])
        self.assertIn("Caio", pendencias[0]["proximo_passo"])
        self.assertEqual(pendencias[0]["quem_decide"], "Financeiro")
        self.assertEqual(pendencias[1]["valor_brl"], "-74.53")

    def test_meridiano_iof_liquidacao_aplicacao_e_rendimento(self):
        parte = self.classificar("MERIDIANO", [
            ("TED ENVIADA PONTE CAMBIO SA LIQ OPERACOES", "-137.43"),
            ("IOF S/ OPERACAO CREDITO", "-12.34"),
            ("APLICACAO AUTOMATICA CDB DI", "-25.61"),
            ("RESGATE AUTOMATICO CDB DI", "10.07"),
            ("RENDIMENTO APLIC AUTOMATICA", "0.83"),
        ], {"2.1.02.001", "4.3.01", "1.1.02.001", "3.2.01"})
        self.assertEqual(
            [linha["conta_codigo"] for linha in parte.linhas["lancamentos_classificados.csv"]],
            ["2.1.02.001", "4.3.01", "1.1.02.001", "1.1.02.001", "3.2.01"],
        )
        self.assertEqual(parte.linhas["pendencias.csv"], [])
        self.assertEqual(len(parte.rastro), 5)

    def test_estorno_com_bandeira_diferente_conserva_vinculo_por_referencia(self):
        conteudo = (
            "id_transacao;data_movimento;cod_estabelecimento;tipo_lancamento;modalidade;"
            "qtd_parcelas;bandeira;valor_bruto;id_referencia;data_venda_original\n"
            "V;02/04/2032;42;VENDA;CREDITO A VISTA;1;VISA;100,00;;\n"
            "E;03/04/2032;42;ESTORNO;CREDITO A VISTA;1;MASTERCARD;-100,00;V;02/04/2032\n"
        )
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "relatorio_sintetico.csv"
            caminho.write_text(conteudo, encoding="utf-8")
            eventos, pendencias, quantidade = orbe.ler(caminho)
        self.assertEqual(quantidade, 2)
        self.assertEqual(pendencias, [])
        self.assertEqual(
            checkout.conferir_estorno(eventos[1], {"V": eventos[0]}, {"V": Decimal("100.00")}),
            "",
        )


if __name__ == "__main__":
    unittest.main()
