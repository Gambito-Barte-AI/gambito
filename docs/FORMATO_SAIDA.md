# Formato de saída

Parte da correção é automática — o formato é fixo.

## Regras gerais

- CSV com `;` como separador
- Ponto como separador decimal
- Datas em `AAAA-MM-DD`
- CNPJ só com números (14 dígitos)
- Colunas extras são permitidas

## Arquivos

| Arquivo | Colunas obrigatórias |
| ------- | -------------------- |
| `comissoes_por_lojista.csv` | `id_saida; cnpj; lojista; linha_negocio; comissao_brl` |
| `divergencias_taxa.csv` | `id_saida; cnpj; linha_negocio; ref_origem; taxa_contratada_pct; taxa_aplicada_pct; diferenca_brl` |
| `notas_a_emitir.csv` | `id_saida; tomador_cnpj; tomador; linha_negocio; valor_brl; discriminacao` |
| `lancamentos_classificados.csv` | `id_saida; banco; ref_origem; data; descricao; valor; conta_codigo; metodo; confianca` |
| `pendencias.csv` | `id_saida; tipo; ref_origem; valor_brl; motivo; quem_decide` |
| `rastro.csv` | `id_saida; arquivo_origem; ref_origem; valor` |

## Domínios

- `linha_negocio`: `CHECKOUT` ou `REMESSA`
- `banco`: `AURORA` ou `MERIDIANO`
- `metodo`: `REGRA`, `IA` ou `HUMANO`
- `confianca`: de `0` a `1`

## `ref_origem`

| Origem | Identificador |
| ------ | ------------- |
| Orbe | `id_transacao` |
| Ponte | `Nº Operação` |
| Extrato Aurora | número da linha física do arquivo (`L10`, `L11`…) |
| Extrato Meridiano | `FITID` |

## `rastro.csv`

Liga cada número de saída às linhas de origem. A soma de `valor` por `id_saida` deve bater com o número reportado.
