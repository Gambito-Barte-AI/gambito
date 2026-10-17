"""Aceite do comando instalado e auditoria independente, fora da raiz do projeto."""

import csv
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from openpyxl import Workbook

from validar_saida import ErroAceite, verificar


class AceiteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.dados = self.raiz / "dados"
        self.dados.mkdir()
        self.saida = self.raiz / "saida"
        self.regras = self.raiz / "regras.toml"
        self.regras.write_text('''versao = 1
fonte = "Amostra sintética de aceite"
[entrada]
aba_taxas = "Taxas"
[modalidades]
PIX = "pix"
[[decisoes_pendentes]]
id = "D-07"
descricao = "Decisão não ratificada"
tratamento_atual = "Amostra de verificação da preservação das decisões"
''', encoding="utf-8")
        livro = Workbook()
        aba = livro.active
        aba.title = "Taxas"
        aba.append(["Lojista", "CNPJ", "EC Orbe", "Débito", "Crédito à vista", "Pix", "Vigência", "Obs"])
        aba.append(["Loja de teste", "01234567800012", "42", .01, .02, .005, "01/01/2030", ""])
        livro.save(self.dados / "taxas.xlsx")
        livro.close()
        self.vendas()

    def vendas(self, extras=(), data="02/04/2032"):
        with (self.dados / "orbe.csv").open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(["id_transacao", "data_movimento", "cod_estabelecimento", "tipo_lancamento",
                               "modalidade", "qtd_parcelas", "valor_bruto", "id_referencia", "data_venda_original"])
            escritor.writerow(["A", data, "42", "VENDA", "PIX", "1", "1,00", "", ""])
            for ref, modalidade, ec, parcelas in extras:
                escritor.writerow([ref, data, ec, "VENDA", modalidade, parcelas, "1,00", "", ""])

    def executar(self, codigo=0):
        ambiente = os.environ.copy()
        for chave in ("PYTHONPATH", "PYTHONHOME", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            ambiente.pop(chave, None)
        ambiente["PYTHONNOUSERSITE"] = "1"
        ambiente["PYTHONUTF8"] = "1"
        processo = subprocess.run(
            [sys.executable, "-m", "tarvo", "--dados", str(self.dados), "--saida", str(self.saida),
             "--regras", str(self.regras)], cwd=self.raiz, env=ambiente,
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        self.assertEqual(processo.returncode, codigo, processo.stdout + processo.stderr)
        return processo

    def auditar(self, esperar="COMPLETO"):
        return verificar(self.dados, self.saida, self.regras, esperar)

    def regravar_hash(self, nome):
        caminho = self.saida / "manifesto.json"
        m = json.loads(caminho.read_text(encoding="utf-8"))
        m["arquivos"][nome] = sha256((self.saida / nome).read_bytes()).hexdigest()
        caminho.write_text(json.dumps(m), encoding="utf-8")

    def test_execucao_instalada_fora_da_raiz_sem_chaves_e_repeticao(self):
        self.executar()
        antes = {p.name: p.read_bytes() for p in self.saida.iterdir()}
        self.executar()
        self.assertEqual(antes, {p.name: p.read_bytes() for p in self.saida.iterdir()})
        self.assertEqual(self.auditar()["total_brl"], "0.01")

    def test_outro_mes_e_modalidade_desconhecida_sem_perda_de_cobertura(self):
        self.vendas([("B", "NOVA", "42", "1"), ("C", "PIX", "99", "1"),
                     ("D", "PIX", "42", "13")], data="02/05/2032")
        self.executar(2)
        aceite = self.auditar("PROVISORIO")
        self.assertEqual(aceite["competencia"], "2032-05")
        self.assertEqual(aceite["cobertura"], {"linhas_lidas": 4, "calculadas": 1, "pendentes": 3, "bloqueadas": 0})

    def test_fonte_ausente_invalida_saida_anterior(self):
        self.executar()
        (self.dados / "taxas.xlsx").unlink()
        self.executar(1)
        self.auditar("BLOQUEADO")
        self.assertFalse((self.saida / "rastro.csv").exists())
        self.assertFalse((self.saida / "comissoes_por_lojista.csv").exists())

    def test_layout_invalido_falha_sem_csvs(self):
        (self.dados / "orbe.csv").write_text("id_transacao;outra\nA;1\n", encoding="utf-8")
        self.executar(1)
        self.auditar("BLOQUEADO")
        self.assertEqual(list(self.saida.glob("*.csv")), [])

    def test_auditor_detecta_soma_errada_mesmo_com_hash_atualizado(self):
        self.executar()
        caminho = self.saida / "comissoes_por_lojista.csv"
        caminho.write_bytes(caminho.read_bytes().replace(b"0.01", b"9.99"))
        self.regravar_hash(caminho.name)
        with self.assertRaisesRegex(ErroAceite, "Soma do rastro"):
            self.auditar()

    def test_auditor_detecta_referencia_inventada_mesmo_com_hash_atualizado(self):
        self.executar()
        caminho = self.saida / "rastro.csv"
        caminho.write_bytes(caminho.read_bytes().replace(b";A;", b";INVENTADA;"))
        self.regravar_hash(caminho.name)
        with self.assertRaisesRegex(ErroAceite, "destino"):
            self.auditar()

    def test_auditor_detecta_decisao_financeira_omitida(self):
        self.executar()
        caminho = self.saida / "manifesto.json"
        m = json.loads(caminho.read_text(encoding="utf-8"))
        m["decisoes_financeiras_pendentes"] = []
        caminho.write_text(json.dumps(m), encoding="utf-8")
        with self.assertRaisesRegex(ErroAceite, "Decisões financeiras"):
            self.auditar()

    def test_soma_interna_corrompida_bloqueia_publicacao(self):
        from tarvo.execucao import executar
        from tarvo.exportacao import publicar
        from tarvo.validacao import consolidar

        def corromper(resultado):
            consolidar(resultado)
            resultado.rastro[0]["valor"] = "9.99"

        with patch("tarvo.execucao.validacao.consolidar", side_effect=corromper):
            resultado = executar(self.dados, self.regras)
        self.assertEqual(resultado.situacao, "BLOQUEADO")
        publicar(resultado, self.saida)
        self.auditar("BLOQUEADO")
        self.assertEqual(list(self.saida.glob("*.csv")), [])

    def test_publicacao_interrompida_nao_deixa_manifesto_valido(self):
        from tarvo.execucao import executar
        from tarvo.exportacao import publicar

        original = os.replace
        chamadas = []

        def falhar_no_segundo_csv(origem, destino):
            chamadas.append(str(destino))
            if len(chamadas) == 3:
                raise OSError("falha de escrita simulada")
            return original(origem, destino)

        with patch("tarvo.exportacao.os.replace", side_effect=falhar_no_segundo_csv):
            with self.assertRaises(OSError):
                publicar(executar(self.dados, self.regras), self.saida)
        self.auditar("BLOQUEADO")


if __name__ == "__main__":
    unittest.main()
