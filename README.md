# gambito

> Projeto do hackathon — conciliação de comissões, taxas, notas e lançamentos bancários a partir do data pack.

## Estrutura

```
.
├── README.md          # este arquivo: como instalar, rodar e limitações
├── HIPOTESES.md       # premissas assumidas e perguntas ao financeiro
├── PROMPTS/           # histórico das sessões de IA
│   ├── MOMENTOS.md    # 2 a 4 momentos que importaram
│   └── sessoes/       # transcripts, exports, links e prints
├── data/
│   └── raw/           # data pack original (não versionado)
├── docs/              # documentação de apoio (formato de saída etc.)
├── saida/             # CSVs gerados (correção automática)
└── src/               # código, fluxos e configurações
```

## Pré-requisitos

_TODO_

## Instalação

_TODO_

## Configuração

Copie o arquivo de exemplo e preencha as chaves:

```bash
cp .env.example .env
```

| Variável | Descrição |
| -------- | --------- |
| _TODO_   | _TODO_    |

## Como rodar do zero

_TODO_

## Saídas

Os arquivos gerados ficam em [`saida/`](saida/). Formato detalhado em [`docs/FORMATO_SAIDA.md`](docs/FORMATO_SAIDA.md).

## Limitações conhecidas

_TODO_
