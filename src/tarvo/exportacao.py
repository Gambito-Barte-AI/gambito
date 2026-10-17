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

from .contratos import ARQUIVOS
from .partes import preparar_partes, selecionar, agregar_situacoes

MANIFESTO = "manifesto.json"


def csv_bytes(linhas: list[dict], colunas: list[str]) -> bytes:
    texto = StringIO(newline="")
    escritor = csv.DictWriter(texto, fieldnames=colunas, delimiter=";", lineterminator="\n")
    escritor.writeheader()
    escritor.writerows(linhas)
    return texto.getvalue().encode("utf-8")


def resumo(resultado: Resultado, escopo: str = "checkout") -> dict:
    processados = len(resultado.contribuicoes) if resultado.partes["CHECKOUT"].validado else 0
    pendentes = len(resultado.pendencias) if resultado.partes["PENDENCIAS_CHECKOUT"].validado else 0
    dados = {
        "versao": 3, "escopo": "CHECKOUT_MINIMO", "etapa": "ALVO_A1", "situacao": resultado.situacao,
        "escopo_situacao": "CHECKOUT",
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
        "fora_do_escopo": ["remessas", "divergencias", "notas", "extratos"],
    }

    escolhidas = selecionar(resultado, escopo)
    dados["escopo_comando"] = escopo
    dados["situacao_comando"] = agregar_situacoes(resultado.partes[n].situacao for n in escolhidas)
    dados["fechamento"] = {
        "escopo": "ALVO", "situacao": agregar_situacoes(p.situacao for p in resultado.partes.values()),
        "partes": list(resultado.partes),
        "bloqueadas": [n for n, p in resultado.partes.items() if p.situacao == "BLOQUEADO"],
        "provisorias": [n for n, p in resultado.partes.items() if p.situacao == "PROVISORIO"],
    }
    dados["partes"] = {
        nome: {"situacao": parte.situacao, "motivos": parte.motivos,
               "implementado": parte.implementado, "rastro_validado": parte.validado,
               "dependencias": {"fontes": list(parte.fontes), "partes": list(parte.depende_de)},
               "fontes": {f: resultado.fontes.get(f, {}).get("situacao", "NAO_AVALIADA") for f in parte.fontes},
               "relatorios": list(parte.relatorios), "cobertura": parte.cobertura}
        for nome, parte in resultado.partes.items()
    }
    return dados


def publicar(resultado: Resultado, pasta: Path, escopo: str = "checkout") -> dict:
    selecionar(resultado, escopo)  # rejeita escopo inválido antes de qualquer escrita
    preparar_partes(resultado)  # isola alterações/corrupção por resultado antes de publicar
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
    dados = resumo(resultado, escopo)
    linhas = {nome: [] for nome in ARQUIVOS}
    escolhidas = selecionar(resultado, escopo)
    dados["resultados"] = {}
    for arquivo in ARQUIVOS:
        previstas = [n for n, p in resultado.partes.items() if arquivo == "rastro.csv" or arquivo in p.relatorios]
        participantes = [n for n in previstas if n in escolhidas] or previstas
        for nome in participantes:
            parte = resultado.partes[nome]
            if nome in escolhidas and parte.validado and parte.situacao != "BLOQUEADO":
                linhas[arquivo].extend(parte.rastro if arquivo == "rastro.csv" else parte.linhas.get(arquivo, []))
        dados["resultados"][arquivo] = {
            "situacao": agregar_situacoes(resultado.partes[n].situacao for n in participantes),
            "situacao_alvo": agregar_situacoes(resultado.partes[n].situacao for n in previstas),
            "escopo": escopo, "partes": participantes,
            "partes_bloqueadas": [n for n in participantes if resultado.partes[n].situacao == "BLOQUEADO"],
            "motivos": list(dict.fromkeys(m for n in participantes for m in resultado.partes[n].motivos)),
            "linhas": len(linhas[arquivo]),
        }
    conteudos = {nome: csv_bytes(linhas[nome], colunas) for nome, colunas in ARQUIVOS.items()}
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
        interrompido = dict(dados, situacao="BLOQUEADO", situacao_comando="BLOQUEADO", rastro_validado=False,
                            publicacao_concluida=False,
                            total_parcial_brl=None, arquivos={},
                            motivos=["Publicação interrompida; arquivos não são válidos até o manifesto final"])
        interrompido["resultados"] = {
            nome: {"situacao": "BLOQUEADO", "motivos": interrompido["motivos"], "linhas": 0}
            for nome in ARQUIVOS
        }
        interrompido["fechamento"] = dict(dados["fechamento"], situacao="BLOQUEADO",
                                           bloqueadas=list(resultado.partes), provisorias=[])
        interrompido["partes"] = {
            nome: dict(detalhe, situacao="BLOQUEADO", rastro_validado=False, motivos=interrompido["motivos"])
            for nome, detalhe in dados["partes"].items()
        }
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
