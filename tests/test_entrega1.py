"""Amostras sintéticas; nenhum total de produção é critério único de aceite."""

from contextlib import redirect_stdout
import csv
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openpyxl import Workbook

from tarvo.__main__ import main
from tarvo.execucao import executar
from tarvo.exportacao import publicar
from tarvo.modelos import ErroEntrada
from tarvo.validacao import validar

REGRAS = Path(__file__).resolve().parents[1] / "regras.toml"
CABECALHO = [
    "id_transacao", "data_movimento", "cod_estabelecimento", "nome_estabelecimento",
    "tipo_lancamento", "modalidade", "qtd_parcelas", "valor_bruto", "taxa_aplicada_pct",
    "valor_taxa", "id_referencia", "data_venda_original",
]


class FluxoTest(unittest.TestCase):
    def setUp(self):
        self.temporario = TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.raiz = Path(self.temporario.name)
        self.dados = self.raiz / "dados"
        self.dados.mkdir()
        self.saida = self.raiz / "saida"
        self.vendas()
        self.taxas()

    def vendas(self, linhas=None):
        if linhas is None:
            linhas = [{"id_transacao": "A", "valor_bruto": "1,00"},
                      {"id_transacao": "B", "valor_bruto": "1,00"}]
        with (self.dados / "exportacao.csv").open("w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=CABECALHO, delimiter=";")
            escritor.writeheader()
            for linha in linhas:
                valores = {
                    "id_transacao": "A", "data_movimento": "02/03/2031", "cod_estabelecimento": "42",
                    "nome_estabelecimento": "NOME ORBE DIFERENTE", "tipo_lancamento": "VENDA",
                    "modalidade": "CREDITO A VISTA", "qtd_parcelas": "1", "valor_bruto": "1,00",
                    "taxa_aplicada_pct": "99,00", "valor_taxa": "999,99",
                    "id_referencia": "", "data_venda_original": "",
                }
                escritor.writerow(valores | linha)

    def taxas(self, linhas=None, aba="Taxas vigentes"):
        livro = Workbook()
        planilha = livro.active
        planilha.title = aba
        planilha.append(["Cabeçalho do exportador"])
        planilha.append([])
        planilha.append(["Lojista", "CNPJ", "EC Orbe", "Débito", "Crédito à vista", "Pix", "Vigência", "Obs"])
        if linhas is None:
            linhas = [["Loja Sintética", "1234567800012", "42", 0.005, "0,50%", 0.005, "01/01/2031", ""]]
        for linha in linhas:
            planilha.append(linha)
        antiga = livro.create_sheet("ANTIGO 2025 - nao usar")
        antiga.append(["Lojista", "CNPJ", "EC Orbe", "Débito", "Crédito à vista", "Pix", "Vigência", "Obs"])
        antiga.append(["Loja Sintética", "1234567800012", "42", 0.99, 0.99, 0.99, "01/01/2031", ""])
        livro.save(self.dados / "contratos.xlsx")
        livro.close()

    def executar(self):
        return executar(self.dados, REGRAS)

    def test_calculo_por_linha_contrato_e_rastro(self):
        resultado = self.executar()
        self.assertEqual(resultado.situacao, "COMPLETO")
        self.assertTrue(resultado.validado)
        self.assertEqual(resultado.comissoes[0]["comissao_brl"], "0.02")
        self.assertEqual(resultado.comissoes[0]["cnpj"], "01234567800012")
        self.assertEqual([r["valor"] for r in resultado.rastro], ["0.01", "0.01"])
        self.assertEqual(resultado.rastro[0]["ref_contrato"], "Taxas vigentes!L4")
        self.assertEqual(resultado.contribuicoes[0].taxa, Decimal("0.005"))
        publicar(resultado, self.saida)
        with (self.saida / "comissoes_por_lojista.csv").open(encoding="utf-8", newline="") as f:
            linhas = list(csv.DictReader(f, delimiter=";"))
        self.assertEqual(linhas[0]["comissao_brl"], "0.02")

    def test_ausencia_de_fontes_do_alvo_nao_bloqueia(self):
        self.assertEqual(self.executar().situacao, "COMPLETO")
        self.assertEqual(set(self.executar().fontes), {"orbe", "taxas", "regras"})

    def test_evento_futuro_vira_pendencia_sem_comissao_zero(self):
        self.vendas([{"id_transacao": "A"}, {"id_transacao": "B", "tipo_lancamento": "ESTORNO", "valor_bruto": "-1,00"}])
        resultado = self.executar()
        self.assertEqual(resultado.situacao, "PROVISORIO")
        self.assertEqual(len(resultado.contribuicoes), 1)
        self.assertEqual(resultado.pendencias[0].origem.ref, "B")
        self.assertEqual(resultado.comissoes[0]["comissao_brl"], "0.01")

    def test_nome_nao_e_usado_para_casar_ec(self):
        self.vendas([{"cod_estabelecimento": "999"}])
        resultado = self.executar()
        self.assertEqual(resultado.situacao, "PROVISORIO")
        self.assertEqual(resultado.comissoes, [])
        self.assertEqual(resultado.pendencias[0].quem_decide, "Comercial")

    def test_vigencia_desconhecida_e_observacao_nao_sao_ignoradas(self):
        for vigencia, obs in [("prazo a combinar", ""), ("01/01/2031", "condição especial")]:
            with self.subTest(vigencia=vigencia, obs=obs):
                self.taxas([["Loja", "1234567800012", "42", .005, .005, .005, vigencia, obs]])
                resultado = self.executar()
                self.assertEqual(resultado.contribuicoes, [])
                self.assertEqual(len(resultado.pendencias), 2)

    def test_contrato_multiplo_nao_seleciona_primeiro(self):
        linha = ["Loja", "1234567800012", "42", .005, .005, .005, "01/01/2031", ""]
        self.taxas([linha, linha])
        self.assertEqual(self.executar().contribuicoes, [])

    def test_venda_anterior_ao_contrato_nao_e_calculada(self):
        self.vendas([{"data_movimento": "01/12/2030"}])
        self.assertEqual(self.executar().contribuicoes, [])

    def test_taxa_textual_sem_unidade_formula_e_ausencia_nao_sao_inferidas(self):
        for valor in ["0,50", "=1/200", None]:
            with self.subTest(valor=valor):
                self.taxas([["Loja", "1234567800012", "42", .005, valor, .005, "01/01/2031", ""]])
                self.assertEqual(self.executar().contribuicoes, [])

    def test_modalidade_parcelas_e_sinal_ficam_pendentes(self):
        for campos in [{"modalidade": "NOVA"}, {"qtd_parcelas": "13"}, {"valor_bruto": "-1,00"}]:
            with self.subTest(campos=campos):
                self.vendas([campos])
                resultado = self.executar()
                self.assertEqual(resultado.situacao, "PROVISORIO")
                self.assertEqual(len(resultado.pendencias), 1)

    def test_linha_malformada_e_contada(self):
        self.vendas([{"id_transacao": "A"}, {"id_transacao": "B", "valor_bruto": "NaN"}])
        resultado = self.executar()
        self.assertEqual(resultado.linhas_lidas, 2)
        self.assertEqual(len(resultado.pendencias), 1)
        self.assertTrue(resultado.validado)

    def test_identificador_duplicado_bloqueia_sem_deduplicacao_arbitraria(self):
        self.vendas([{"id_transacao": "A"}, {"id_transacao": "A"}])
        self.assertEqual(self.executar().situacao, "BLOQUEADO")

    def test_fonte_ausente_bloqueia_e_remove_somente_saidas_proprias_antigas(self):
        publicar(self.executar(), self.saida)
        (self.dados / "contratos.xlsx").unlink()
        resultado = self.executar()
        self.assertEqual(resultado.situacao, "BLOQUEADO")
        self.assertEqual(resultado.fontes["orbe"]["situacao"], "DISPONIVEL")
        manifesto = publicar(resultado, self.saida)
        self.assertEqual(manifesto["arquivos"], {})
        self.assertFalse((self.saida / "rastro.csv").exists())

    def test_layout_invalido_bloqueia_com_arquivo_e_colunas(self):
        (self.dados / "exportacao.csv").write_text("id_transacao;outra\nA;1\n", encoding="utf-8")
        resultado = self.executar()
        self.assertEqual(resultado.situacao, "BLOQUEADO")
        self.assertTrue(any("exportacao.csv" in m and "colunas" in m for m in resultado.motivos))

    def test_layout_taxas_invalido(self):
        self.taxas(aba="Outra aba")
        resultado = self.executar()
        self.assertEqual(resultado.situacao, "BLOQUEADO")
        self.assertIn("contratos.xlsx", resultado.fontes["taxas"]["motivo"])

    def test_configuracao_invalida(self):
        caminho = self.raiz / "invalida.toml"
        for texto in ["versao = [", 'versao = 1\nfonte = "teste"\nentrada = []',
                      'versao = 1\nfonte = "teste"\nmodalidades = []\n[entrada]\naba_taxas = "Taxas vigentes"']:
            with self.subTest(texto=texto):
                caminho.write_text(texto, encoding="utf-8")
                self.assertEqual(executar(self.dados, caminho).situacao, "BLOQUEADO")
        caminho.write_bytes(b"\xff")
        self.assertEqual(executar(self.dados, caminho).situacao, "BLOQUEADO")

    def test_csv_alheio_invalido_nao_bloqueia_checkout(self):
        (self.dados / "outro_banco.csv").write_bytes(b"\x81")
        self.assertEqual(self.executar().situacao, "COMPLETO")

    def test_dois_relatorios_orbe_bloqueiam_sem_escolha_automatica(self):
        (self.dados / "ajustes.csv").write_bytes((self.dados / "exportacao.csv").read_bytes())
        resultado = self.executar()
        self.assertEqual(resultado.situacao, "BLOQUEADO")
        self.assertIn("ajustes.csv", resultado.fontes["orbe"]["motivo"])

    def test_evento_sem_parcelas_preserva_bruto_na_pendencia(self):
        self.vendas([{"tipo_lancamento": "ANTECIPACAO", "qtd_parcelas": ""}])
        resultado = self.executar()
        self.assertEqual(resultado.pendencias[0].valor_bruto, Decimal("1.00"))
        self.assertIn("Taxa contratada ausente", resultado.pendencias[0].motivo)

    def test_manifesto_externo_invalido_nao_e_sobrescrito(self):
        self.saida.mkdir()
        caminho = self.saida / "manifesto.json"
        caminho.write_text("[]", encoding="utf-8")
        with self.assertRaises(ErroEntrada):
            publicar(self.executar(), self.saida)
        self.assertEqual(caminho.read_text(encoding="utf-8"), "[]")

    def test_multiplas_competencias_bloqueiam(self):
        self.vendas([{"id_transacao": "A"}, {"id_transacao": "B", "data_movimento": "02/04/2031"}])
        self.assertEqual(self.executar().situacao, "BLOQUEADO")

    def test_rastro_corrompido_nao_publica(self):
        resultado = self.executar()
        resultado.rastro[0]["valor"] = "0.00"
        with self.assertRaises(ErroEntrada):
            publicar(resultado, self.saida)
        self.assertFalse((self.saida / "manifesto.json").exists())

    def test_cobertura_corrompida_falha(self):
        resultado = self.executar()
        resultado.contribuicoes.pop()
        with self.assertRaises(ErroEntrada):
            validar(resultado)

    def test_determinismo_inclui_manifesto(self):
        publicar(self.executar(), self.saida)
        antes = {p.name: p.read_bytes() for p in self.saida.iterdir()}
        publicar(self.executar(), self.saida)
        depois = {p.name: p.read_bytes() for p in self.saida.iterdir()}
        self.assertEqual(antes, depois)

    def test_nao_sobrescreve_arquivo_externo_ou_modificado(self):
        self.saida.mkdir()
        caminho = self.saida / "rastro.csv"
        caminho.write_text("arquivo do usuário", encoding="utf-8")
        with self.assertRaises(ErroEntrada):
            publicar(self.executar(), self.saida)
        self.assertEqual(caminho.read_text(encoding="utf-8"), "arquivo do usuário")
        caminho.unlink()
        publicar(self.executar(), self.saida)
        caminho.write_text("alterado pelo usuário", encoding="utf-8")
        with self.assertRaises(ErroEntrada):
            publicar(self.executar(), self.saida)

    def test_cli_codigos_de_saida_e_decisoes_pendentes(self):
        argumentos = ["--dados", str(self.dados), "--saida", str(self.saida), "--regras", str(REGRAS)]
        texto = StringIO()
        with redirect_stdout(texto):
            self.assertEqual(main(argumentos), 0)
            self.vendas([{"tipo_lancamento": "ESTORNO", "valor_bruto": "-1,00"}])
            self.assertEqual(main(argumentos), 2)
            (self.dados / "contratos.xlsx").unlink()
            self.assertEqual(main(argumentos), 1)
        self.assertIn("D-07", texto.getvalue())
        manifesto = json.loads((self.saida / "manifesto.json").read_text(encoding="utf-8"))
        self.assertIsNone(manifesto["total_parcial_brl"])


if __name__ == "__main__":
    unittest.main()
