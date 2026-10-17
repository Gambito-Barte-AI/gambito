"""Contratos internos: dinheiro em Decimal e origem desde a leitura."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


class ErroEntrada(ValueError):
    """Fonte ou configuração sem condições de processamento confiável."""


@dataclass(frozen=True)
class Origem:
    arquivo: str
    ref: str
    linha: int


@dataclass(frozen=True)
class Evento:
    origem: Origem
    data: date
    ec: str
    tipo: str
    modalidade: str
    parcelas: int | None
    bruto: Decimal
    referencia: str
    data_original: date | None


@dataclass(frozen=True)
class Contrato:
    origem: Origem
    ec: str
    cnpj: str
    nome: str
    taxas: dict[str, Decimal | None]
    inicio: date | None
    limitacao: str = ""
    fim: date | None = None
    observacao: str = ""


@dataclass(frozen=True)
class Identidade:
    cnpj: str
    nome: str
    origem: Origem
    ec: str = ""
    historica: bool = False
    vinculo: str = ""


@dataclass
class Cadastro:
    contratos: list[Contrato] = field(default_factory=list)
    identidades: list[Identidade] = field(default_factory=list)


@dataclass(frozen=True)
class Pendencia:
    origem: Origem
    motivo: str
    quem_decide: str
    valor_bruto: Decimal | None = None
    cnpj: str | None = None
    identidade_origem: Origem | None = None
    vinculo: str = ""


@dataclass(frozen=True)
class Contribuicao:
    origem: Origem
    contrato: Origem
    cnpj: str
    lojista: str
    competencia: str
    taxa: Decimal
    valor: Decimal
    faixa: str = ""
    regra: str = "PLANILHA"
    vinculo: str = ""


@dataclass
class Resultado:
    situacao: str = "BLOQUEADO"
    motivos: list[str] = field(default_factory=list)
    fontes: dict[str, dict] = field(default_factory=dict)
    eventos: list[Evento] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)
    contribuicoes: list[Contribuicao] = field(default_factory=list)
    comissoes: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    competencia: str | None = None
    linhas_lidas: int = 0
    validado: bool = False
    decisoes_pendentes: list[dict] = field(default_factory=list)
