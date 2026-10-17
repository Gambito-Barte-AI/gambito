"""A1: coordenação real e resultados sintéticos, sem implementar módulos do alvo."""

from contextlib import redirect_stdout
import csv
from io import StringIO
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_aceite as amostras
from validar_saida import ErroAceite, verificar
from tarvo.__main__ import main
from tarvo.execucao import executar
from tarvo.exportacao import publicar
from tarvo.modelos import ResultadoParte
from tarvo.partes import agregar_situacoes, projetar_pendencias


class A1Test(unittest.TestCase):
    setUp = amostras.AceiteTest.setUp
    vendas = amostras.AceiteTest.vendas
    regravar_hash = amostras.AceiteTest.regravar_hash

    def ler(self, nome):
        with (self.saida / nome).open(encoding="utf-8", newline="") as arquivo:
            return list(csv.DictReader(arquivo, delimiter=";"))

    def banco(self, banco, ref, valor="1.00"):
        # Saída normalizada sintética: nenhum parser bancário ou regra contábil é executado.
        id_saida = f"TESTE:{banco}:{ref}"
        linha = dict(id_saida=id_saida, banco=banco, ref_origem=ref, data="2032-04-02",
                     descricao="Movimento sintético", valor=valor, conta_codigo="TESTE",
                     metodo="REGRA", confianca="1")
        return ResultadoParte(fontes=(banco.lower(), "plano_contas", "regras"),
            relatorios=("lancamentos_classificados.csv",), implementado=True, situacao="COMPLETO",
            linhas={"lancamentos_classificados.csv": [linha]},
            rastro=[dict(id_saida=id_saida, arquivo_origem=f"{banco}.teste", ref_origem=ref, valor=valor)],
            cobertura=dict(linhas_lidas=1, calculadas=1, pendentes=0, bloqueadas=0))

    def registrar_bancos(self, resultado):
        for nome in ("aurora", "meridiano", "plano_contas"):
            resultado.fontes[nome] = {"situacao": "DISPONIVEL"}
        resultado.partes["EXTRATO_AURORA"] = self.banco("AURORA", "L9")
        resultado.partes["EXTRATO_MERIDIANO"] = self.banco("MERIDIANO", "FITID-TESTE")

    def test_codigo_padrao_preserva_minimo_e_alvo_nao_finge_conclusao(self):
        args = ["--dados", str(self.dados), "--saida", str(self.saida), "--regras", str(self.regras)]
        with redirect_stdout(StringIO()):
            self.assertEqual(main(args), 0)
            self.assertEqual(main(args + ["--escopo", "alvo"]), 2)
        manifesto = json.loads((self.saida / "manifesto.json").read_text(encoding="utf-8"))
        self.assertEqual(manifesto["situacao"], "COMPLETO")
        self.assertEqual(manifesto["situacao_comando"], "PROVISORIO")
        self.assertEqual(manifesto["resultados"]["comissoes_por_lojista.csv"]["situacao"], "PROVISORIO")
        self.assertIn("REMESSAS", manifesto["resultados"]["comissoes_por_lojista.csv"]["partes_bloqueadas"])
        verificar(self.dados, self.saida, self.regras, "COMPLETO", "PROVISORIO")

    def test_ponte_ausente_ou_ainda_nao_lida_nao_bloqueia_checkout(self):
        (self.dados / "qualquer_nome.eml").write_text("Amostra ainda não processada", encoding="utf-8")
        antes = publicar(executar(self.dados, self.regras), self.saida)
        csv_antes = {p.name: p.read_bytes() for p in self.saida.glob("*.csv")}
        (self.dados / "qualquer_nome.eml").unlink()
        depois = publicar(executar(self.dados, self.regras), self.saida)
        self.assertEqual(antes["total_parcial_brl"], depois["total_parcial_brl"])
        self.assertEqual(csv_antes, {p.name: p.read_bytes() for p in self.saida.glob("*.csv")})
        self.assertEqual(depois["partes"]["CHECKOUT"]["situacao"], "COMPLETO")
        self.assertEqual(depois["partes"]["REMESSAS"]["fontes"]["ponte"], "BLOQUEADO")
        self.assertTrue(depois["partes"]["REMESSAS"]["implementado"])

    def test_comissao_corrompida_preserva_pendencia_independente_e_sua_cobertura(self):
        self.vendas([("B", "PIX", "99", "1")])
        resultado = executar(self.dados, self.regras)
        resultado.rastro[0]["valor"] = "9.99"
        m = publicar(resultado, self.saida)
        self.assertEqual(m["partes"]["CHECKOUT"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["partes"]["PENDENCIAS_CHECKOUT"]["situacao"], "COMPLETO")
        self.assertEqual(m["resultados"]["rastro.csv"]["situacao"], "PROVISORIO")
        self.assertEqual(m["cobertura"], dict(linhas_lidas=2, calculadas=0, pendentes=1, bloqueadas=1))
        self.assertEqual(len(self.ler("comissoes_por_lojista.csv")), 0)
        self.assertEqual(len(self.ler("pendencias.csv")), 1)
        self.assertEqual(len(self.ler("rastro.csv")), 1)
        self.assertIsNone(m["total_parcial_brl"])
        verificar(self.dados, self.saida, self.regras, "BLOQUEADO", "PROVISORIO")

    def test_pendencia_corrompida_preserva_comissao_e_sinaliza_codigo_parcial(self):
        self.vendas([("B", "PIX", "99", "1")])

        def corromper(resultado):
            linhas, rastros = projetar_pendencias(resultado)
            rastros[0]["valor"] = "9.99"
            return linhas, rastros

        args = ["--dados", str(self.dados), "--saida", str(self.saida), "--regras", str(self.regras)]
        with patch("tarvo.partes.projetar_pendencias", side_effect=corromper), redirect_stdout(StringIO()):
            self.assertEqual(main(args), 2)
        m = json.loads((self.saida / "manifesto.json").read_text(encoding="utf-8"))
        self.assertEqual(m["partes"]["CHECKOUT"]["situacao"], "COMPLETO")
        self.assertEqual(m["partes"]["PENDENCIAS_CHECKOUT"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["total_parcial_brl"], "0.01")
        self.assertEqual(m["cobertura"], dict(linhas_lidas=2, calculadas=1, pendentes=0, bloqueadas=1))
        self.assertEqual(len(self.ler("comissoes_por_lojista.csv")), 1)
        self.assertEqual(self.ler("pendencias.csv"), [])
        verificar(self.dados, self.saida, self.regras, "COMPLETO", "PROVISORIO")

    def test_fonte_aurora_ausente_nao_bloqueia_meridiano_nem_checkout(self):
        resultado = executar(self.dados, self.regras)
        self.registrar_bancos(resultado)
        resultado.fontes["aurora"] = {"situacao": "BLOQUEADO", "motivo": "Fonte ausente no teste"}
        m = publicar(resultado, self.saida, "alvo")
        self.assertEqual(m["partes"]["EXTRATO_AURORA"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["partes"]["EXTRATO_MERIDIANO"]["situacao"], "COMPLETO")
        self.assertEqual(m["partes"]["CHECKOUT"]["situacao"], "COMPLETO")
        self.assertEqual([l["banco"] for l in self.ler("lancamentos_classificados.csv")], ["MERIDIANO"])
        self.assertEqual(m["resultados"]["lancamentos_classificados.csv"]["situacao"], "PROVISORIO")

    def test_rastro_bancario_quebrado_nao_bloqueia_banco_independente(self):
        resultado = executar(self.dados, self.regras)
        self.registrar_bancos(resultado)
        resultado.partes["EXTRATO_AURORA"].rastro[0]["valor"] = "9.99"
        m = publicar(resultado, self.saida, "alvo")
        self.assertEqual(m["partes"]["EXTRATO_AURORA"]["situacao"], "BLOQUEADO")
        self.assertTrue(m["partes"]["EXTRATO_MERIDIANO"]["rastro_validado"])
        self.assertEqual(len(self.ler("lancamentos_classificados.csv")), 1)
        self.assertNotIn("TESTE:AURORA:L9", {r["id_saida"] for r in self.ler("rastro.csv")})

    def test_sem_taxas_preserva_parte_que_depende_apenas_de_ponte_e_regras(self):
        (self.dados / "taxas.xlsx").unlink()
        resultado = executar(self.dados, self.regras)
        resultado.fontes["ponte"] = {"situacao": "DISPONIVEL"}
        # Contribuição fornecida pelo teste; nenhuma fórmula de remessa foi implementada.
        linha = dict(id_saida="TESTE:REMESSA", cnpj="01234567800012", lojista="Sintético",
                     linha_negocio="REMESSA", comissao_brl="7.89")
        resultado.partes["REMESSAS"] = ResultadoParte(fontes=("ponte", "regras"),
            relatorios=("comissoes_por_lojista.csv", "pendencias.csv"), implementado=True, situacao="COMPLETO",
            linhas={"comissoes_por_lojista.csv": [linha]},
            rastro=[dict(id_saida="TESTE:REMESSA", arquivo_origem="anexo.teste", ref_origem="PC-TESTE", valor="7.89")],
            cobertura=dict(linhas_lidas=1, calculadas=1, pendentes=0, bloqueadas=0))
        m = publicar(resultado, self.saida, "alvo")
        self.assertEqual(m["partes"]["CHECKOUT"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["partes"]["REMESSAS"]["situacao"], "COMPLETO")
        self.assertEqual(m["partes"]["DIVERGENCIAS_REMESSA"]["situacao"], "BLOQUEADO")
        self.assertEqual(self.ler("comissoes_por_lojista.csv"), [linha])
        self.assertIsNone(m["total_parcial_brl"])  # campo legado é exclusivamente checkout

    def test_plano_ausente_bloqueia_bancos_mas_preserva_checkout(self):
        resultado = executar(self.dados, self.regras)
        self.registrar_bancos(resultado)
        resultado.fontes["plano_contas"] = {"situacao": "BLOQUEADO", "motivo": "Ausente no teste"}
        m = publicar(resultado, self.saida, "alvo")
        self.assertEqual(m["partes"]["CHECKOUT"]["situacao"], "COMPLETO")
        self.assertEqual(m["partes"]["EXTRATO_AURORA"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["partes"]["EXTRATO_MERIDIANO"]["situacao"], "BLOQUEADO")
        self.assertEqual(self.ler("lancamentos_classificados.csv"), [])

    def test_linha_fora_do_contrato_bloqueia_so_a_parte_produtora(self):
        resultado = executar(self.dados, self.regras)
        self.registrar_bancos(resultado)
        resultado.partes["EXTRATO_AURORA"].linhas["lancamentos_classificados.csv"] = [None]
        m = publicar(resultado, self.saida, "alvo")
        self.assertEqual(m["partes"]["EXTRATO_AURORA"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["partes"]["EXTRATO_MERIDIANO"]["situacao"], "COMPLETO")
        self.assertEqual(m["partes"]["CHECKOUT"]["situacao"], "COMPLETO")

    def test_resultado_dependente_bloqueia_mas_parte_independente_continua(self):
        resultado = executar(self.dados, self.regras)
        self.registrar_bancos(resultado)
        resultado.partes["NOTAS_CHECKOUT"] = ResultadoParte(depende_de=("CHECKOUT",),
            relatorios=("notas_a_emitir.csv",), implementado=True, situacao="COMPLETO")
        resultado.rastro[0]["valor"] = "9.99"
        m = publicar(resultado, self.saida, "alvo")
        self.assertEqual(m["partes"]["NOTAS_CHECKOUT"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["partes"]["EXTRATO_MERIDIANO"]["situacao"], "COMPLETO")
        self.assertEqual(len(self.ler("lancamentos_classificados.csv")), 2)

    def test_conflito_de_ids_bloqueia_produtores_e_nao_checkout(self):
        resultado = executar(self.dados, self.regras)
        self.registrar_bancos(resultado)
        a, b = resultado.partes["EXTRATO_AURORA"], resultado.partes["EXTRATO_MERIDIANO"]
        b.linhas["lancamentos_classificados.csv"][0]["id_saida"] = a.linhas["lancamentos_classificados.csv"][0]["id_saida"]
        b.rastro[0]["id_saida"] = a.rastro[0]["id_saida"]
        m = publicar(resultado, self.saida, "alvo")
        self.assertEqual(m["partes"]["EXTRATO_AURORA"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["partes"]["EXTRATO_MERIDIANO"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["partes"]["CHECKOUT"]["situacao"], "COMPLETO")
        self.assertEqual(self.ler("lancamentos_classificados.csv"), [])

    def test_dependencia_circular_e_ausente_nao_travam_as_demais_partes(self):
        resultado = executar(self.dados, self.regras)
        for nome, dep in (("NOTAS_CHECKOUT", "NOTAS_REMESSA"), ("NOTAS_REMESSA", "NOTAS_CHECKOUT")):
            resultado.partes[nome] = ResultadoParte(depende_de=(dep,), relatorios=("notas_a_emitir.csv",),
                                                   implementado=True, situacao="COMPLETO")
        m = publicar(resultado, self.saida, "alvo")
        self.assertEqual(m["partes"]["NOTAS_CHECKOUT"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["partes"]["NOTAS_REMESSA"]["situacao"], "BLOQUEADO")
        self.assertEqual(m["partes"]["CHECKOUT"]["situacao"], "COMPLETO")

    def test_auditor_rejeita_fechamento_indevidamente_completo(self):
        publicar(executar(self.dados, self.regras), self.saida)
        caminho = self.saida / "manifesto.json"
        m = json.loads(caminho.read_text(encoding="utf-8"))
        m["fechamento"]["situacao"] = "COMPLETO"
        caminho.write_text(json.dumps(m), encoding="utf-8")
        with self.assertRaisesRegex(ErroAceite, "Situação agregada"):
            verificar(self.dados, self.saida, self.regras)

    def test_todos_bloqueados_sem_total_financeiro_zero(self):
        (self.dados / "taxas.xlsx").unlink()
        resultado = executar(self.dados, self.regras)
        m = publicar(resultado, self.saida, "alvo")
        self.assertEqual(m["situacao_comando"], "BLOQUEADO")
        self.assertEqual(m["fechamento"]["situacao"], "BLOQUEADO")
        self.assertIsNone(m["total_parcial_brl"])
        self.assertTrue(all(not self.ler(nome) for nome in m["arquivos"]))
        verificar(self.dados, self.saida, self.regras, "BLOQUEADO", "BLOQUEADO")

    def test_agregacao_completa_parcial_bloqueada(self):
        self.assertEqual(agregar_situacoes(["COMPLETO", "COMPLETO"]), "COMPLETO")
        self.assertEqual(agregar_situacoes(["COMPLETO", "BLOQUEADO"]), "PROVISORIO")
        self.assertEqual(agregar_situacoes(["PROVISORIO", "BLOQUEADO"]), "PROVISORIO")
        self.assertEqual(agregar_situacoes(["BLOQUEADO", "BLOQUEADO"]), "BLOQUEADO")


if __name__ == "__main__":
    unittest.main()
