"""Identidade por chave forte e contrato único vigente na data da venda."""

from dataclasses import replace
from datetime import date

from .leitores.taxas import normalizar
from .modelos import Cadastro, Contrato, Identidade


def identificar(ec: str, cadastro: Cadastro, regras: dict) -> tuple[Identidade | None, str]:
    if any(c.ec == ec and not c.cnpj for c in cadastro.contratos):
        return None, "EC com identidade contratual inválida; não substituir por vínculo complementar"
    vinculos = [v for v in regras.get("vinculos", []) if v["ec"] == ec]
    diretos = [i for i in cadastro.identidades if i.ec == ec and not i.historica]
    cnpjs = {i.cnpj for i in diretos} | {v["cnpj"] for v in vinculos}
    if len(cnpjs) != 1:
        return None, "Identidade ausente ou conflitante para o EC; não associar por nome"
    cnpj = cnpjs.pop()
    identidades = [i for i in cadastro.identidades if i.cnpj == cnpj]
    if not identidades:
        return None, "CNPJ do vínculo não encontrado nas fontes de identidade"
    identidade = min(identidades, key=lambda i: (i.historica, i.origem.arquivo, i.origem.linha))
    fonte = " | ".join(sorted({v["id"] for v in vinculos})) or "EC_ORBE_PLANILHA"
    return replace(identidade, vinculo=fonte), ""


def resolver(identidade: Identidade, data: date, cadastro: Cadastro, regras: dict) -> tuple[Contrato | None, str]:
    bloqueios = [b for b in regras.get("contratos_bloqueados", []) if b["cnpj"] == identidade.cnpj]
    if bloqueios:
        return None, "; ".join(b["motivo"] for b in bloqueios)
    candidatos = [c for c in cadastro.contratos if c.cnpj == identidade.cnpj]
    if any(c.inicio is None and c.fim is None for c in candidatos):
        return None, "Há vigência contratual desconhecida; não é possível excluir sobreposição"
    vigentes = [c for c in candidatos if (c.inicio is None or data >= c.inicio)
                and (c.fim is None or data <= c.fim)]
    if len(vigentes) != 1:
        return None, "Contrato ausente na data da venda ou vigências sobrepostas"
    contrato = vigentes[0]
    if contrato.limitacao:
        return None, contrato.limitacao
    esclarecidas = [o for o in regras.get("observacoes_esclarecidas", []) if o["cnpj"] == identidade.cnpj]
    if contrato.observacao and not any(normalizar(o["texto"]) == normalizar(contrato.observacao)
                                      for o in esclarecidas):
        return None, "Observação comercial não esclarecida; requer decisão do Comercial"
    return contrato, ""
