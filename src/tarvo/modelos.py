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
    valor_taxa: Decimal | None = None
    taxa_aplicada_pct: Decimal | None = None
    erro_taxa_aplicada: str = ""
    erro_valor_taxa: str = ""


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
    categoria: str = "DADOS"
    proximo_passo: str = "Conferir a linha na origem e reenviar os dados corrigidos."
    valor_orbe: Decimal | None = None
    tipo: str = "DADO_NAO_RESOLVIDO"


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
    tipo: str = ""
    data_base_taxa: date | None = None
    ref_original: str = ""
    arquivo_original: str = ""


@dataclass
class ResultadoParte:
    """Um resultado validável; não executa leitores ou cálculos financeiros."""

    fontes: tuple[str, ...] = ()
    depende_de: tuple[str, ...] = ()
    relatorios: tuple[str, ...] = ()
    implementado: bool = False
    situacao: str = "BLOQUEADO"
    motivos: list[str] = field(default_factory=list)
    linhas: dict[str, list[dict]] = field(default_factory=dict)
    rastro: list[dict] = field(default_factory=list)
    cobertura: dict[str, int] = field(default_factory=dict)
    validado: bool = False


@dataclass(frozen=True)
class OperacaoPonte:
    origem: Origem
    contratacao: date
    cnpj: str
    cliente: str
    spread_brl: Decimal
    spread_pct: Decimal | None
    ptax: Decimal | None
    valor_me: Decimal | None
    observacao: str = ""
    status: str = ""
    competencia_ajuste: str = ""

    @property
    def competencia(self):
        return self.competencia_ajuste or self.contratacao.strftime("%Y-%m")


@dataclass(frozen=True)
class ContratoRemessa:
    origem: Origem
    cnpj: str
    nome: str
    spread: Decimal | None
    inicio: date | None
    fim: date | None = None
    limitacao: str = ""


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
    decisoes_documentadas: list[dict] = field(default_factory=list)
    ingestao: dict = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    partes: dict[str, ResultadoParte] = field(default_factory=dict)
    calculo_executado: bool = False
    parametros_notas: dict[str, dict] = field(default_factory=dict)
