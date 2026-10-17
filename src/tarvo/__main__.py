"""Uso: python -m tarvo --dados <pasta> --saida <pasta> --regras regras.toml."""

import argparse
from pathlib import Path
import sys

from .execucao import executar
from .exportacao import publicar
from .modelos import ErroEntrada


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mínimo: comissões de checkout com rastro e pendências explícitas")
    parser.add_argument("--dados", required=True, type=Path)
    parser.add_argument("--saida", default=Path("saida"), type=Path)
    parser.add_argument("--regras", default=Path("regras.toml"), type=Path)
    parser.add_argument("--competencia", help="AAAA-MM; obrigatório quando as entradas têm vários meses")
    parser.add_argument("--escopo", choices=["checkout", "alvo"], default="checkout",
                        help="Critério de conclusão; alvo inclui etapas ainda não implementadas")
    argumentos = parser.parse_args(argv)
    try:
        if argumentos.saida.resolve() == argumentos.dados.resolve():
            raise ErroEntrada("Use uma pasta de saída diferente da pasta de dados originais")
        resultado = executar(argumentos.dados, argumentos.regras, argumentos.competencia)
        manifesto = publicar(resultado, argumentos.saida, argumentos.escopo)
    except (ErroEntrada, OSError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    print(f"Checkout {resultado.situacao}")
    print(f"Escopo {argumentos.escopo}: {manifesto['situacao_comando']}")
    print(f"Fechamento alvo: {manifesto['fechamento']['situacao']}")
    print(f"Competência: {resultado.competencia or 'não determinada'}")
    cobertura = manifesto["cobertura"]
    print(f"Linhas: {cobertura['linhas_lidas']} | calculadas: {cobertura['calculadas']} | "
          f"pendentes: {cobertura['pendentes']} | bloqueadas: {cobertura['bloqueadas']}")
    print(f"Total da fatia validada: {manifesto['total_parcial_brl'] or 'indisponível'} BRL")
    for motivo in resultado.motivos:
        print(f"AVISO: {motivo}")
    for pendencia in resultado.pendencias:
        print(f"PENDÊNCIA {pendencia.origem.arquivo}:{pendencia.origem.ref} "
              f"(L{pendencia.origem.linha}) — {pendencia.motivo} — {pendencia.quem_decide}")
    for decisao in resultado.decisoes_pendentes:
        print(f"DECISÃO PENDENTE {decisao['id']}: {decisao['descricao']}")
    for decisao in resultado.decisoes_documentadas:
        print(f"DECISÃO DOCUMENTADA {decisao['id']}: {decisao['descricao']}")
    for nome, detalhe in manifesto["resultados"].items():
        print(f"RESULTADO {nome}: {detalhe['situacao']} ({detalhe['linhas']} linhas)")
    print(f"Manifesto: {argumentos.saida / 'manifesto.json'}")
    return {"COMPLETO": 0, "PROVISORIO": 2, "BLOQUEADO": 1}[manifesto["situacao_comando"]]


if __name__ == "__main__":
    sys.exit(main())
