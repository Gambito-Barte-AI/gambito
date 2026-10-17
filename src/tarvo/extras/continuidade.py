"""E2: snapshot verificável de pendências Orbe, sem reabrir mês ou faturar."""

from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict, fields
from datetime import date
from decimal import Decimal, DecimalException
from hashlib import sha256
import json
import re

from ..modelos import ErroEntrada, Evento


LIMITACOES = [
    "E2-P: controle de já faturados, aprovação comercial e apresentação da competência original ainda pendentes; faturamento desabilitado.",
    "D-10: natureza do ajuste da Ponte permanece pendente de confirmação financeira; nenhuma regra alterada.",
    "Contrato/vigência precisam de evidência comercial; snapshot e leitura não autorizam cobrança.",
]


def _exigir(condicao, mensagem):
    if not condicao:
        raise ErroEntrada(mensagem)


def _canonico(documento):
    return json.dumps(documento, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _selar(pacote):
    pacote["sha256_conteudo"] = sha256(_canonico(pacote).encode("utf-8")).hexdigest()
    return pacote


def _origem(origem):
    _exigir(isinstance(origem, dict) and set(origem) == {"arquivo", "ref", "linha"}, "Origem incompleta")
    _exigir(all(isinstance(origem[k], str) and origem[k] for k in ("arquivo", "ref")) and
            type(origem["linha"]) is int and origem["linha"] > 0, "Arquivo, referência ou linha inválidos")
    return origem["arquivo"], origem["ref"], origem["linha"]


def _data(texto, opcional=False):
    if texto is None and opcional:
        return None
    _exigir(isinstance(texto, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", texto), "Data deve ser ISO")
    return date.fromisoformat(texto)


def _decimal(texto, dinheiro=False, opcional=False):
    if texto is None and opcional:
        return None
    padrao = r"-?[0-9]+\.[0-9]{2}" if dinheiro else r"-?[0-9]+(?:\.[0-9]+)?"
    _exigir(isinstance(texto, str) and re.fullmatch(padrao, texto), "Decimal inválido; não usar float ou arredondar entrada")
    return Decimal(texto)


def _ler_evento(item):
    _exigir(isinstance(item, dict) and set(item) == {f.name for f in fields(Evento)}, "Campos de Evento incompatíveis")
    _origem(item["origem"])
    for campo in ("ec", "tipo", "modalidade", "referencia", "erro_taxa_aplicada", "erro_valor_taxa"):
        _exigir(isinstance(item[campo], str), f"{campo} deve preservar texto")
    _exigir(item["parcelas"] is None or type(item["parcelas"]) is int, "Parcelas inválidas")
    _data(item["data"]); _data(item["data_original"], opcional=True)
    _decimal(item["bruto"], dinheiro=True)
    _decimal(item["valor_taxa"], dinheiro=True, opcional=True)
    _decimal(item["taxa_aplicada_pct"], opcional=True)
    return item


def _serializar(evento):
    _exigir(isinstance(evento, Evento), "Evento normalizado indisponível")
    item = asdict(evento)
    for campo in ("data", "data_original"):
        valor = item[campo]
        _exigir(valor is None or type(valor) is date, "Data normalizada inválida")
        item[campo] = valor.isoformat() if valor is not None else None
    for campo in ("bruto", "valor_taxa", "taxa_aplicada_pct"):
        valor = item[campo]
        if valor is None:
            continue
        _exigir(isinstance(valor, Decimal) and valor.is_finite(), "Evento contém valor não Decimal/finito")
        texto = format(valor, "f")
        if campo != "taxa_aplicada_pct":
            # Só acrescentar casas, nunca arredondar informação do evento.
            texto = format(valor, ".2f")
            _exigir(Decimal(texto) == valor, "Dinheiro com precisão indevida")
        item[campo] = texto
    return _ler_evento(item)


def _id_pendencia(evento):
    arquivo, ref, linha = _origem(evento["origem"])
    return f"PENDENCIA:{arquivo}:L{linha}:{ref}"


def _vinculos(principal, eventos):
    por_ref = defaultdict(list)
    for evento in eventos:
        por_ref[evento["origem"]["ref"]].append(evento)
    contextos, referencias = {}, []
    atual, visitados = principal, {principal["origem"]["ref"]}
    while atual["referencia"]:
        ref = atual["referencia"]
        ligacao = dict(evento_ref=atual["origem"]["ref"], ref=ref)
        if ref in visitados:
            referencias.append(dict(ligacao, estado="CICLICA")); break
        candidatas = sorted(por_ref[ref], key=lambda e: _origem(e["origem"]))
        if not candidatas:
            referencias.append(dict(ligacao, estado="AUSENTE")); break
        for evento in candidatas:
            contextos[_origem(evento["origem"])] = dict(papel="CONTEXTO_NAO_FATURAVEL", evento=deepcopy(evento))
        if len(candidatas) > 1:
            referencias.append(dict(ligacao, estado="AMBIGUA")); break
        referencias.append(dict(ligacao, estado="DISPONIVEL", origem=deepcopy(candidatas[0]["origem"])))
        atual = candidatas[0]
        visitados.add(ref)
    return [contextos[k] for k in sorted(contextos)], referencias


def _fontes(resultado):
    encontradas = {}
    for nome in ("orbe", "taxas", "regras"):
        fonte = resultado.fontes.get(nome, {})
        itens = fonte.get("arquivos", []) if nome == "orbe" else [fonte]
        for item in itens:
            if "arquivo" not in item or "sha256" not in item:
                continue
            arquivo, valor = item["arquivo"], item["sha256"]
            _exigir(isinstance(arquivo, str) and arquivo and isinstance(valor, str) and
                    re.fullmatch(r"[0-9a-fA-F]{64}", valor), "Fonte/hash inválido")
            _exigir(arquivo not in encontradas or encontradas[arquivo] == valor.lower(), "Hash de fonte conflitante")
            encontradas[arquivo] = valor.lower()
    return [dict(arquivo=k, sha256=v) for k, v in sorted(encontradas.items())]


def _origens(principal, contextos, fontes):
    hashes = {f["arquivo"]: f["sha256"] for f in fontes}
    origens = {_origem(principal["origem"]): deepcopy(principal["origem"])}
    for contexto in contextos:
        e = contexto["evento"]
        origens[_origem(e["origem"])] = deepcopy(e["origem"])
    for origem in origens.values():
        if origem["arquivo"] in hashes:
            origem["sha256"] = hashes[origem["arquivo"]]
    return [origens[k] for k in sorted(origens)]


def exportar_pendencias(resultado, config):
    """Exporta apenas pendências de checkout com Evento recuperável, sem mutação/I/O."""
    pacote = dict(versao=1, recurso="continuidade", situacao="BLOQUEADO", motivos=[], registros=[],
        fontes=[], diagnosticos=[], origem_provisoria=False, faturamento_habilitado=False,
        limitacoes_financeiras=list(LIMITACOES),
        cobertura=dict(pendencias_lidas=0, exportadas=0, nao_exportadas=0))
    try:
        _exigir(isinstance(config, dict) and not config, "E2 aceita configuração vazia; retomada financeira não habilitada")
        parte = resultado.partes.get("PENDENCIAS_CHECKOUT")
        _exigir(parte is not None and parte.validado and parte.situacao in {"COMPLETO", "PROVISORIO"},
                "Pendências de checkout bloqueadas ou não validadas")
        _exigir(isinstance(resultado.competencia, str) and
                re.fullmatch(r"[0-9]{4}-(?:0[1-9]|1[0-2])", resultado.competencia), "Competência de origem inválida")
        pacote["fontes"] = _fontes(resultado)
        pacote["origem_provisoria"] = parte.situacao == "PROVISORIO"
        eventos, por_origem, por_ref = [], defaultdict(list), defaultdict(list)
        for evento in resultado.eventos:
            item = _serializar(evento)
            eventos.append(item); por_origem[_origem(item["origem"])].append(item)
            por_ref[item["origem"]["ref"]].append(item)
        linhas = parte.linhas.get("pendencias.csv", [])
        ids = [p["id_saida"] for p in linhas]
        _exigir(len(ids) == len(set(ids)), "Pendências com IDs duplicados")
        pacote["cobertura"]["pendencias_lidas"] = len(linhas)
        for p in sorted(linhas, key=lambda p: p["id_saida"]):
            try:
                chave = p["arquivo_origem"], p["ref_origem"], int(p["linha_origem"])
                candidatas = por_origem[chave]
                _exigir(len(candidatas) == 1, "Evento normalizado ausente ou origem ambígua; original permanece pendente")
                evento = candidatas[0]
                _exigir(len(por_ref[evento["origem"]["ref"]]) == 1, "ID de transação conflitante; não escolher ocorrência")
                _exigir(_id_pendencia(evento) == p["id_saida"], "Vínculo pendência/evento incompatível")
                _exigir(evento["data"][:7] == resultado.competencia, "Evento fora da competência de origem")
                contexto, referencias = _vinculos(evento, eventos)
                registro = dict(id="CONTINUIDADE:" + p["id_saida"], id_pendencia=p["id_saida"],
                    cnpj=p.get("cnpj") or None, competencia_origem=resultado.competencia,
                    evento=deepcopy(evento), contextos=contexto, referencias_necessarias=referencias,
                    origens=_origens(evento, contexto, pacote["fontes"]),
                    motivo=p["motivo"], quem_decide=p["quem_decide"], proximo_passo=p["proximo_passo"],
                    tipo=p["tipo"], categoria=p["categoria"], natureza_valor=p["natureza_valor"],
                    valor_pendencia_brl=p["valor_brl"] if p["valor_brl"] != "" else None)
                _validar_registro(registro, pacote["fontes"])
                pacote["registros"].append(registro)
            except (ErroEntrada, ValueError, KeyError, TypeError, DecimalException) as exc:
                pacote["diagnosticos"].append(dict(id_pendencia=p["id_saida"], motivo=str(exc)))
        pacote["cobertura"].update(exportadas=len(pacote["registros"]), nao_exportadas=len(pacote["diagnosticos"]))
        problemas = any(r["estado"] != "DISPONIVEL" for g in pacote["registros"] for r in g["referencias_necessarias"])
        if pacote["diagnosticos"] or pacote["origem_provisoria"] or problemas:
            pacote["situacao"] = "PARCIAL" if pacote["registros"] or not linhas else "BLOQUEADO"
            pacote["motivos"] = ["Há dados não recuperáveis, fonte provisória ou referências ausentes/ambíguas/cíclicas; revisar antes de qualquer retomada."]
        else:
            pacote["situacao"] = "COMPLETO"
    except (ErroEntrada, ValueError, KeyError, TypeError, AttributeError, DecimalException) as exc:
        # Falha global não deixa registros parciais aparentarem um pacote válido.
        pacote["registros"] = []
        pacote["diagnosticos"] = []
        pacote["cobertura"] = dict(pendencias_lidas=0, exportadas=0, nao_exportadas=0)
        pacote["motivos"] = [str(exc)]
        pacote["situacao"] = "BLOQUEADO"
    return _selar(pacote)


def _validar_registro(r, fontes):
    campos = {"id", "id_pendencia", "cnpj", "competencia_origem", "evento", "contextos", "referencias_necessarias",
              "origens", "motivo", "quem_decide", "proximo_passo", "tipo", "categoria", "natureza_valor", "valor_pendencia_brl"}
    _exigir(isinstance(r, dict) and set(r) == campos, "Registro de continuidade incompleto/desconhecido")
    evento = _ler_evento(r["evento"])
    _exigir(r["id_pendencia"] == _id_pendencia(evento) and r["id"] == "CONTINUIDADE:" + r["id_pendencia"],
            "IDs não preservam o vínculo da origem")
    _exigir(r["competencia_origem"] == evento["data"][:7], "Competência não corresponde à origem")
    _exigir(r["cnpj"] is None or isinstance(r["cnpj"], str) and re.fullmatch(r"[0-9]{14}", r["cnpj"]), "CNPJ inválido")
    _exigir(all(isinstance(r[c], str) and r[c].strip() for c in ("motivo", "quem_decide", "proximo_passo")), "Pendência sem motivo/responsável/próximo passo")
    _exigir(isinstance(r["tipo"], str) and r["tipo"] and r["categoria"] in {"DADOS", "NEGOCIO"}
            and r["natureza_valor"] in {"NAO_INFORMADO", "BRUTO_REFERENCIA", "COBRANCA_ORBE"}, "Tipo/categoria/natureza inválidos")
    _decimal(r["valor_pendencia_brl"], dinheiro=True, opcional=True)
    _exigir((r["valor_pendencia_brl"] is None) == (r["natureza_valor"] == "NAO_INFORMADO"),
            "Valor desconhecido deve conservar natureza explícita, sem zero inventado")
    _exigir(isinstance(r["contextos"], list), "Contextos inválidos")
    eventos, chaves = [evento], {_origem(evento["origem"])}
    for contexto in r["contextos"]:
        _exigir(isinstance(contexto, dict) and set(contexto) == {"papel", "evento"}
                and contexto["papel"] == "CONTEXTO_NAO_FATURAVEL", "Contexto não pode ser faturável")
        e = _ler_evento(contexto["evento"]); chave = _origem(e["origem"])
        _exigir(chave not in chaves, "Contexto/evento duplicado")
        chaves.add(chave); eventos.append(e)
    contextos, referencias = _vinculos(evento, eventos)
    _exigir(r["contextos"] == contextos and r["referencias_necessarias"] == referencias, "Referências/contextos inconsistentes ou não relacionados")
    _exigir(r["origens"] == _origens(evento, contextos, fontes), "Origens/hashes incompatíveis com eventos")


def _objeto_sem_duplicatas(pares):
    item = {}
    for chave, valor in pares:
        _exigir(chave not in item, "Chave JSON duplicada")
        item[chave] = valor
    return item


def ler_pendencias(documento):
    """Lê dict ou conteúdo JSON explícito; não abre caminhos nem calcula/fatura."""
    try:
        if isinstance(documento, (str, bytes)):
            documento = json.loads(documento, object_pairs_hook=_objeto_sem_duplicatas)
        pacote = deepcopy(documento)
        campos = {"versao", "recurso", "situacao", "motivos", "registros", "fontes", "diagnosticos", "origem_provisoria",
                  "faturamento_habilitado", "limitacoes_financeiras", "cobertura", "sha256_conteudo"}
        _exigir(isinstance(pacote, dict) and set(pacote) == campos and type(pacote["versao"]) is int
                and pacote["versao"] == 1 and pacote["recurso"] == "continuidade", "Versão/schema de continuidade inválido")
        digest = pacote.pop("sha256_conteudo")
        _exigir(isinstance(digest, str) and sha256(_canonico(pacote).encode("utf-8")).hexdigest() == digest,
                "Integridade do conteúdo de continuidade não confere")
        pacote["sha256_conteudo"] = digest
        _exigir(pacote["faturamento_habilitado"] is False and pacote["limitacoes_financeiras"] == LIMITACOES,
                "E2-P: documento não pode habilitar faturamento ou remover decisões pendentes")
        _exigir(pacote["situacao"] in {"COMPLETO", "PARCIAL", "BLOQUEADO"} and type(pacote["origem_provisoria"]) is bool,
                "Estado de continuidade inválido")
        _exigir(isinstance(pacote["motivos"], list) and all(isinstance(m, str) and m.strip() for m in pacote["motivos"]), "Motivos inválidos")
        _exigir(isinstance(pacote["fontes"], list), "Fontes inválidas")
        arquivos = set()
        for f in pacote["fontes"]:
            _exigir(isinstance(f, dict) and set(f) == {"arquivo", "sha256"} and isinstance(f["arquivo"], str)
                    and f["arquivo"] and f["arquivo"] not in arquivos and isinstance(f["sha256"], str)
                    and re.fullmatch(r"[0-9a-f]{64}", f["sha256"]), "Fonte/hash inválido ou duplicado")
            arquivos.add(f["arquivo"])
        _exigir(isinstance(pacote["registros"], list) and isinstance(pacote["diagnosticos"], list), "Listas inválidas")
        ids, refs, eventos = set(), set(), {}
        for r in pacote["registros"]:
            _validar_registro(r, pacote["fontes"])
            ref = r["evento"]["origem"]["ref"]
            _exigir(r["id"] not in ids and ref not in refs, "Pendência/transação exportada mais de uma vez")
            ids.add(r["id"]); refs.add(ref)
            for e in [r["evento"], *(c["evento"] for c in r["contextos"])]:
                chave = _origem(e["origem"])
                _exigir(chave not in eventos or eventos[chave] == e, "Evento/contexto conflitante entre registros")
                eventos[chave] = e
        for r in pacote["registros"]:
            contextos, referencias = _vinculos(r["evento"], list(eventos.values()))
            _exigir(r["contextos"] == contextos and r["referencias_necessarias"] == referencias,
                    "Referência disponível em outro registro foi omitida ou alterada")
        ids_pendencias = {r["id_pendencia"] for r in pacote["registros"]}
        for d in pacote["diagnosticos"]:
            _exigir(isinstance(d, dict) and set(d) == {"id_pendencia", "motivo"}
                    and all(isinstance(v, str) and v for v in d.values()), "Diagnóstico inválido")
            _exigir(d["id_pendencia"] not in ids_pendencias, "Pendência duplicada entre registros/diagnósticos")
            ids_pendencias.add(d["id_pendencia"])
        cobertura = pacote["cobertura"]
        _exigir(isinstance(cobertura, dict) and set(cobertura) == {"pendencias_lidas", "exportadas", "nao_exportadas"}
                and all(type(v) is int and v >= 0 for v in cobertura.values())
                and cobertura["exportadas"] == len(ids) and cobertura["nao_exportadas"] == len(pacote["diagnosticos"])
                and cobertura["pendencias_lidas"] == cobertura["exportadas"] + cobertura["nao_exportadas"], "Cobertura inconsistente")
        incompleto = pacote["origem_provisoria"] or bool(pacote["diagnosticos"]) or any(
            r["estado"] != "DISPONIVEL" for g in pacote["registros"] for r in g["referencias_necessarias"])
        _exigir(pacote["situacao"] != "COMPLETO" or not incompleto, "Pacote incompleto não pode declarar COMPLETO")
        _exigir(pacote["situacao"] == "COMPLETO" or bool(pacote["motivos"]), "Limitação sem diagnóstico")
        _exigir(pacote["situacao"] != "BLOQUEADO" or not pacote["registros"], "Pacote bloqueado não publica eventos recuperados")
        return pacote
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError) as exc:
        raise ErroEntrada(f"Continuidade rejeitada: {exc}") from exc
