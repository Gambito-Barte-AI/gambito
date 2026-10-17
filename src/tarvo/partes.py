"""Dependências explícitas e isolamento dos resultados, sem cálculos do alvo."""

from collections import defaultdict
from decimal import Decimal, DecimalException

from . import validacao
from .modelos import ErroEntrada, Resultado, ResultadoParte

# (fontes, resultados anteriores, relatórios). Leitores futuros não são presumidos válidos.
PLANO = {
    "CHECKOUT": (("orbe", "taxas", "regras"), (), ("comissoes_por_lojista.csv",)),
    "PENDENCIAS_CHECKOUT": (("orbe", "taxas", "regras"), (), ("pendencias.csv",)),
    "REMESSAS": (("ponte", "regras"), (), ("comissoes_por_lojista.csv", "pendencias.csv")),
    "DIVERGENCIAS_CHECKOUT": (("orbe", "taxas", "regras"), (), ("divergencias_taxa.csv", "pendencias.csv")),
    "DIVERGENCIAS_REMESSA": (("ponte", "taxas", "regras"), (), ("divergencias_taxa.csv", "pendencias.csv")),
    "NOTAS_CHECKOUT": ((), ("CHECKOUT",), ("notas_a_emitir.csv", "pendencias.csv")),
    "NOTAS_REMESSA": ((), ("REMESSAS",), ("notas_a_emitir.csv", "pendencias.csv")),
    "EXTRATO_AURORA": (("aurora", "plano_contas", "regras"), (), ("lancamentos_classificados.csv", "pendencias.csv")),
    "EXTRATO_MERIDIANO": (("meridiano", "plano_contas", "regras"), (), ("lancamentos_classificados.csv", "pendencias.csv")),
}
MINIMO = ("CHECKOUT", "PENDENCIAS_CHECKOUT")


def agregar_situacoes(situacoes):
    estados = list(situacoes)
    if not estados or all(e == "BLOQUEADO" for e in estados):
        return "BLOQUEADO"
    return "COMPLETO" if all(e == "COMPLETO" for e in estados) else "PROVISORIO"


def selecionar(resultado: Resultado, escopo: str):
    if escopo not in {"checkout", "alvo"}:
        raise ErroEntrada("Escopo deve ser checkout ou alvo")
    return list(MINIMO) if escopo == "checkout" else list(resultado.partes)


def projetar_pendencias(resultado: Resultado) -> tuple[list[dict], list[dict]]:
    """Publica somente pendências existentes; valores de referência não são comissões."""
    linhas, rastros = [], []
    for p in sorted(resultado.pendencias, key=lambda p: (p.origem.arquivo, p.origem.linha, p.origem.ref)):
        identificador = f"PENDENCIA:{p.origem.arquivo}:L{p.origem.linha}:{p.origem.ref}"
        valor = p.valor_orbe if p.valor_orbe is not None else p.valor_bruto
        natureza = "COBRANCA_ORBE" if p.valor_orbe is not None else "BRUTO_REFERENCIA" if valor is not None else "NAO_INFORMADO"
        if valor is not None and (not valor.is_finite() or valor != valor.quantize(Decimal("0.01"))):
            raise ErroEntrada("Pendência com valor não finito ou fração de centavo")
        linhas.append({
            "id_saida": identificador, "tipo": p.tipo, "ref_origem": p.origem.ref,
            "valor_brl": format(valor, ".2f") if valor is not None else "",
            "motivo": p.motivo, "quem_decide": p.quem_decide, "proximo_passo": p.proximo_passo,
            "arquivo_origem": p.origem.arquivo, "linha_origem": p.origem.linha,
            "cnpj": p.cnpj or "", "categoria": p.categoria, "natureza_valor": natureza,
        })
        if valor is not None:
            rastros.append({"id_saida": identificador, "arquivo_origem": p.origem.arquivo,
                            "ref_origem": p.origem.ref, "valor": format(valor, ".2f"),
                            "natureza_valor": natureza})
    return linhas, rastros



def preparar_partes(resultado: Resultado) -> None:
    """Adapta o contrato legado de checkout e revalida antes de cada publicação."""
    c = {"linhas_lidas": resultado.linhas_lidas, "calculadas": len(resultado.contribuicoes),
         "pendentes": len(resultado.pendencias),
         "bloqueadas": resultado.linhas_lidas - len(resultado.contribuicoes) - len(resultado.pendencias)}
    fontes, depende_de, relatorios = PLANO["CHECKOUT"]
    resultado.partes["CHECKOUT"] = ResultadoParte(
        fontes=fontes, depende_de=depende_de, relatorios=relatorios, implementado=True,
        situacao=resultado.situacao, motivos=list(resultado.motivos),
        linhas={"comissoes_por_lojista.csv": resultado.comissoes}, rastro=resultado.rastro, cobertura=c,
    )
    fontes, depende_de, relatorios = PLANO["PENDENCIAS_CHECKOUT"]
    avaliado = resultado.calculo_executado or resultado.validado
    pendencias = ResultadoParte(fontes=fontes, depende_de=depende_de, relatorios=relatorios,
                               implementado=True, situacao="COMPLETO" if avaliado else "BLOQUEADO",
                               motivos=[] if avaliado else ["Identificação das pendências de checkout não concluída"])
    if avaliado:
        try:
            linhas, rastro = projetar_pendencias(resultado)
            pendencias.linhas = {"pendencias.csv": linhas}
            pendencias.rastro = rastro
            pendencias.cobertura = {"linhas_lidas": len(linhas), "calculadas": 0,
                                   "pendentes": len(linhas), "bloqueadas": 0}
            if resultado.avisos or any(p.categoria == "DADOS" for p in resultado.pendencias):
                pendencias.situacao = "PROVISORIO"
                pendencias.motivos = ["Há linhas de dados pendentes ou avisos nas fontes"]
        except (ErroEntrada, ValueError, DecimalException) as exc:
            pendencias.situacao = "BLOQUEADO"
            pendencias.motivos = [f"Falha ao preparar pendências: {exc}"]
    resultado.partes["PENDENCIAS_CHECKOUT"] = pendencias
    for nome, (fontes, anteriores, relatorios) in PLANO.items():
        resultado.partes.setdefault(nome, ResultadoParte(
            fontes=fontes, depende_de=anteriores, relatorios=relatorios,
            motivos=[f"{nome}: etapa não implementada; nenhum valor calculado"],
        ))
    validar_partes(resultado)


def validar_partes(resultado: Resultado) -> None:
    """Uma falha de uma parte bloqueia seus dependentes, nunca suas irmãs."""
    resolvidos, visitando = set(), set()

    def avaliar(nome):
        parte = resultado.partes[nome]
        if nome in resolvidos:
            return
        parte.validado = False
        if nome in visitando:
            parte.situacao = "BLOQUEADO"
            parte.motivos = ["Dependência circular entre resultados"]
            return
        visitando.add(nome)
        problemas = []
        provisorio = False
        if parte.situacao not in {"COMPLETO", "PROVISORIO", "BLOQUEADO"}:
            problemas.append("Situação de resultado inválida")
        for anterior in parte.depende_de:
            if anterior not in resultado.partes:
                problemas.append(f"Resultado requerido não registrado: {anterior}")
                continue
            avaliar(anterior)
            dependencia = resultado.partes[anterior]
            if not dependencia.validado or dependencia.situacao == "BLOQUEADO":
                problemas.append(f"Resultado requerido bloqueado: {anterior}")
            provisorio |= dependencia.situacao == "PROVISORIO"
        for fonte in parte.fontes:
            estado = resultado.fontes.get(fonte, {}).get("situacao", "NAO_AVALIADA")
            if estado not in {"DISPONIVEL", "PROVISORIO"}:
                motivo = resultado.fontes.get(fonte, {}).get("motivo", "fonte não avaliada nesta etapa")
                problemas.append(f"Dependência {fonte}: {estado}; {motivo}")
            provisorio |= estado == "PROVISORIO"
        if not parte.implementado:
            problemas.insert(0, f"{nome}: etapa não implementada; nenhum valor calculado")
        if problemas:
            parte.situacao = "BLOQUEADO"
            parte.motivos = list(dict.fromkeys(parte.motivos + problemas))
        elif parte.situacao != "BLOQUEADO":
            try:
                if nome == "CHECKOUT":
                    validacao.validar(resultado)
                validacao.validar_parte(parte)
                if provisorio:
                    parte.situacao = "PROVISORIO"
                    parte.motivos.append("Há dependência provisória")
            except (ErroEntrada, KeyError, TypeError, ValueError, DecimalException) as exc:
                parte.situacao = "BLOQUEADO"
                parte.validado = False
                parte.motivos = [f"Falha de validação em {nome}: {exc}"]
        if nome == "CHECKOUT":
            resultado.situacao = parte.situacao
            resultado.validado = parte.validado
            resultado.motivos = list(parte.motivos)
        parte.motivos = list(dict.fromkeys(parte.motivos))
        visitando.remove(nome)
        resolvidos.add(nome)

    for nome in resultado.partes:
        avaliar(nome)
    # Um ID compartilhado entre partes faria o rastro se misturar. Bloqueia os produtores envolvidos.
    produtores = defaultdict(set)
    for nome, parte in resultado.partes.items():
        if parte.validado:
            for linhas in parte.linhas.values():
                for linha in linhas:
                    produtores[linha["id_saida"]].add(nome)
    conflitos = {nome for nomes in produtores.values() if len(nomes) > 1 for nome in nomes}
    if conflitos:
        for nome in conflitos:
            parte = resultado.partes[nome]
            parte.situacao, parte.validado = "BLOQUEADO", False
            parte.motivos = ["ID de saída repetido entre partes; rastro ambíguo"]
        # Propaga apenas por dependências de resultados, preservando partes independentes.
        for _ in resultado.partes:
            alterou = False
            for nome, parte in resultado.partes.items():
                if parte.validado and any(not resultado.partes[d].validado for d in parte.depende_de):
                    parte.situacao, parte.validado = "BLOQUEADO", False
                    parte.motivos = ["Resultado requerido bloqueado por conflito de IDs"]
                    alterou = True
            if not alterou:
                break
        checkout = resultado.partes["CHECKOUT"]
        resultado.situacao, resultado.validado = checkout.situacao, checkout.validado
        resultado.motivos = list(checkout.motivos)
