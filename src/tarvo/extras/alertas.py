"""E3: pico observado ao fim de cada dia, sem limiar e sem efeito financeiro."""

from collections import defaultdict
from copy import deepcopy
from decimal import Decimal, DecimalException, localcontext
from datetime import datetime
import re

from ..cadastro import identificar
from ..modelos import ErroEntrada, ResultadoParte

NOME = "ALERTAS_ANTECIPACAO"


def parametros(config):
    if not isinstance(config, dict) or any(not isinstance(config.get(k), str) or not config[k].strip()
            for k in ("id", "fonte", "aprovacao", "aprovador", "aprovado_em", "natureza")):
        raise ErroEntrada("E3: critério exige fonte, aprovação, aprovador e data (RN-61)")
    if (config.get("habilitado") is not True or config.get("metodo") != "SALDO_FIM_DIA" or config.get("sem_valor_minimo") is not True
            or config.get("elegibilidade") != "CONTRATOS_BLOQUEADOS"
            or config.get("reversao_fora_periodo") != "LISTAR_SEM_ABATER"
            or config.get("exposicao_anterior") != "DESCONHECIDA"
            or config["natureza"] != "DECISAO_TIME" or "limiar_brl" in config):
        raise ErroEntrada("E3: critério diverge da decisão aprovada; sem inferência de histórico ou limiar")
    datetime.fromisoformat(config["aprovado_em"])
    return config


def elegibilidade(eventos, cadastro, regras):
    """Chave forte resolvida pelo cadastro; falha de fonte nunca cria bloqueio comercial."""
    bloqueados = {b["cnpj"]: b for b in regras.get("contratos_bloqueados", [])}
    saida = {}
    for ec in sorted({e.ec for e in eventos if e.tipo in {"ANTECIPACAO", "REVERSAO ANTECIPACAO"}}):
        identidade, erro = identificar(ec, cadastro, regras)
        if identidade and identidade.cnpj in bloqueados:
            saida[ec] = dict(cnpj=identidade.cnpj, bloqueio=deepcopy(bloqueados[identidade.cnpj]),
                            identidade_origem=identidade.origem)
        elif erro:
            saida[ec] = dict(erro=erro)
    return saida


def _valor(e):
    v = e.bruto
    if not isinstance(v, Decimal) or not v.is_finite() or Decimal(format(v, ".2f")) != v:
        raise ErroEntrada("Valor bruto inválido ou fração de centavo")
    return v


def _origem(e):
    return dict(arquivo=e.origem.arquivo, ref=e.origem.ref, linha=e.origem.linha)


def analisar_antecipacoes(eventos, elegibilidade, config):
    elegiveis = elegibilidade
    pacote = dict(versao=1, recurso="alertas", situacao="BLOQUEADO", motivos=[], registros=[])
    try:
        parametros(config)
        meses = {e.data.strftime("%Y-%m") for e in eventos}
        if len(meses) > 1:
            raise ErroEntrada("E3: fornecer eventos de uma única competência")
        por_ref, grupos, identidades = defaultdict(list), defaultdict(list), defaultdict(set)
        for e in eventos:
            por_ref[e.origem.ref].append(e)
            if e.tipo not in {"ANTECIPACAO", "REVERSAO ANTECIPACAO"}:
                continue
            estado = elegiveis.get(e.ec)
            if not estado:
                continue
            if estado.get("erro"):
                pacote["motivos"].append(f"EC {e.ec}: {estado['erro']}; sem inferir contrato/histórico")
                continue
            cnpj = estado["cnpj"]
            if not re.fullmatch(r"[0-9]{14}", cnpj) or estado["bloqueio"]["cnpj"] != cnpj:
                raise ErroEntrada("E3: evidência de bloqueio comercial inválida")
            if any(not isinstance(estado["bloqueio"].get(k), str) or not estado["bloqueio"][k].strip()
                   for k in ("id", "fonte", "aprovacao", "aprovador", "aprovado_em")):
                raise ErroEntrada("E3: bloqueio comercial sem proveniência")
            grupos[cnpj].append(e); identidades[cnpj].add(e.ec)
        for cnpj, itens in sorted(grupos.items()):
            try:
                antecipacoes = [e for e in itens if e.tipo == "ANTECIPACAO"]
                if not antecipacoes:
                    continue
                dias, movimentos, reversoes, anuladas = defaultdict(list), [], [], set()
                for e in sorted(itens, key=lambda e: (e.data, e.origem.arquivo, e.origem.ref)):
                    if len(por_ref[e.origem.ref]) != 1:
                        raise ErroEntrada("ID de operação repetido/conflitante")
                    valor = _valor(e)
                    if e.tipo == "ANTECIPACAO":
                        if valor <= 0:
                            raise ErroEntrada("Antecipação deve ter bruto positivo")
                        dias[e.data].append((e, valor)); movimentos.append((e, valor))
                    else:
                        if valor >= 0 or not e.referencia:
                            raise ErroEntrada("Reversão sem referência ou sinal compatível")
                        candidatas = por_ref[e.referencia]
                        abatida = bool(candidatas)
                        if abatida:
                            if len(candidatas) != 1:
                                raise ErroEntrada("Original da reversão ambíguo")
                            original = candidatas[0]
                            if (original.tipo != "ANTECIPACAO" or original.ec != e.ec
                                    or original.data > e.data or e.data_original != original.data
                                    or _valor(original) != -valor or e.referencia in anuladas):
                                raise ErroEntrada("Reversão não anula exclusivamente a antecipação vinculada")
                            anuladas.add(e.referencia)
                            dias[e.data].append((e, valor)); movimentos.append((e, valor))
                        reversoes.append(dict(ref=e.origem.ref, ref_original=e.referencia,
                            data=e.data.isoformat(), valor_brl=format(valor, ".2f"), abatida=abatida,
                            origem=_origem(e)))
                # Soma diária, sem inventar a ordem intradia. O pico pode ser zero.
                with localcontext() as ctx:
                    ctx.prec = max(28, max(len(format(v, "f")) for _, v in movimentos) + len(str(len(movimentos))) + 4)
                    saldo, pico, data_pico = Decimal(0), None, None
                    for dia in sorted(dias):
                        saldo += sum((v for _, v in dias[dia]), Decimal(0))
                        if saldo < 0:
                            raise ErroEntrada("Saldo observado negativo: revisar vínculos, sem estimar exposição anterior")
                        if pico is None or saldo > pico:
                            pico, data_pico = saldo, dia
                    total = sum((_valor(e) for e in antecipacoes), Decimal(0))
                contribuicoes = [dict(origem=_origem(e), valor_brl=format(v, ".2f"),
                    tipo=e.tipo, ref_original=e.referencia) for e, v in movimentos if e.data <= data_pico]
                competencia = data_pico.strftime("%Y-%m")
                texto_reversoes = "; ".join(
                    f"{r['ref']} em {r['data']}: {r['valor_brl']} BRL, ref. {r['ref_original']}"
                    + (" (abatida)" if r["abatida"] else " (não abatida: antecipação não disponível no período)") for r in reversoes) or "nenhuma"
                motivo = (f"Contrato explicitamente bloqueado. Pico observado ao fim do dia {data_pico.isoformat()}: {pico:.2f} BRL; "
                    f"total antecipado {total:.2f} BRL; saldo final observado {saldo:.2f} BRL. "
                    f"Reversões: {texto_reversoes}. Exposição anterior ao período desconhecida; "
                    "não representa a agenda completa e não compara com vendas do mês. Sem valor mínimo.")
                evidencias = [deepcopy(elegiveis[ec]["bloqueio"]) for ec in sorted(identidades[cnpj])]
                pacote["registros"].append(dict(id=f"ALERTA_ANTECIPACAO:{competencia}:{cnpj}",
                    cnpj=cnpj, ec=" | ".join(sorted(identidades[cnpj])), motivo_elegibilidade="CONTRATO_EXPLICITAMENTE_BLOQUEADO",
                    evidencias_elegibilidade=evidencias, pico_brl=format(pico, ".2f"), data_pico=data_pico.isoformat(),
                    total_antecipado_brl=format(total, ".2f"), saldo_final_brl=format(saldo, ".2f"),
                    refs_antecipacoes=sorted(e.origem.ref for e in antecipacoes), refs_reversoes=sorted(r["ref"] for r in reversoes),
                    origens=[_origem(e) for e in sorted(itens, key=lambda e: (e.origem.arquivo, e.origem.ref))],
                    reversoes=reversoes, contribuicoes_pico=contribuicoes, regra_id=config["id"], texto=motivo,
                    quem_decide="Financeiro e Comercial"))
            except (ErroEntrada, KeyError, ValueError, DecimalException) as exc:
                pacote["motivos"].append(f"CNPJ {cnpj}: {exc}; alerta não publicado")
        pacote["motivos"] = sorted(set(pacote["motivos"]))
        pacote["situacao"] = "PARCIAL" if pacote["motivos"] else "COMPLETO"
    except (ErroEntrada, ValueError, KeyError, TypeError, AttributeError, DecimalException) as exc:
        pacote["registros"] = []; pacote["motivos"] = [str(exc)]
        pacote["situacao"] = "BLOQUEADO"
    return pacote


def calcular_parte(contexto):
    pacote = analisar_antecipacoes(contexto["eventos"], contexto["elegiveis"], contexto["config"])
    parte = ResultadoParte(fontes=("orbe", "taxas", "regras"), relatorios=("pendencias.csv",), implementado=True,
        situacao={"COMPLETO": "COMPLETO", "PARCIAL": "PROVISORIO", "BLOQUEADO": "BLOQUEADO"}[pacote["situacao"]],
        motivos=list(pacote["motivos"]), linhas={"pendencias.csv": []})
    for r in pacote["registros"]:
        primeiro = r["contribuicoes_pico"][0]["origem"]
        parte.linhas["pendencias.csv"].append(dict(id_saida=r["id"], tipo="ALERTA_ANTECIPACAO", cnpj=r["cnpj"],
            ref_origem=primeiro["ref"], arquivo_origem=primeiro["arquivo"], linha_origem=primeiro["linha"],
            valor_brl=r["pico_brl"], motivo=r["texto"], quem_decide=r["quem_decide"],
            proximo_passo="Avaliar o risco da antecipação enquanto o contrato não for confirmado.",
            categoria="NEGOCIO", natureza_valor="PICO_EXPOSICAO_OBSERVADA"))
        for c in r["contribuicoes_pico"]:
            o = c["origem"]
            parte.rastro.append(dict(id_saida=r["id"], arquivo_origem=o["arquivo"], ref_origem=o["ref"],
                linha_origem=o["linha"], valor=c["valor_brl"], tipo_lancamento=c["tipo"],
                ref_evento_original=c["ref_original"], regra=r["regra_id"], natureza_valor="PICO_EXPOSICAO_OBSERVADA"))
    parte.cobertura = dict(linhas_lidas=len(pacote["registros"])+len(pacote["motivos"]),
        calculadas=len(pacote["registros"]), pendentes=len(pacote["motivos"]), bloqueadas=0)
    return parte


def validar(parte, contexto):
    esperado = calcular_parte(contexto)
    if parte.linhas != esperado.linhas or parte.rastro != esperado.rastro or parte.cobertura != esperado.cobertura:
        raise ErroEntrada("Alerta diverge do pico diário, dos eventos ou da elegibilidade comprovada")


def preparar(resultado):
    if resultado.contexto_alertas is None:
        return
    resultado.partes[NOME] = calcular_parte(resultado.contexto_alertas)
