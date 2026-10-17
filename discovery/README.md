# Discovery — análises exploratórias

Esta etapa reúne as análises que apoiam a construção da solução de fechamento financeiro da Tarvo. Antes de automatizar os cálculos e a classificação dos extratos, precisamos entender como os dados chegam, quais informações conectam as fontes e onde o processo exige uma decisão humana.

O problema vai além de somar valores: a Orbe identifica lojistas por EC, a planilha usa CNPJ e os bancos apresentam nomes muitas vezes truncados. Os arquivos também têm formatos distintos, duplicatas e diferenças entre a data do movimento e a competência financeira. As análises ajudam a identificar esses pontos e a separar evidências dos dados, regras de negócio e hipóteses que precisam de validação.

Os notebooks registram esse processo:

- `00_teste_ambiente.ipynb`: verifica o ambiente e a disponibilidade das fontes.
- `01_exploracao.ipynb`: explora as fontes, as chaves de integração e a integridade dos dados da Orbe.
- `02_ponte_cambio.ipynb`: analisa o relatório de remessas da Ponte, duplicatas e valores de spread.
- `03_analise_extratos.ipynb`: examina os extratos dos bancos e o plano de contas Fênix, preservando as referências de origem e levantando contrapartidas e pendências.

- `04_analise_ajustes_tardios.ipynb`: compara os ajustes adicionais com a Orbe original, verifica referências, impacto incremental, reprocessamento e rastro.

As descobertas orientam os leitores, as validações e as regras do motor financeiro. O objetivo é sustentar as seis saídas da solução — comissões, divergências, notas, lançamentos classificados, pendências e rastro — com cada valor ligado à sua origem e cada exceção encaminhada para quem pode decidir.

Esta pasta documenta a exploração; os notebooks não geram os CSVs finais. As conclusões refletem as informações disponíveis quando cada análise foi feita e precisam ser confrontadas com as regras aprovadas antes de entrar na implementação.

## Como rodar os notebooks

Use Python 3.12 e mantenha os arquivos de entrada em `Tarvo_Data_Pack_set2026/`, na raiz do repositório. O pacote de dados não é versionado; ele precisa estar disponível localmente. Para usar outra pasta, ajuste a variável `PASTA` nos notebooks.

Na raiz do repositório, crie o ambiente e instale as dependências:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r discovery/requirements.txt
```

Se a `.venv` já estiver configurada, basta abrir o JupyterLab:

```bash
bash discovery/abrir_jupyter.sh
```

Abra os notebooks na ordem de `00` a `04` e use **Kernel → Restart Kernel and Run All Cells** para executar cada um do início ao fim. Cada notebook pode ser executado independentemente, sem depender das variáveis dos anteriores. Os resultados aparecem nas próprias células e os arquivos de entrada são preservados.

No VS Code, habilite as extensões **Python** e **Jupyter** da Microsoft, abra um notebook em `discovery/` e escolha **Select Kernel → Python Environments → .venv** deste repositório. Se necessário, selecione o interpretador `.venv/bin/python`. Depois, clique em **Run All**.

Para executar o notebook `04`, disponibilize também `06_orbe_ajustes_tardios_set2026.csv` na pasta de dados. O arquivo de entrada não é versionado. As regras são lidas de `docs/documentação-geral.md`, incluindo RN-13, RN-14, RN-20 a RN-23, RN-65 e RF-22; não é mais necessário disponibilizar `contexto_solucao.md`.

Os notebooks `00` a `03` preservam a exploração anterior à chegada das regras finais. A análise incremental `04` já utiliza a documentação atual do repositório; os avisos históricos de regras ausentes nos anteriores não descrevem a situação atual da documentação.
