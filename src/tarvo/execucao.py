"""Coordena somente checkout; fontes futuras não são dependências desta entrega."""

from hashlib import sha256
from pathlib import Path

from . import checkout, regras, validacao
from .leitores import orbe, taxas
from .modelos import Cadastro, ErroEntrada, Resultado


def executar(pasta: Path, configuracao: Path) -> Resultado:
    resultado = Resultado()
    bloqueios = []
    config = None
    try:
        config = regras.carregar(configuracao)
        resultado.decisoes_pendentes = config.get("decisoes_pendentes", [])
        resultado.fontes["regras"] = {
            "arquivo": configuracao.name, "situacao": "DISPONIVEL",
            "sha256": sha256(configuracao.read_bytes()).hexdigest(),
        }
    except (ErroEntrada, OSError) as exc:
        bloqueios.append(str(exc))
        resultado.fontes["regras"] = {"situacao": "BLOQUEADO", "motivo": str(exc)}
    cadastro = Cadastro()
    for nome, descobrir, ler in (
        ("orbe", orbe.descobrir, orbe.ler),
        ("taxas", taxas.descobrir, taxas.ler),
    ):
        try:
            if not pasta.is_dir():
                raise ErroEntrada(f"Pasta de dados inexistente ou inválida: {pasta}")
            caminho = descobrir(pasta)
            if nome == "orbe":
                resultado.eventos, resultado.pendencias, resultado.linhas_lidas = ler(caminho)
            elif config is None:
                raise ErroEntrada("Taxas: leitura bloqueada por configuração inválida")
            else:
                cadastro = ler(caminho, config["entrada"]["aba_taxas"], config["entrada"].get("abas_identidade", []))
            resultado.fontes[nome] = {
                "arquivo": caminho.name, "situacao": "DISPONIVEL",
                "sha256": sha256(caminho.read_bytes()).hexdigest(),
            }
        except (ErroEntrada, OSError) as exc:
            bloqueios.append(str(exc))
            resultado.fontes[nome] = {"situacao": "BLOQUEADO", "motivo": str(exc)}
    competencias = sorted({e.data.strftime("%Y-%m") for e in resultado.eventos})
    if len(competencias) == 1:
        resultado.competencia = competencias[0]
    else:
        bloqueios.append("Orbe: competência única não identificada; arquivo vazio, inválido ou com múltiplos meses")
    if bloqueios:
        resultado.motivos = bloqueios
        return resultado
    resultado.contribuicoes, pendencias = checkout.calcular(
        resultado.eventos, cadastro, config,
    )
    resultado.pendencias.extend(pendencias)
    resultado.pendencias.sort(key=lambda p: (p.origem.arquivo, p.origem.linha))
    validacao.consolidar(resultado)
    try:
        validacao.validar(resultado)
    except ErroEntrada as exc:
        resultado.motivos = [str(exc)]
        return resultado
    resultado.situacao = "PROVISORIO" if resultado.pendencias else "COMPLETO"
    if resultado.pendencias:
        resultado.motivos.append("Há linhas não calculadas; os CSVs representam somente os eventos de checkout validados")
    return resultado
