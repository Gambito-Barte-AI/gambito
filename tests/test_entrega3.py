"""Estornos por data/faixa e reversões exclusivas, com amostras sintéticas."""

from dataclasses import replace
import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tarvo.checkout import calcular
from tarvo.exportacao import publicar
from tarvo.execucao import executar
from tarvo.modelos import Cadastro, Contrato, ErroEntrada, Evento, Identidade, Origem, Resultado
from tarvo.partes import projetar_pendencias
from tarvo.validacao import consolidar, validar


class Entrega3Test(unittest.TestCase):
    def setUp(self):
        self.cnpj = "01234567800012"
        origem = Origem("contratos.xlsx", "Vigente!L3", 3)
        self.contrato = Contrato(origem, "42", self.cnpj, "Loja",
                                 {"debito": Decimal("0.01"), "credito_vista": Decimal("0.02"),
                                  "parcelado_2_6": Decimal("0.03"), "parcelado_7_12": Decimal("0.04"),
                                  "pix": Decimal("0.005"), "antecipacao": Decimal("0.021")}, date(2030, 1, 1))
        self.cadastro = Cadastro([self.contrato], [Identidade(self.cnpj, "Loja", origem, "42")])
        self.regras = {"modalidades": {"DEBITO": "debito", "CREDITO A VISTA": "credito_vista",
                                       "CREDITO PARCELADO": "parcelado", "PIX": "pix"}}

    def evento(self, ref="V", tipo="VENDA", bruto="100.00", **campos):
        e = Evento(Origem("orbe.csv", ref, 2), date(2031, 3, 20), "42", tipo,
                   "CREDITO A VISTA", 1, Decimal(bruto), "", None)
        return replace(e, **campos)

    def estorno(self, **campos):
        e = self.evento("E", "ESTORNO", "-100.00", referencia="V", data_original=date(2031, 2, 15))
        return replace(e, **campos)

    def antecipacao(self, **campos):
        return self.evento("A", "ANTECIPACAO", "100.00", modalidade="", parcelas=None, **campos)

    def reversao(self, **campos):
        e = self.evento("R", "REVERSAO ANTECIPACAO", "-100.00", modalidade="", parcelas=None,
                        referencia="A", data_original=date(2031, 3, 20), data=date(2031, 3, 21))
        return replace(e, **campos)

    def calcular(self, eventos):
        return calcular(eventos, self.cadastro, self.regras)

    def resultado(self, eventos):
        contribuicoes, pendencias = self.calcular(eventos)
        r = Resultado(situacao="PROVISORIO" if pendencias else "COMPLETO", eventos=eventos,
                      contribuicoes=contribuicoes, pendencias=pendencias, linhas_lidas=len(eventos),
                      competencia="2031-03")
        r.fontes = {nome: {"situacao": "DISPONIVEL"} for nome in ("orbe", "taxas", "regras")}
        consolidar(r)
        validar(r)
        return r

    def test_estorno_historico_usa_data_original_sem_reabrir_mes_anterior(self):
        self.cadastro.contratos = [replace(self.contrato, fim=date(2031, 2, 28)),
                                   replace(self.contrato, inicio=date(2031, 3, 1), taxas={"credito_vista": Decimal("0.09")})]
        cs, ps = self.calcular([self.estorno()])
        self.assertFalse(ps)
        self.assertEqual(cs[0].valor, Decimal("-2.00"))
        self.assertEqual(cs[0].competencia, "2031-03")
        self.assertEqual(cs[0].data_base_taxa, date(2031, 2, 15))
        self.assertEqual(cs[0].ref_original, "V")
        self.assertEqual(cs[0].arquivo_original, "")  # fonte histórica não foi inventada

    def test_faixa_vem_do_estorno_e_nao_da_venda_local(self):
        venda = self.evento()
        estorno = self.estorno(data_original=venda.data, modalidade="CREDITO PARCELADO", parcelas=7)
        cs, ps = self.calcular([venda, estorno])
        self.assertFalse(ps)
        self.assertEqual([c.valor for c in cs], [Decimal(2), Decimal(-4)])

    def test_estorno_pre_isencao_e_isento_sao_distintos(self):
        self.regras["isencoes"] = [{"id": "ZERO", "cnpj": self.cnpj,
                                    "inicio": date(2031, 3, 1), "fim": date(2031, 3, 31)}]
        historico = self.estorno()
        atual = self.estorno(origem=Origem("orbe.csv", "E2", 3), referencia="V2", data_original=date(2031, 3, 10))
        venda = self.evento("V2", data=date(2031, 3, 10))
        cs, ps = self.calcular([historico, atual, venda])
        self.assertFalse(ps)
        self.assertEqual([c.valor for c in cs], [Decimal(-2), Decimal(0), Decimal(0)])

    def test_arredondamento_meio_centavo_negativo(self):
        e = self.estorno(bruto=Decimal("-1.00"), modalidade="PIX")
        self.assertEqual(self.calcular([e])[0][0].valor, Decimal("-0.01"))

    def test_estorno_com_dados_insuficientes_e_sinal_errado_fica_pendente(self):
        for campos in ({"referencia": ""}, {"data_original": None}, {"data_original": date(2031, 4, 1)},
                       {"bruto": Decimal(100)}, {"parcelas": 13}):
            with self.subTest(campos=campos):
                cs, ps = self.calcular([self.estorno(**campos)])
                self.assertFalse(cs)
                self.assertEqual(len(ps), 1)

    def test_estorno_referencia_local_ausente_ou_inconsistente(self):
        for e, outros in ((self.estorno(), [self.evento()]),
                          (self.estorno(), [self.evento(tipo="ANTECIPACAO")]),
                          (self.estorno(), [self.evento(ec="99", data=date(2031, 2, 15))])):
            cs, ps = self.calcular([e, *outros])
            self.assertTrue(any(p.origem.ref == "E" for p in ps))

    def test_estorno_orfao_do_mes_entra_com_pendencia_derivada(self):
        e = self.estorno(data_original=date(2031, 3, 1), bruto=Decimal("-137.00"))
        r = self.resultado([e])
        self.assertFalse(r.pendencias)
        self.assertEqual(r.comissoes[0]["comissao_brl"], "-2.74")
        self.assertTrue(r.contribuicoes[0].original_ausente)
        linhas, rastros = projetar_pendencias(r)
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["categoria"], "DADOS")
        self.assertEqual(linhas[0]["valor_brl"], "-2.74")
        self.assertEqual(linhas[0]["quem_decide"], "Financeiro")
        self.assertEqual(rastros[0]["ref_evento_original"], "V")

    def test_estornos_que_excedem_venda_nao_sao_escolhidos_por_ordem(self):
        venda = self.evento()
        a = self.estorno(bruto=Decimal(-60), data_original=venda.data)
        b = replace(a, origem=Origem("orbe.csv", "E2", 3))
        cs, ps = self.calcular([venda, a, b])
        self.assertEqual(len(cs), 1)
        self.assertEqual(len(ps), 2)

    def test_antecipacao_usa_coluna_propria_sem_modalidade(self):
        cs, ps = self.calcular([self.antecipacao()])
        self.assertFalse(ps)
        self.assertEqual(cs[0].valor, Decimal("2.10"))
        self.assertEqual(cs[0].faixa, "antecipacao")

    def test_antecipacao_sem_taxa_nao_usa_constante(self):
        self.cadastro.contratos = [replace(self.contrato, taxas={"credito_vista": Decimal("0.99")})]
        cs, ps = self.calcular([self.antecipacao()])
        self.assertFalse(cs)
        self.assertIn("Taxa contratada ausente", ps[0].motivo)

    def test_reversao_anula_apenas_original_referenciado(self):
        ante = self.antecipacao()
        outra = replace(ante, origem=Origem("orbe.csv", "B", 3), bruto=Decimal(200))
        r = self.resultado([ante, outra, self.reversao()])
        self.assertEqual([c.valor for c in r.contribuicoes], [Decimal("2.10"), Decimal("4.20"), Decimal("-2.10")])
        self.assertEqual(r.comissoes[0]["comissao_brl"], "4.20")

    def test_reversao_independe_da_ordem_das_linhas(self):
        r = self.resultado([self.reversao(), self.antecipacao()])
        self.assertEqual(r.comissoes[0]["comissao_brl"], "0.00")
        self.assertEqual(len(r.rastro), 2)

    def test_reversao_nao_usa_taxa_nova(self):
        self.cadastro.contratos = [replace(self.contrato, fim=date(2031, 3, 20)),
                                   replace(self.contrato, inicio=date(2031, 3, 21), taxas={"antecipacao": Decimal("0.99")})]
        cs, ps = self.calcular([self.antecipacao(), self.reversao()])
        self.assertFalse(ps)
        self.assertEqual(cs[1].valor, Decimal("-2.10"))
        self.assertEqual(cs[1].taxa, cs[0].taxa)

    def test_reversao_de_antecipacao_isenta_continua_zero_apos_isencao(self):
        self.regras["isencoes"] = [{"id": "ZERO", "cnpj": self.cnpj,
                                    "inicio": date(2031, 3, 1), "fim": date(2031, 3, 20)}]
        cs, ps = self.calcular([self.antecipacao(), self.reversao()])
        self.assertFalse(ps)
        self.assertEqual([c.valor for c in cs], [Decimal(0), Decimal(0)])
        self.assertEqual(cs[1].regra, "ZERO")

    def test_reversao_inconsistente_nao_e_recalculada(self):
        for campos in ({"referencia": ""}, {"data_original": None},
                       {"data_original": date(2031, 3, 1)}, {"data": date(2031, 3, 19)},
                       {"bruto": Decimal(-50)}, {"bruto": Decimal(100)}):
            with self.subTest(campos=campos):
                cs, ps = self.calcular([self.antecipacao(), self.reversao(**campos)])
                self.assertEqual(len(cs), 1)
                self.assertEqual(len(ps), 1)

    def test_reversao_orfa_do_mes_usa_taxa_original_e_fica_para_revisao(self):
        self.cadastro.contratos = [replace(self.contrato, fim=date(2031, 3, 20)),
                                   replace(self.contrato, inicio=date(2031, 3, 21),
                                           taxas={"antecipacao": Decimal("0.99")})]
        r = self.resultado([self.reversao(referencia="ORIGEM_AUSENTE", bruto=Decimal("-137"))])
        self.assertFalse(r.pendencias)
        self.assertEqual(r.comissoes[0]["comissao_brl"], "-2.88")
        self.assertTrue(r.contribuicoes[0].original_ausente)
        self.assertEqual(r.rastro[0]["ref_evento_original"], "ORIGEM_AUSENTE")
        self.assertEqual(projetar_pendencias(r)[0][0]["valor_brl"], "-2.88")

    def test_reversao_nao_aceita_venda_como_antecipacao(self):
        cs, ps = self.calcular([self.evento("A"), self.reversao()])
        self.assertEqual(len(cs), 1)
        self.assertIn("tipo ou lojista", ps[0].motivo)

    def test_multiplas_reversoes_nao_cancelam_em_dobro(self):
        a, r = self.antecipacao(), self.reversao()
        cs, ps = self.calcular([a, r, replace(r, origem=Origem("orbe.csv", "R2", 4))])
        self.assertEqual(len(cs), 1)
        self.assertEqual(len(ps), 2)
        self.assertTrue(all("Múltiplas" in p.motivo for p in ps))

    def test_reversao_de_original_nao_calculado_tambem_e_pendente(self):
        a = self.antecipacao(data_original=date(2031, 1, 1))
        cs, ps = self.calcular([a, self.reversao()])
        self.assertFalse(cs)
        self.assertEqual(len(ps), 2)

    def test_tipo_desconhecido_nao_e_inferido_pelo_sinal(self):
        cs, ps = self.calcular([self.evento(tipo="AJUSTE")])
        self.assertFalse(cs)
        self.assertEqual(len(ps), 1)

    def test_rastro_mantem_evento_assinado_e_vinculo_sem_dupla_contagem(self):
        r = self.resultado([self.antecipacao(), self.reversao()])
        self.assertEqual(len(r.rastro), 2)
        reversao = next(l for l in r.rastro if l["ref_origem"] == "R")
        self.assertEqual(reversao["valor"], "-2.10")
        self.assertEqual(reversao["ref_evento_original"], "A")
        self.assertEqual(reversao["data_base_taxa"], "2031-03-20")
        reversao["ref_evento_original"] = "ERRADO"
        with self.assertRaises(ErroEntrada):
            validar(r)
        self.assertFalse(r.validado)

    def test_validador_rejeita_reversao_com_valor_alterado(self):
        r = self.resultado([self.antecipacao(), self.reversao()])
        r.contribuicoes[1] = replace(r.contribuicoes[1], valor=Decimal("-2.00"))
        with self.assertRaises(ErroEntrada):
            validar(r)

    def test_publicacao_negativa_sem_nota_calculada(self):
        r = self.resultado([self.estorno()])
        self.assertEqual(r.comissoes[0]["comissao_brl"], "-2.00")
        with TemporaryDirectory() as tmp:
            m = publicar(r, Path(tmp))
            self.assertEqual(set(m["arquivos"]), {"comissoes_por_lojista.csv", "rastro.csv", "pendencias.csv", "divergencias_taxa.csv", "notas_a_emitir.csv", "lancamentos_classificados.csv"})
            self.assertEqual(m["etapa"], "ALVO_A6")

    def test_pipeline_completo_le_antecipacao_e_relacoes(self):
        from openpyxl import Workbook

        with TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            dados = raiz / "dados"
            dados.mkdir()
            livro = Workbook()
            aba = livro.active
            aba.title = "Vigente"
            aba.append(["Lojista", "CNPJ", "EC Orbe", "Débito", "Crédito à vista",
                        "Pix", "Antecipação", "Vigência", "Obs"])
            aba.append(["Loja", self.cnpj, "42", .01, .02, .005, "2,50%", "01/01/2031", ""])
            livro.save(dados / "taxas.xlsx")
            livro.close()
            colunas = ["id_transacao", "data_movimento", "cod_estabelecimento", "tipo_lancamento",
                       "modalidade", "qtd_parcelas", "valor_bruto", "id_referencia", "data_venda_original"]
            with (dados / "orbe.csv").open("w", encoding="utf-8", newline="") as arquivo:
                escritor = csv.writer(arquivo, delimiter=";")
                escritor.writerow(colunas)
                escritor.writerow(["R", "20/03/2031", "42", "REVERSAO ANTECIPACAO", "", "", "-100,00", "A", "19/03/2031"])
                escritor.writerow(["E", "20/03/2031", "42", "ESTORNO", "CREDITO A VISTA", "1", "-100,00", "HISTORICA", "01/02/2031"])
                escritor.writerow(["A", "19/03/2031", "42", "ANTECIPACAO", "", "", "100,00", "", ""])
            config = raiz / "regras.toml"
            config.write_text('''versao = 1
fonte = "Amostra sintética"
[entrada]
aba_taxas = "Vigente"
[modalidades]
"CREDITO A VISTA" = "credito_vista"
''', encoding="utf-8")
            resultado = executar(dados, config)
            self.assertEqual(resultado.situacao, "COMPLETO")
            self.assertEqual(resultado.comissoes[0]["comissao_brl"], "-2.00")
            valores = {c.origem.ref: c.valor for c in resultado.contribuicoes}
            self.assertEqual(valores, {"A": Decimal("2.50"), "R": Decimal("-2.50"), "E": Decimal("-2.00")})
            manifesto = publicar(resultado, raiz / "saida")
            self.assertEqual(manifesto["cobertura"]["calculadas"], 3)
            with (dados / "orbe.csv").open("a", encoding="utf-8", newline="") as arquivo:
                escritor = csv.writer(arquivo, delimiter=";")
                escritor.writerow(["R2", "20/03/2031", "42", "REVERSAO ANTECIPACAO", "", "", "-40,00", "SEM_ANTECIPACAO", "19/03/2031"])
                escritor.writerow(["E2", "20/03/2031", "42", "ESTORNO", "CREDITO A VISTA", "1", "-30,00", "SEM_VENDA", "19/03/2031"])
            orfaos = executar(dados, config)
            self.assertEqual(orfaos.situacao, "PROVISORIO")
            self.assertEqual(orfaos.comissoes[0]["comissao_brl"], "-3.60")
            self.assertEqual({c.origem.ref for c in orfaos.contribuicoes if c.original_ausente}, {"R2", "E2"})
            manifesto = publicar(orfaos, raiz / "saida")
            self.assertEqual(manifesto["cobertura"]["calculadas"], 5)
            with (raiz / "saida" / "pendencias.csv").open(encoding="utf-8", newline="") as arquivo:
                pendencias = list(csv.DictReader(arquivo, delimiter=";"))
            self.assertEqual({p["ref_origem"] for p in pendencias if p["tipo"] == "ORIGEM_ORBE_A_CONFIRMAR"},
                             {"R2", "E2"})


if __name__ == "__main__":
    unittest.main()
