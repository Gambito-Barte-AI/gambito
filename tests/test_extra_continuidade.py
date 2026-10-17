"""E2: continuidade sem faturamento, sem entradas oficiais e sem alterar o alvo."""

from copy import deepcopy
from dataclasses import replace
from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cenarios_a7 import criar
from tarvo.execucao import executar
from tarvo.exportacao import publicar
from tarvo.extras.continuidade import exportar_pendencias, ler_pendencias
from tarvo.modelos import ErroEntrada, Evento, Origem, Pendencia, Resultado, ResultadoParte
from tarvo.partes import projetar_pendencias
from validar_saida import verificar


def evento(ref="V-OUTRO", tipo="VENDA", referencia="", arquivo="lote_novo.csv", linha=2, valor="100.00"):
    return Evento(Origem(arquivo, ref, linha), date(2034, 11, 10), "EC-NOVO", tipo, "PIX", 1,
        Decimal(valor), referencia, date(2034, 11, 9) if referencia else None,
        Decimal("2.35"), Decimal("2.3500"))


def resultado(eventos=None, pendentes=None):
    eventos = [evento()] if eventos is None else eventos
    pendentes = eventos if pendentes is None else pendentes
    r = Resultado(competencia="2034-11", eventos=eventos,
        pendencias=[Pendencia(e.origem, "Contrato aguarda aprovação", "Comercial",
            valor_bruto=e.bruto, cnpj="11111111000111", tipo="CONTRATO_PENDENTE",
            categoria="NEGOCIO", proximo_passo="Comercial deve confirmar condição e vigência.") for e in pendentes])
    r.fontes = {"orbe": {"arquivos": [dict(arquivo=a, sha256="a" * 64) for a in sorted({e.origem.arquivo for e in eventos})]}}
    linhas, rastro = projetar_pendencias(r)
    r.partes["PENDENCIAS_CHECKOUT"] = ResultadoParte(validado=True, situacao="COMPLETO",
        linhas={"pendencias.csv": linhas}, rastro=rastro)
    return r


def resselar(p):
    p.pop("sha256_conteudo", None)
    texto = json.dumps(p, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    p["sha256_conteudo"] = sha256(texto.encode("utf-8")).hexdigest()
    return p


class ContinuidadeTest(unittest.TestCase):
    def test_roundtrip_json_preserva_evento_completo_e_precisao(self):
        r = resultado(); p = exportar_pendencias(r, {})
        self.assertEqual(p["situacao"], "COMPLETO")
        self.assertEqual(ler_pendencias(json.dumps(p)), p)
        registro = p["registros"][0]
        self.assertEqual(registro["evento"]["bruto"], "100.00")
        self.assertEqual(registro["evento"]["taxa_aplicada_pct"], "2.3500")
        self.assertEqual(registro["origens"][0]["sha256"], "a" * 64)
        self.assertEqual(registro["competencia_origem"], "2034-11")
        self.assertEqual(registro["tipo"], "CONTRATO_PENDENTE")
        self.assertEqual(registro["natureza_valor"], "BRUTO_REFERENCIA")
        self.assertEqual(registro["valor_pendencia_brl"], "100.00")
        self.assertFalse(p["faturamento_habilitado"])
        self.assertTrue(any("D-10" in m for m in p["limitacoes_financeiras"]))

    def test_reversao_preserva_antecipacao_como_contexto_nao_faturavel(self):
        original = evento("AN-NOVA", "ANTECIPACAO")
        reversao = evento("RV-NOVA", "REVERSAO ANTECIPACAO", "AN-NOVA", linha=3, valor="-100.00")
        r = resultado([original, reversao], [reversao])
        p = ler_pendencias(exportar_pendencias(r, {}))
        g = p["registros"][0]
        self.assertEqual(p["cobertura"]["exportadas"], 1)
        self.assertEqual(g["contextos"][0]["papel"], "CONTEXTO_NAO_FATURAVEL")
        self.assertEqual(g["contextos"][0]["evento"]["origem"]["ref"], "AN-NOVA")
        self.assertEqual(g["referencias_necessarias"][0]["estado"], "DISPONIVEL")

    def test_estorno_preserva_venda_original_e_data_anterior_sem_reabrir_mes(self):
        venda = replace(evento(), data=date(2034, 10, 30))
        estorno = replace(evento("EST", "ESTORNO", venda.origem.ref, linha=3, valor="-10.00"), data_original=venda.data)
        p = ler_pendencias(exportar_pendencias(resultado([venda, estorno], [estorno]), {}))
        self.assertEqual(p["situacao"], "COMPLETO")
        self.assertEqual(p["registros"][0]["competencia_origem"], "2034-11")
        self.assertEqual(p["registros"][0]["contextos"][0]["evento"]["data"], "2034-10-30")

    def test_referencia_ausente_fica_parcial_sem_reconstrucao(self):
        r = resultado([evento("EST", "ESTORNO", "VENDA-AUSENTE", valor="-10.00")])
        p = ler_pendencias(exportar_pendencias(r, {}))
        self.assertEqual(p["situacao"], "PARCIAL")
        self.assertEqual(p["registros"][0]["contextos"], [])
        self.assertEqual(p["registros"][0]["referencias_necessarias"][0]["estado"], "AUSENTE")

    def test_ciclo_nao_trava_ou_aprova_referencia(self):
        a = evento("A", referencia="B"); b = evento("B", referencia="A", linha=3)
        p = ler_pendencias(exportar_pendencias(resultado([a, b]), {}))
        self.assertEqual(p["situacao"], "PARCIAL")
        self.assertEqual(p["registros"][0]["referencias_necessarias"][-1]["estado"], "CICLICA")

    def test_referencia_ambigua_preserva_candidatas_sem_escolher(self):
        a = evento("ORIGINAL", arquivo="a.csv")
        b = evento("ORIGINAL", arquivo="b.csv", valor="90.00")
        est = evento("EST", "ESTORNO", "ORIGINAL", linha=4, valor="-10.00")
        p = ler_pendencias(exportar_pendencias(resultado([a, b, est], [est]), {}))
        self.assertEqual(p["situacao"], "PARCIAL")
        self.assertEqual(len(p["registros"][0]["contextos"]), 2)
        self.assertEqual(p["registros"][0]["referencias_necessarias"][0]["estado"], "AMBIGUA")

    def test_nao_exporta_evento_principal_conflitante(self):
        a = evento(); b = replace(a, origem=Origem("outro.csv", a.origem.ref, 2), bruto=Decimal("90.00"))
        p = ler_pendencias(exportar_pendencias(resultado([a, b], [a]), {}))
        self.assertEqual(p["situacao"], "BLOQUEADO")
        self.assertEqual(p["cobertura"], dict(pendencias_lidas=1, exportadas=0, nao_exportadas=1))

    def test_sem_normalizado_nao_inventa_evento_e_registra_cobertura(self):
        r = resultado([], [evento()])
        p = ler_pendencias(exportar_pendencias(r, {}))
        self.assertEqual(p["registros"], [])
        self.assertEqual(p["cobertura"]["nao_exportadas"], 1)

    def test_erros_e_valores_desconhecidos_sao_preservados(self):
        e = replace(evento(), valor_taxa=None, taxa_aplicada_pct=None,
            erro_valor_taxa="Campo ausente", erro_taxa_aplicada="Unidade desconhecida")
        p = ler_pendencias(exportar_pendencias(resultado([e]), {}))
        self.assertIsNone(p["registros"][0]["evento"]["valor_taxa"])
        self.assertEqual(p["registros"][0]["evento"]["erro_taxa_aplicada"], "Unidade desconhecida")

    def test_entrada_e_config_nao_mutadas_e_determinismo_por_ordem(self):
        r = resultado([evento("Z"), evento("A", linha=3)])
        antes = deepcopy(r); config = {}
        p = exportar_pendencias(r, config)
        self.assertEqual(r, antes); self.assertEqual(config, {})
        r.eventos.reverse(); r.partes["PENDENCIAS_CHECKOUT"].linhas["pendencias.csv"].reverse()
        self.assertEqual(exportar_pendencias(r, config), p)
        copia = deepcopy(p); self.assertEqual(ler_pendencias(p), copia); self.assertEqual(p, copia)

    def test_sem_pendencias_retorna_pacote_vazio_completo(self):
        p = ler_pendencias(exportar_pendencias(resultado([], []), {}))
        self.assertEqual(p["situacao"], "COMPLETO"); self.assertEqual(p["registros"], [])

    def test_fonte_provisoria_e_bloqueio_da_parte_explicitos(self):
        r = resultado(); r.partes["PENDENCIAS_CHECKOUT"].situacao = "PROVISORIO"
        self.assertEqual(ler_pendencias(exportar_pendencias(r, {}))["situacao"], "PARCIAL")
        r.partes["PENDENCIAS_CHECKOUT"].validado = False
        self.assertEqual(ler_pendencias(exportar_pendencias(r, {}))["situacao"], "BLOQUEADO")

    def test_config_nao_habilita_faturamento(self):
        p = ler_pendencias(exportar_pendencias(resultado(), {"faturar": True}))
        self.assertEqual(p["situacao"], "BLOQUEADO"); self.assertFalse(p["faturamento_habilitado"])

    def test_exportacao_nao_arredonda_dinheiro_mesmo_acima_da_precisao_do_contexto(self):
        for bruto in ("1.001", "123456789012345678901234567890.001"):
            with self.subTest(bruto=bruto):
                r = resultado()
                r.eventos[0] = replace(r.eventos[0], bruto=Decimal(bruto))
                p = ler_pendencias(exportar_pendencias(r, {}))
                self.assertEqual(p["situacao"], "BLOQUEADO")
                self.assertEqual(p["registros"], [])

    def test_hash_detecta_alteracao_do_conteudo(self):
        p = exportar_pendencias(resultado(), {}); p["registros"][0]["evento"]["bruto"] = "9.00"
        with self.assertRaisesRegex(ErroEntrada, "Integridade"):
            ler_pendencias(p)

    def test_rejeita_schema_financeiro_alterado_mesmo_com_hash_atualizado(self):
        alteracoes = (
            lambda p: p.update(versao=True), lambda p: p.update(versao=2),
            lambda p: p.update(faturamento_habilitado=True),
            lambda p: p.update(limitacoes_financeiras=[]),
            lambda p: p["registros"][0].update(competencia_origem="2034-12"),
            lambda p: p["registros"][0].update(id_pendencia="outra"),
            lambda p: p["registros"][0]["evento"].update(bruto=100.0),
            lambda p: p["registros"][0]["evento"].update(bruto="100.001"),
            lambda p: p["registros"][0]["evento"].update(data="2034-02-30"),
            lambda p: p["registros"][0]["evento"].update(parcelas=True),
            lambda p: p["registros"][0].update(natureza_valor="COMISSAO"),
            lambda p: p["registros"][0]["origens"][0].update(sha256="b" * 64),
            lambda p: p["registros"].append(deepcopy(p["registros"][0])),
            lambda p: p["cobertura"].update(pendencias_lidas=99),
        )
        for alterar in alteracoes:
            with self.subTest(alterar=alterar):
                p = exportar_pendencias(resultado(), {}); alterar(p)
                with self.assertRaises(ErroEntrada):
                    ler_pendencias(resselar(p))

    def test_contexto_nao_pode_virar_faturavel_ou_ser_omitido(self):
        a = evento(); est = evento("EST", "ESTORNO", a.origem.ref, linha=3, valor="-10.00")
        original = exportar_pendencias(resultado([a, est]), {})
        p = deepcopy(original)
        next(g for g in p["registros"] if g["contextos"])["contextos"][0]["papel"] = "FATURAR"
        with self.assertRaises(ErroEntrada):ler_pendencias(resselar(p))
        p = deepcopy(original); g = next(g for g in p["registros"] if g["contextos"])
        g["contextos"] = []; g["referencias_necessarias"][0].update(estado="AUSENTE")
        g["referencias_necessarias"][0].pop("origem")
        g["origens"] = [o for o in g["origens"] if o["ref"] == g["evento"]["origem"]["ref"]]
        p["situacao"] = "PARCIAL"; p["motivos"] = ["Referência ausente"]
        with self.assertRaisesRegex(ErroEntrada, "outro registro"):
            ler_pendencias(resselar(p))

    def test_json_duplicado_truncado_ou_caminho_nao_e_aberto(self):
        for doc in ('{"versao":1,"versao":1}', '{', 'pasta/continuidade.json', [], None):
            with self.subTest(doc=doc), self.assertRaises(ErroEntrada):
                ler_pendencias(doc)

    def test_evento_sem_cnpj_preserva_identidade_desconhecida(self):
        r = resultado(); r.partes["PENDENCIAS_CHECKOUT"].linhas["pendencias.csv"][0]["cnpj"] = ""
        self.assertIsNone(ler_pendencias(exportar_pendencias(r, {}))["registros"][0]["cnpj"])

    def test_pacote_de_outro_mes_pode_ser_lido_sem_modificar_fechamento(self):
        with TemporaryDirectory() as tmp:
            raiz = Path(tmp); dados, regras = criar(raiz)
            r = executar(dados, regras); saida = raiz / "saida"
            publicar(r, saida, "alvo"); verificar(dados, saida, regras)
            antes = {p: p.read_bytes() for p in [*dados.iterdir(), *saida.iterdir(), regras] if p.is_file()}
            p = exportar_pendencias(r, {})
            self.assertEqual(p["situacao"], "COMPLETO")
            self.assertEqual(len(p["registros"]), 1)
            self.assertEqual(p["registros"][0]["competencia_origem"], "2032-10")
            # Consumidor do mês seguinte lê o mesmo conteúdo, sem relabelar nem faturar.
            recebido = ler_pendencias(json.dumps(p).encode("utf-8"))
            self.assertEqual(recebido, p); self.assertFalse(recebido["faturamento_habilitado"])
            self.assertEqual({p: p.read_bytes() for p in antes}, antes)
            verificar(dados, saida, regras)


if __name__ == "__main__":
    unittest.main()
