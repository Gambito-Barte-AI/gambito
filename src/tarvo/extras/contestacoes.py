"""E1: rascunhos determinísticos sobre a projeção validada do alvo, sem I/O."""

from collections import defaultdict
from decimal import Decimal, DecimalException
import re

from ..contratos import ARQUIVOS


REGRAS = {
    "ORBE": (("DIVERGENCIAS_CHECKOUT", "CONTESTACAO_TAXA_ORBE", "CONTESTACAO_ORBE:",
              "DIFERENCA_CONTRATUAL_LIQUIDA", "CHECKOUT"),),
    "PONTE": (("DIVERGENCIAS_REMESSA", "CONTESTACAO_SPREAD_CONTRATUAL", "CONTESTACAO_PONTE:",
               "DIFERENCA_SPREAD_CONTRATUAL", "REMESSA"),
              ("REMESSAS", "CONTESTACAO_SPREAD_NEGATIVO", "SPREAD_NEGATIVO:",
               "DIFERENCA_ATE_CONTRATO", None)),
}


def _exigir(condicao, mensagem):
    if not condicao:
        raise ValueError(mensagem)


def _dinheiro(valor):
    _exigir(isinstance(valor, (str, Decimal)) and
            re.fullmatch(r"-?[0-9]+\.[0-9]{2}", str(valor)), "Valor monetário inválido ou desconhecido")
    return Decimal(valor)


def _texto(valor):
    """Escapa dados de origem para não criar estrutura Markdown ou instruções."""
    return str(valor).replace("\\", "\\\\").replace("\r", " ").replace("\n", " ").translate(
        str.maketrans({c: "\\" + c for c in "`*[]<>|_#"}))


def _hashes(fontes):
    encontrados = {}

    def visitar(item):
        if isinstance(item, dict):
            if item.get("arquivo") and item.get("sha256"):
                arquivo, sha = item["arquivo"], item["sha256"]
                _exigir(isinstance(arquivo, str) and isinstance(sha, str) and
                        re.fullmatch(r"[0-9a-fA-F]{64}", sha), "Identificador/hash de fonte inválido")
                _exigir(arquivo not in encontrados or encontrados[arquivo] == sha.lower(),
                        "Hashes conflitantes para a mesma fonte")
                encontrados[arquivo] = sha.lower()
            for filho in item.values():
                visitar(filho)
        elif isinstance(item, list):
            for filho in item:
                visitar(filho)

    visitar(fontes)
    return encontrados


def _origem(linha, hashes, pendencia):
    arquivo, ref = linha.get("arquivo_origem"), linha.get("ref_origem")
    _exigir(isinstance(arquivo, str) and arquivo and isinstance(ref, str) and ref,
            "Operação sem arquivo ou referência de origem")
    numero = linha.get("linha_origem")
    if not numero and (arquivo, ref) == (pendencia.get("arquivo_origem"), pendencia.get("ref_origem")):
        numero = pendencia.get("linha_origem")
    _exigir(numero in (None, "") or (str(numero).isdigit() and int(numero) > 0), "Linha física inválida")
    origem = dict(arquivo=arquivo, ref=ref, linha=int(numero) if numero else None)
    # O hash da fonte externa é do e-mail, não da aba de um anexo.
    externo = arquivo.split("::", 1)[0]
    if arquivo in hashes or externo in hashes:
        chave = arquivo if arquivo in hashes else externo
        origem.update(arquivo_hash=chave, sha256=hashes[chave])
    return origem


def _grupo(p, natureza, negocio, rastros, divergencias, hashes, competencia):
    ident = p["id_saida"]
    _exigir(re.fullmatch(r"[0-9]{14}", p.get("cnpj", "")), "Pendência sem CNPJ válido")
    if negocio:
        _exigir(ident.split(":")[1] == competencia, "Pendência de outra competência")
    desconhecido = negocio is None and p.get("valor_brl") in (None, "")
    _exigir(p.get("natureza_valor") == ("NAO_INFORMADO" if desconhecido else natureza),
            "Natureza da pendência incompatível")
    valor = None if desconhecido else _dinheiro(p.get("valor_brl"))
    rastro = rastros.get(ident, [])
    _exigir((not rastro) if desconhecido else bool(rastro), "Pendência sem rastro monetário coerente")
    operacoes, vistos, ids_divergencias = [], set(), []
    for r in rastro:
        origem = _origem(r, hashes, p)
        chave = origem["arquivo"], origem["ref"]
        _exigir(chave not in vistos, "Origem repetida na mesma pendência")
        vistos.add(chave)
        quantia = _dinheiro(r.get("valor"))
        operacao = dict(origem=origem, valor_brl=format(quantia, ".2f"))
        if negocio:
            candidatas = divergencias.get((negocio, *chave), [])
            _exigir(len(candidatas) == 1, "Operação sem divergência única correspondente")
            d, detalhe = candidatas[0]
            _exigir(d["id_saida"].startswith(f"DIVERGENCIA:{negocio}:") and
                    d.get("cnpj") == p["cnpj"] and _dinheiro(d.get("diferenca_brl")) == quantia
                    and _dinheiro(detalhe.get("valor")) == quantia,
                    "Divergência e pendência não reconciliam")
            for campo in ("taxa_contratada_pct", "taxa_aplicada_pct"):
                _exigir(isinstance(d.get(campo), (str, Decimal)) and
                        re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", str(d[campo])), "Taxa percentual inválida")
                operacao[campo] = str(d[campo])
            operacao["id_divergencia"] = d["id_saida"]
            ids_divergencias.append(d["id_saida"])
        operacoes.append(operacao)
    if desconhecido:
        operacoes.append(dict(origem=_origem(p, hashes, p), valor_brl=None))
    else:
        _exigir(sum((_dinheiro(o["valor_brl"]) for o in operacoes), Decimal(0)) == valor,
                "Soma do rastro não fecha com a pendência")
    grupo = dict(id_pendencia=ident, cnpj=p["cnpj"], natureza_valor=natureza,
                 valor_brl=format(valor, ".2f") if valor is not None else None,
                 operacoes=sorted(operacoes, key=lambda o: (o["origem"]["arquivo"], o["origem"]["ref"])),
                 ids_divergencias=sorted(ids_divergencias))
    if negocio is None:
        _exigir(len(operacoes) == 1, "Spread negativo exige uma operação por pendência")
        reportado = _dinheiro(p.get("valor_reportado_brl"))
        _exigir(reportado < 0, "Spread reportado deve ser negativo")
        solicitado = None if desconhecido else _dinheiro(p.get("valor_solicitado_brl"))
        _exigir(solicitado == valor, "Pedido D-11 diverge do valor principal")
        if desconhecido:
            _exigir(p.get("valor_solicitado_brl") in (None, ""), "Pedido desconhecido não pode ser estimado")
        grupo.update(valor_reportado_brl=format(reportado, ".2f"),
                     valor_solicitado_brl=format(solicitado, ".2f") if solicitado is not None else None)
    return grupo


def _renderizar(contraparte, competencia, grupos, motivos):
    linhas = [f"# Rascunho de contestação — {contraparte} — {competencia}", "",
              "REVISÃO OBRIGATÓRIA PELO FINANCEIRO. Documento não enviado; não autoriza pagamento.", "",
              "Valores assinados em BRL, copiados dos resultados validados. Diferenças negativas e saldos zero exigem decisão caso a caso."]
    if motivos:
        linhas += ["", "LIMITAÇÃO: subconjunto disponível; não tratar como contestação definitiva."]
        linhas += ["- " + _texto(m) for m in sorted(set(motivos))]
    for negativos, titulo in ((False, "Diferenças contratuais líquidas"), (True, "Spreads negativos — RN-35 / D-11")):
        selecionados = [g for g in grupos if ("valor_reportado_brl" in g) == negativos]
        if not selecionados:
            continue
        linhas += ["", "## " + titulo]
        for g in selecionados:
            linhas += ["", f"CNPJ: {g['cnpj']} | Pendência: {_texto(g['id_pendencia'])}"]
            if negativos:
                pedido = (g["valor_solicitado_brl"] + " BRL" if g["valor_solicitado_brl"] is not None
                          else "NÃO INFORMADO — aguarda contrato/dados, sem estimativa")
                linhas += [f"Reportado no relatório: {g['valor_reportado_brl']} BRL; solicitado até o contrato: {pedido}."]
            else:
                linhas += [f"Diferença líquida validada: {g['valor_brl']} BRL."]
            for o in g["operacoes"]:
                origem = o["origem"]
                local = f"{origem['arquivo']} | {origem['ref']}"
                if origem["linha"]:
                    local += f" | L{origem['linha']}"
                valor = o["valor_brl"] if o["valor_brl"] is not None else "NÃO INFORMADO"
                texto = f"- {_texto(local)}: {valor} BRL"
                if "id_divergencia" in o:
                    texto += (f"; contratada {o['taxa_contratada_pct']}%; aplicada {o['taxa_aplicada_pct']}%"
                              f"; divergência {_texto(o['id_divergencia'])}")
                linhas.append(texto)
        conhecidos = [g["valor_brl"] for g in selecionados if g["valor_brl"] is not None]
        total = sum((_dinheiro(v) for v in conhecidos), Decimal(0))
        parcial = len(conhecidos) != len(selecionados)
        rotulo = "Subtotal conhecido" if parcial else "Total assinado"
        linhas += [f"{rotulo} desta natureza: {total:.2f} BRL." if conhecidos else "Total desta natureza: NÃO INFORMADO."]
    linhas += ["", "Não somar estas naturezas como comissão ou nota. Não executar cobrança automaticamente.",
               "Casa/concessões, cadastro e acompanhamento de TED estão fora deste rascunho.",
               "D-10 confirmada: ajuste abate 50% do spread uma vez; ajustes não integram esta contestação."]
    return "\n".join(linhas) + "\n"


def construir_contestacoes(visao, config):
    """Contrato E0 v1. Retorna diagnósticos locais; não altera entradas nem publica."""
    pacote = dict(versao=1, recurso="contestacoes", situacao="BLOQUEADO", motivos=[], registros=[])
    try:
        _exigir(isinstance(config, dict) and not config, "E1 aceita seção de configuração vazia; não define parâmetros financeiros")
        _exigir(isinstance(visao, dict) and type(visao.get("versao")) is int and visao["versao"] == 1,
                "Versão da visão não suportada")
        competencia = visao.get("competencia")
        _exigir(isinstance(competencia, str) and re.fullmatch(r"[0-9]{4}-(?:0[1-9]|1[0-2])", competencia),
                "Competência não determinada ou inválida")
        relatorios, partes = visao["relatorios"], visao["partes"]
        _exigir(isinstance(relatorios, dict) and set(ARQUIVOS).issubset(relatorios) and
                all(isinstance(relatorios[n], list) for n in ARQUIVOS) and isinstance(partes, dict),
                "Projeção deve conter os seis relatórios e os estados das partes")
        _exigir(isinstance(visao["fontes"], dict), "Fontes da projeção devem ser um mapa")
        hashes = _hashes(visao["fontes"])
        ids = set()
        for nome in ARQUIVOS:
            if nome == "rastro.csv":
                continue
            for linha in relatorios[nome]:
                ident = linha["id_saida"]
                _exigir(isinstance(ident, str) and ident and ident not in ids, "ID de saída ausente ou duplicado na projeção")
                ids.add(ident)
        rastros = defaultdict(list)
        for linha in relatorios["rastro.csv"]:
            rastros[linha["id_saida"]].append(linha)
        divergencias = defaultdict(list)
        for d in relatorios["divergencias_taxa.csv"]:
            # A origem exata vem do rastro, não do ref isolado entre arquivos.
            for r in rastros[d["id_saida"]]:
                divergencias[d["linha_negocio"], r["arquivo_origem"], r["ref_origem"]].append((d, r))
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        pacote["motivos"] = [f"Visão/configuração rejeitada: {exc}"]
        return pacote

    disponiveis = 0
    for contraparte, regras in REGRAS.items():
        motivos, grupos, origens_vistas = [], [], set()
        partes_disponiveis = 0
        try:
            for parte, tipo, prefixo, natureza, negocio in regras:
                estado = partes.get(parte, {})
                if estado.get("validado") is not True or estado.get("situacao") not in {"COMPLETO", "PROVISORIO"}:
                    motivos.append(f"{parte}: bloqueado ou não validado; nenhum valor dessa parte utilizado")
                    continue
                partes_disponiveis += 1
                if estado["situacao"] == "PROVISORIO":
                    motivos.append(f"{parte}: provisório; operações ainda não resolvidas")
                for p in sorted(relatorios["pendencias.csv"], key=lambda p: p["id_saida"]):
                    if p.get("tipo") != tipo:
                        continue
                    _exigir(p["id_saida"].startswith(prefixo), "Produtor da pendência incompatível com seu tipo")
                    g = _grupo(p, natureza, negocio, rastros, divergencias, hashes, competencia)
                    for o in g["operacoes"]:
                        chave = o["origem"]["arquivo"], o["origem"]["ref"]
                        _exigir(chave not in origens_vistas, "Operação cobrada em mais de uma pendência da contraparte")
                        origens_vistas.add(chave)
                    if g["valor_brl"] is None:
                        motivos.append(f"{p['id_saida']}: pedido desconhecido, somente valor reportado disponível")
                    grupos.append(g)
            if grupos:
                origens = [o["origem"] for g in grupos for o in g["operacoes"]]
                pacote["registros"].append(dict(id=f"CONTESTACAO:{contraparte}:{competencia}",
                    contraparte=contraparte, origens=sorted(origens, key=lambda o: (o["arquivo"], o["ref"])),
                    ids_pendencias=sorted(g["id_pendencia"] for g in grupos),
                    ids_divergencias=sorted(d for g in grupos for d in g["ids_divergencias"]),
                    grupos=grupos, texto=_renderizar(contraparte, competencia, grupos, motivos)))
            disponiveis += partes_disponiveis
        except (ValueError, KeyError, TypeError, AttributeError, IndexError, DecimalException) as exc:
            motivos.append(f"{contraparte}: rascunho rejeitado por inconsistência: {exc}")
        pacote["motivos"].extend(motivos)
    pacote["motivos"] = sorted(set(pacote["motivos"]))
    pacote["situacao"] = ("PARCIAL" if disponiveis else "BLOQUEADO") if pacote["motivos"] else "COMPLETO"
    return pacote
