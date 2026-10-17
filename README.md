# Gambito — Entrega 2

Checkout Tarvo com identidade, faixas e vigências: lê Orbe e taxas, calcula **vendas com contrato inequívoco na data da venda**, valida o rastro e publica dois CSVs. O resultado do data pack é **parcial**: estornos, antecipações e reversões ainda pertencem à Entrega 3. Nenhuma funcionalidade do alvo foi implementada.

## Instalação

Python 3.11 ou superior. Na raiz do repositório, em PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

A única dependência de execução é `openpyxl` (XLSX). Não há servidor, banco, acesso a API ou chave obrigatória. `.env.example` fica reservado à eventual IA, fora desta entrega. Nenhuma variável desse arquivo é consumida agora.

## Executar

Coloque os arquivos originais do mês em uma pasta. Não os edite antes de executar:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados data/raw --saida saida --regras regras.toml
```

Para o data pack local, se disponível:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida --regras regras.toml
```

O data pack e `Context/` não estão versionados. A banca precisa fornecer os arquivos originais. O comando não depende desses nomes: descobre um CSV com `id_transacao` e um único XLSX; a aba vigente é configurada em `regras.toml`. Mais de um candidato bloqueia a fonte, sem escolher arbitrariamente. A competência é obtida de `data_movimento`; arquivos vazios ou com múltiplos meses ficam bloqueados nesta entrega.

Na validação da Entrega 2, a pasta local recebeu também `06_orbe_ajustes_tardios_set2026.csv`. Com dois relatórios Orbe, o comando acima gera corretamente `BLOQUEADO`; não há fusão ou seleção automática. Para reproduzir o recorte aprovado, coloque em `data/raw/` somente o relatório Orbe original e a planilha de taxas, copiados sem alteração, e use o primeiro comando. O relatório adicional permanece intacto e seu processamento não foi incorporado. A evidência desta entrega está em `saida/entrega2/`; o manifesto na raiz de `saida/` registra o bloqueio da pasta completa.

## Escopo financeiro

- Calcula `VENDA` de débito, crédito à vista e Pix com 0 ou 1 parcela, e crédito parcelado nas faixas 2–6 e 7–12. Valores não positivos, 13x, modalidade desconhecida ou quantidade inconsistente ficam pendentes.
- Resolve EC/CNPJ pela planilha ou por vínculo explícito de `regras.toml`. Não associa por nome. Vínculos conflitantes ficam pendentes, sem sobrescrever o cadastro da planilha.
- Seleciona uma única linha contratual válida: data isolada representa início; `até dd/mm/aaaa` representa término; `a partir de dd/mm/aaaa` representa início. Limites são inclusivos; o limite não informado é aberto. Sobreposição, lacuna ou vigência desconhecida gera pendência.
- Observações desconhecidas continuam pendentes. Apenas os textos explicitamente esclarecidos por CNPJ em `regras.toml` podem ser utilizados, com fonte e interpretação registradas.
- Taxas XLSX numéricas são frações; taxas textuais exigem `%`. Texto sem unidade, fórmula ou taxa ausente vira pendência.
- Usa a taxa contratada, nunca `valor_taxa` ou taxa aplicada da Orbe. Arredonda cada contribuição com `Decimal`/`ROUND_HALF_UP` antes de somar.
- As abas em `entrada.abas_identidade` fornecem apenas CNPJ/nome/origem, nunca taxas ou vigência. Ausência dessas abas não bloqueia os contratos vigentes; identidades que dependeriam delas permanecem pendentes.
- A Atlas é identificada pela aba antiga e vínculo documentado, mas o bloqueio comercial mantém seus eventos pendentes. Nenhuma taxa antiga é importada. D-07 não foi ratificada: a ausência de comissão calculada não decide a representação final fora/zerada.
- A isenção confirmada da Casa usa a data da venda e o intervalo configurado. Contribuições isentas são zero com rastro. Antes/depois do intervalo, aplica-se o contrato vigente, sem estender a isenção. Devolução ao lojista não é calculada e D-08 permanece pendente.
- D-10 continua fora do escopo. Estornos, antecipações e reversões não são calculados nesta etapa, inclusive para lojistas isentos.
- Remessas, divergências, notas, extratos, devoluções, IA e `pendencias.csv` não são implementados.

## Resultados e fechamento parcial

`saida/` recebe:

- `comissoes_por_lojista.csv`: somente contribuições calculadas, agrupadas por CNPJ; layout obrigatório.
- `rastro.csv`: contribuições de comissão com referência Orbe; soma exata por `id_saida`, incluindo linhas com valor zero. Colunas adicionais registram arquivo/linha contratual, taxa em fração, faixa, regra aplicada e vínculo de identidade.
- `manifesto.json`: situação, competência, hashes das fontes e saídas, cobertura, limitações, decisões pendentes e todas as pendências por referência. O valor bruto de uma pendência não representa comissão nem valor a cobrar.

O terminal exibe resumo e pendências com motivo e responsável. IDs e ordenação são estáveis; mesma entrada e regras geram os mesmos arquivos.

| Situação | Significado | Código de saída |
| --- | --- | --- |
| `COMPLETO` | Todas as linhas atendidas pelo recorte até a Entrega 2, sem pendências. Não significa mínimo completo nem alvo concluído. | `0` |
| `PROVISORIO` | CSVs válidos somente para contribuições calculadas; demais linhas identificadas como pendências. | `2` |
| `BLOQUEADO` | Dependência inválida/ausente, competência ambígua ou falha de validação; sem CSVs atuais. | `1` |

Ausência de fontes do alvo não bloqueia checkout. As duas fontes desta entrega são inspecionadas independentemente, mas checkout precisa de ambas e das regras. Linha com dado inválido e ID conhecido pode ficar pendente; ID ausente/duplicado ou erro estrutural bloqueia a fonte. Não se infere como deduplicar Orbe.

**Consulte sempre `manifesto.json` e verifique seus hashes antes de consumir CSVs.** Ele é publicado por último como marcador de validade. Se a publicação for interrompida, o marcador permanece bloqueado. Só os arquivos registrados em `arquivos` pertencem à execução atual.

Uma execução bloqueada publica diagnóstico e remove apenas os dois CSVs anteriores gerados por este produtor e cujo hash permanece intacto. Arquivos externos ou modificados pelo usuário nunca são sobrescritos/removidos: o comando falha e pede outra pasta de saída. Não use a pasta das entradas como saída. Outros arquivos presentes em `saida/` não fazem parte desta entrega.

## Verificação

Os testes usam `unittest` da biblioteca padrão, sem dependência de desenvolvimento adicional:

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src')
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

As amostras são sintéticas e criadas em diretório temporário: arredondamento por linha, rastro, faixas 2/6/7/12/13x, limites de vigência, sobreposições, lacunas, vínculos conflitantes, identidade histórica sem taxa antiga, isenção, fontes faltantes, layouts, pendências, determinismo, proteção das saídas e códigos do comando. Totais do case não são usados como regras.

## Configuração e decisões pendentes

`regras.toml` contém os três ECs complementares confirmados, vínculo da Atlas, bloqueio por falta de confirmação comercial, período de isenção da Casa e observações esclarecidas. Valores, datas e identificadores do caso ficam nessa configuração, nunca como constantes no código de cálculo. Cada registro tem fonte e descrição da aprovação conhecida ou da interpretação técnica; datas/pessoas não informadas não são inventadas.

D-07 (representação da Atlas), D-08 (devolução da Casa) e D-10 (semântica do ajuste Ponte) continuam no manifesto e em `HIPOTESES.md`. Aprovar esta entrega não ratifica essas decisões financeiras. Não é preciso API nem nova dependência para a Entrega 2.

## Estrutura

`src/tarvo/` separa execução, modelos, leitores, cadastro, cálculo, validação e exportação. `regras.toml` contém a configuração desta fatia e decisões pendentes. `docs/FORMATO_SAIDA.md` conserva o contrato do desafio. `HIPOTESES.md` registra limites e decisões. `PROMPTS/` registra o uso de IA.
