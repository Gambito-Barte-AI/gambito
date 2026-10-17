"""Publicação local: manifesto é o marcador de validade da execução atual."""

import csv
from decimal import Decimal
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from .modelos import ErroEntrada, Resultado
from .validacao import validar

ARQUIVOS = {
    "comissoes_por_lojista.csv": ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"],
    "rastro.csv": ["id_saida", "arquivo_origem", "ref_origem", "valor",
                  "contrato_origem", "ref_contrato", "taxa_contratada_fracao",
                  "faixa", "regra", "vinculo_identidade", "tipo_lancamento", "data_base_taxa",
                  "ref_evento_original", "arquivo_evento_original"],
}
MANIFESTO = "manifesto.json"


def csv_bytes(linhas: list[dict], colunas: list[str]) -> bytes:
    texto = StringIO(newline="")
    escritor = csv.DictWriter(texto, fieldnames=colunas, delimiter=";", lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(linhas)
    return texto.getvalue().encode("utf-8")


def resumo(resultado: Resultado) -> dict:
    processados = len(resultado.contribuicoes)
    pendentes = len(resultado.pendencias)
    return {
        "versao": 1, "escopo": "CHECKOUT_MINIMO", "etapa": "ENTREGA_4", "situacao": resultado.situacao,
        "competencia": resultado.competencia, "motivos": resultado.motivos,
        "fontes": resultado.fontes, "rastro_validado": resultado.validado and resultado.situacao != "BLOQUEADO",
        "ingestao": resultado.ingestao, "avisos": resultado.avisos,
        "cobertura": {
            "linhas_lidas": resultado.linhas_lidas, "calculadas": processados,
            "pendentes": pendentes,
            "bloqueadas": resultado.linhas_lidas - processados - pendentes,
        },
        "total_parcial_brl": (
            format(sum((c.valor for c in resultado.contribuicoes), Decimal(0)), ".2f")
            if resultado.validado and resultado.situacao != "BLOQUEADO" else None
        ),
        "pendencias": [{
            "arquivo_origem": p.origem.arquivo, "ref_origem": p.origem.ref,
            "linha": p.origem.linha, "motivo": p.motivo, "quem_decide": p.quem_decide,
            "valor_bruto_brl": str(p.valor_bruto) if p.valor_bruto is not None else None,
            "cnpj": p.cnpj,
            "identidade_origem": p.identidade_origem.arquivo if p.identidade_origem else None,
            "ref_identidade": p.identidade_origem.ref if p.identidade_origem else None,
            "vinculo_identidade": p.vinculo,
            "categoria": p.categoria, "tipo": p.tipo, "proximo_passo": p.proximo_passo,
            "valor_orbe_brl": format(p.valor_orbe, ".2f") if p.valor_orbe is not None else None,
        } for p in resultado.pendencias],
        "decisoes_financeiras_pendentes": resultado.decisoes_pendentes,
        "decisoes_documentadas": resultado.decisoes_documentadas,
        "fora_do_escopo": ["remessas", "divergencias", "notas", "extratos", "pendencias.csv"],
    }


def publicar(resultado: Resultado, pasta: Path) -> dict:
    if resultado.situacao != "BLOQUEADO":
        validar(resultado)  # nenhuma publicação se o resultado foi alterado após a execução
    pasta.mkdir(parents=True, exist_ok=True)
    anteriores = {}
    caminho_manifesto = pasta / MANIFESTO
    if caminho_manifesto.exists():
        try:
            anterior = json.loads(caminho_manifesto.read_text(encoding="utf-8"))
            if not isinstance(anterior, dict) or anterior.get("escopo") not in {"ENTREGA_1_CHECKOUT", "CHECKOUT_MINIMO"}:
                raise ValueError("manifesto de outro produtor")
            anteriores = anterior["arquivos"]
            if not isinstance(anteriores, dict) or set(anteriores) - ARQUIVOS.keys():
                raise ValueError("lista de arquivos não reconhecida")
        except (ValueError, KeyError) as exc:
            raise ErroEntrada(f"{caminho_manifesto}: não sobrescrito; manifesto não reconhecido") from exc
    for nome in ARQUIVOS:
        arquivo = pasta / nome
        if arquivo.exists() and (
            nome not in anteriores or sha256(arquivo.read_bytes()).hexdigest() != anteriores[nome]
        ):
            raise ErroEntrada(f"{arquivo}: não sobrescrito; arquivo externo ou modificado pelo usuário")
    dados = resumo(resultado)
    conteudos = {
        "comissoes_por_lojista.csv": csv_bytes(resultado.comissoes if resultado.situacao != "BLOQUEADO" else [], ARQUIVOS["comissoes_por_lojista.csv"]),
        "rastro.csv": csv_bytes(resultado.rastro if resultado.situacao != "BLOQUEADO" else [], ARQUIVOS["rastro.csv"]),
    }
    dados["publicacao_concluida"] = True
    dados["arquivos"] = {nome: sha256(valor).hexdigest() for nome, valor in conteudos.items()}
    # Prepara todos os bytes antes de trocar o marcador de validade.
    with TemporaryDirectory(prefix=".publicacao-", dir=pasta) as temporario:
        staging = Path(temporario)
        for nome, conteudo in conteudos.items():
            (staging / nome).write_bytes(conteudo)
        (staging / MANIFESTO).write_text(
            json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        interrompido = dict(dados, situacao="BLOQUEADO", rastro_validado=False,
                            publicacao_concluida=False,
                            total_parcial_brl=None, arquivos={},
                            motivos=["Publicação interrompida; arquivos não são válidos até o manifesto final"])
        marcador = staging / "interrompido.json"
        marcador.write_text(json.dumps(interrompido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(marcador, caminho_manifesto)
        for nome in ARQUIVOS:
            if nome in conteudos:
                os.replace(staging / nome, pasta / nome)
            elif (pasta / nome).exists():
                (pasta / nome).unlink()  # somente arquivos próprios, com hash verificado acima
        os.replace(staging / MANIFESTO, caminho_manifesto)
    return dados
