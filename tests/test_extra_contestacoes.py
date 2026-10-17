"""E1: contratos, separação de naturezas e regressão sem depender do pack oficial."""

from copy import deepcopy
import csv
from decimal import Decimal
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cenarios_a7 import criar
from tarvo.contratos import ARQUIVOS
from tarvo.execucao import executar
from tarvo.exportacao import publicar
from tarvo.extras.contestacoes import construir_contestacoes
from validar_saida import verificar


def visao_vazia():
    return dict(versao=1, competencia="2035-04", fontes={"orbe": {"arquivos": [
        dict(arquivo="outro.csv", sha256="a" * 64)]}},
        partes={p: dict(situacao="COMPLETO", validado=True, motivos=[])
                for p in ("DIVERGENCIAS_CHECKOUT", "DIVERGENCIAS_REMESSA", "REMESSAS")},
        relatorios={n: [] for n in ARQUIVOS})


def adicionar(v, contraparte, ref, valor, cnpj="11111111000111", arquivo="outro.csv", linha=10):
    negocio = "CHECKOUT" if contraparte == "ORBE" else "REMESSA"
    tipo = "CONTESTACAO_TAXA_ORBE" if contraparte == "ORBE" else "CONTESTACAO_SPREAD_CONTRATUAL"
    natureza = "DIFERENCA_CONTRATUAL_LIQUIDA" if contraparte == "ORBE" else "DIFERENCA_SPREAD_CONTRATUAL"
    ident = f"CONTESTACAO_{contraparte}:{v['competencia']}:{cnpj}"
    rel = v["relatorios"]
    if not any(p["id_saida"] == ident for p in rel["pendencias.csv"]):
        rel["pendencias.csv"].append(dict(id_saida=ident, tipo=tipo, cnpj=cnpj, valor_brl="0.00",
            natureza_valor=natureza, arquivo_origem=arquivo, ref_origem=ref, linha_origem=str(linha)))
    p = next(p for p in rel["pendencias.csv"] if p["id_saida"] == ident)
    p["valor_brl"] = format(Decimal(p["valor_brl"]) + Decimal(valor), ".2f")
    div = f"DIVERGENCIA:{negocio}:{arquivo}:{ref}"
    rel["divergencias_taxa.csv"].append(dict(id_saida=div, cnpj=cnpj, linha_negocio=negocio,
        ref_origem=ref, diferenca_brl=valor, taxa_contratada_pct="1.2", taxa_aplicada_pct="1.5"))
    for destino in (ident, div):
        rel["rastro.csv"].append(dict(id_saida=destino, arquivo_origem=arquivo, ref_origem=ref,
                                      linha_origem=str(linha), valor=valor))


def negativo(v, ref="PC-NOVA", reportado="-12.00", solicitado="-17.25"):
    ident = f"SPREAD_NEGATIVO:outro.csv:L50:{ref}"
    p = dict(id_saida=ident, tipo="CONTESTACAO_SPREAD_NEGATIVO", cnpj="22222222000122",
        valor_brl=solicitado, valor_reportado_brl=reportado, valor_solicitado_brl=solicitado,
        natureza_valor="DIFERENCA_ATE_CONTRATO" if solicitado else "NAO_INFORMADO",
        arquivo_origem="outro.csv", ref_origem=ref, linha_origem="50")
    v["relatorios"]["pendencias.csv"].append(p)
    if solicitado:
        v["relatorios"]["rastro.csv"].append(dict(id_saida=ident, arquivo_origem="outro.csv",
            ref_origem=ref, linha_origem="50", valor=solicitado))
    return p


class ContestacoesTest(unittest.TestCase):
    def test_venda_estorno_saldo_assinado_e_rastro_sem_somar_divergencia_duas_vezes(self):
        v = visao_vazia()
        adicionar(v, "ORBE", "VENDA-NOVA", "12.35")
        adicionar(v, "ORBE", "ESTORNO-NOVO", "-2.25", linha=11)
        p = construir_contestacoes(v, {})
        self.assertEqual(p["situacao"], "COMPLETO")
        r = p["registros"][0]
        self.assertEqual(r["grupos"][0]["valor_brl"], "10.10")
        self.assertIn("Total assinado desta natureza: 10.10 BRL", r["texto"])
        self.assertIn("-2.25 BRL", r["texto"])
        self.assertEqual(len(r["ids_divergencias"]), 2)
        self.assertTrue(all(o["sha256"] == "a" * 64 for o in r["origens"]))

    def test_ponte_separa_diferenca_contratual_reportado_e_pedido(self):
        v = visao_vazia(); adicionar(v, "PONTE", "PC-CONTRATO", "4.56"); negativo(v)
        r = construir_contestacoes(v, {})["registros"][0]
        self.assertEqual(r["contraparte"], "PONTE")
        self.assertIn("4.56 BRL", r["texto"])
        self.assertIn("Reportado no relatório: -12.00 BRL; solicitado até o contrato: -17.25", r["texto"])
        self.assertNotIn("-12.69", r["texto"])
        self.assertIn("D-10 continua pendente", r["texto"])

    def test_naturezas_nao_cobraveis_nao_entram(self):
        v = visao_vazia()
        for i, tipo in enumerate(("DEVOLUCAO_LOJISTA", "ACOMPANHAMENTO_REPASSE_PONTE",
                "AJUSTE_PONTE_D10_PENDENTE", "CADASTRO_REMESSA_PENDENTE", "CONTRATO_PENDENTE")):
            v["relatorios"]["pendencias.csv"].append(dict(id_saida=f"IGNORADO:{i}", tipo=tipo))
        self.assertEqual(construir_contestacoes(v, {})["registros"], [])

    def test_sem_casos_nao_cria_rascunho(self):
        self.assertEqual(construir_contestacoes(visao_vazia(), {}),
            dict(versao=1, recurso="contestacoes", situacao="COMPLETO", motivos=[], registros=[]))

    def test_determinismo_entrada_somente_leitura_e_serializacao(self):
        v = visao_vazia(); adicionar(v, "ORBE", "B", "1.11"); adicionar(v, "ORBE", "A", "-0.10")
        antes = deepcopy(v); config = {}
        p = construir_contestacoes(v, config)
        self.assertEqual(v, antes); self.assertEqual(config, {})
        for linhas in v["relatorios"].values():
            linhas.reverse()
        self.assertEqual(construir_contestacoes(v, config), p)
        self.assertEqual(json.loads(json.dumps(p)), p)

    def test_bloqueio_orbe_preserva_ponte(self):
        v = visao_vazia(); adicionar(v, "ORBE", "V", "1.00"); negativo(v)
        v["partes"]["DIVERGENCIAS_CHECKOUT"].update(situacao="BLOQUEADO", validado=False)
        p = construir_contestacoes(v, {})
        self.assertEqual(p["situacao"], "PARCIAL")
        self.assertEqual([r["contraparte"] for r in p["registros"]], ["PONTE"])

    def test_ponte_parcial_se_divergencia_bloqueada_e_negativos_validos(self):
        v = visao_vazia(); negativo(v)
        v["partes"]["DIVERGENCIAS_REMESSA"].update(situacao="BLOQUEADO", validado=False)
        r = construir_contestacoes(v, {})["registros"][0]
        self.assertIn("LIMITAÇÃO", r["texto"])
        self.assertIn("nenhum valor dessa parte utilizado", r["texto"])

    def test_fonte_provisoria_marca_texto_como_subconjunto(self):
        v = visao_vazia(); adicionar(v, "ORBE", "V", "1.00")
        v["partes"]["DIVERGENCIAS_CHECKOUT"]["situacao"] = "PROVISORIO"
        p = construir_contestacoes(v, {})
        self.assertEqual(p["situacao"], "PARCIAL")
        self.assertIn("não tratar como contestação definitiva", p["registros"][0]["texto"])

    def test_spread_negativo_desconhecido_nao_inventa_pedido_ou_rastro(self):
        v = visao_vazia(); negativo(v, solicitado="")
        p = construir_contestacoes(v, {})
        self.assertEqual(p["situacao"], "PARCIAL")
        r = p["registros"][0]
        self.assertIsNone(r["grupos"][0]["valor_brl"])
        self.assertIn("NÃO INFORMADO", r["texto"])
        self.assertNotIn("0.00 BRL", r["texto"])

    def test_saldos_negativo_e_zero_nao_viram_cobranca_automatica(self):
        for valor in ("-1.00", "0.00"):
            with self.subTest(valor=valor):
                v = visao_vazia(); adicionar(v, "ORBE", "V", valor)
                texto = construir_contestacoes(v, {})["registros"][0]["texto"]
                self.assertIn(f"{valor} BRL", texto)
                self.assertIn("decisão caso a caso", texto)

    def test_corrupcao_de_uma_contraparte_nao_afeta_a_outra(self):
        for alterar in (
            lambda v: v["relatorios"]["pendencias.csv"][0].update(valor_brl="9.99"),
            lambda v: v["relatorios"]["divergencias_taxa.csv"][0].update(diferenca_brl="9.99"),
            lambda v: v["relatorios"]["rastro.csv"][1].update(valor="9.99"),
            lambda v: v["relatorios"]["rastro.csv"].pop(0),
            lambda v: v["relatorios"]["rastro.csv"].append(deepcopy(v["relatorios"]["rastro.csv"][0])),
            lambda v: v["relatorios"]["pendencias.csv"][0].update(natureza_valor="DEVOLUCAO_LOJISTA"),
            lambda v: v["relatorios"]["pendencias.csv"][0].update(id_saida="CONTESTACAO_ORBE:2030-01:11111111000111"),
        ):
            with self.subTest(alterar=alterar):
                v = visao_vazia(); adicionar(v, "ORBE", "V", "1.00"); negativo(v); alterar(v)
                p = construir_contestacoes(v, {})
                self.assertEqual(p["situacao"], "PARCIAL")
                self.assertEqual([r["contraparte"] for r in p["registros"]], ["PONTE"])

    def test_versao_schema_hash_e_ids_invalidos_bloqueiam(self):
        for alterar in (
            lambda v: v.update(versao=True), lambda v: v.update(versao=2),
            lambda v: v.update(competencia="2035-99"),
            lambda v: v["relatorios"].pop("rastro.csv"),
            lambda v: v["fontes"]["orbe"]["arquivos"][0].update(sha256="invalid"),
            lambda v: v["relatorios"]["pendencias.csv"].append(deepcopy(v["relatorios"]["pendencias.csv"][0])),
        ):
            with self.subTest(alterar=alterar):
                v = visao_vazia(); adicionar(v, "ORBE", "V", "1.00"); alterar(v)
                self.assertEqual(construir_contestacoes(v, {})["situacao"], "BLOQUEADO")

    def test_decimal_invalido_nao_vira_float_ou_estimativa(self):
        for valor in ("1,00", "NaN", "Infinity", "1.001", "", 1.0, None):
            with self.subTest(valor=valor):
                v = visao_vazia(); adicionar(v, "ORBE", "V", "1.00")
                v["relatorios"]["pendencias.csv"][0]["valor_brl"] = valor
                self.assertEqual(construir_contestacoes(v, {})["registros"], [])

    def test_mesmo_ref_em_arquivos_diferentes_e_hash_email_explicito(self):
        v = visao_vazia(); adicionar(v, "ORBE", "V", "1.00")
        arquivo = "email.eml::anexo.xlsx::Dados"
        adicionar(v, "PONTE", "V", "2.00", arquivo=arquivo)
        v["fontes"]["ponte"] = dict(arquivos=[dict(arquivo="email.eml", sha256="b" * 64)])
        p = construir_contestacoes(v, {})
        self.assertEqual(len(p["registros"]), 2)
        o = p["registros"][1]["origens"][0]
        self.assertEqual(o["arquivo"], arquivo); self.assertEqual(o["arquivo_hash"], "email.eml")

    def test_nomes_com_markdown_nao_injetam_bloco_no_rascunho(self):
        v = visao_vazia(); adicionar(v, "ORBE", "[V]\n# título", "1.00")
        texto = construir_contestacoes(v, {})["registros"][0]["texto"]
        self.assertNotIn("\n# título", texto); self.assertIn("\\[V\\]", texto)

    def test_configuracao_nao_autoriza_parametro_financeiro_novo(self):
        self.assertEqual(construir_contestacoes(visao_vazia(), {"taxa": "0.50"})["situacao"], "BLOQUEADO")

    def test_mesma_operacao_nao_pode_entrar_em_dois_grupos_de_cobranca(self):
        v = visao_vazia(); adicionar(v, "ORBE", "V", "1.00")
        outro = deepcopy(v["relatorios"]["pendencias.csv"][0])
        outro["id_saida"] += ":DUPLICADA"
        v["relatorios"]["pendencias.csv"].append(outro)
        rastro = deepcopy(v["relatorios"]["rastro.csv"][0]); rastro["id_saida"] = outro["id_saida"]
        v["relatorios"]["rastro.csv"].append(rastro)
        pacote = construir_contestacoes(v, {})
        self.assertEqual(pacote["registros"], [])
        self.assertTrue(any("mais de uma pendência" in m for m in pacote["motivos"]))

    def test_linha_fisica_desconhecida_nao_e_inventada(self):
        v = visao_vazia(); adicionar(v, "ORBE", "V", "1.00")
        v["relatorios"]["pendencias.csv"][0].pop("linha_origem")
        for r in v["relatorios"]["rastro.csv"]:
            r.pop("linha_origem")
        p = construir_contestacoes(v, {})
        self.assertEqual(p["situacao"], "COMPLETO")
        self.assertIsNone(p["registros"][0]["origens"][0]["linha"])

    def test_spread_negativo_rejeita_pedido_divergente_do_principal(self):
        v = visao_vazia(); p = negativo(v); p["valor_solicitado_brl"] = "-1.00"
        pacote = construir_contestacoes(v, {})
        self.assertEqual(pacote["registros"], [])
        self.assertTrue(any("D-11" in m for m in pacote["motivos"]))

    def test_todas_partes_bloqueadas_nao_produzem_rascunhos(self):
        v = visao_vazia()
        for p in v["partes"].values():
            p.update(situacao="BLOQUEADO", validado=False)
        self.assertEqual(construir_contestacoes(v, {})["situacao"], "BLOQUEADO")

    def test_pacote_outro_mes_com_fechamento_e_auditor_alvo_preservados(self):
        with TemporaryDirectory() as tmp:
            raiz = Path(tmp); dados, regras = criar(raiz)
            resultado = executar(dados, regras); saida = raiz / "saida"
            manifesto = publicar(resultado, saida, "alvo")
            verificar(dados, saida, regras)
            antes = {p: p.read_bytes() for p in [*dados.iterdir(), *saida.iterdir(), regras] if p.is_file()}
            v = dict(versao=1, competencia=manifesto["competencia"], fontes=manifesto["fontes"],
                partes={n: dict(situacao=p["situacao"], validado=p["rastro_validado"], motivos=p["motivos"])
                        for n, p in manifesto["partes"].items()}, relatorios={})
            for n in ARQUIVOS:
                with (saida/n).open(encoding="utf-8", newline="") as f:
                    v["relatorios"][n] = list(csv.DictReader(f, delimiter=";"))
            original = deepcopy(v); pacote = construir_contestacoes(v, {})
            self.assertEqual(pacote["situacao"], "COMPLETO")
            self.assertEqual({r["contraparte"] for r in pacote["registros"]}, {"ORBE", "PONTE"})
            self.assertTrue(all("2032-10" in r["id"] for r in pacote["registros"]))
            self.assertNotIn("AJUSTE_D10:", json.dumps(pacote))
            self.assertEqual(v, original)
            self.assertEqual({p: p.read_bytes() for p in antes}, antes)
            verificar(dados, saida, regras)


if __name__ == "__main__":
    unittest.main()
