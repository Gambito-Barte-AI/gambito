# Aceite A4 — notas a emitir

A4 autorizada pelo usuário e implementada em 17/10/2026. Preservados o mínimo, A1–A3, a RN-64 corrigida e a arquitetura modular existente. A5 não iniciada; nenhuma dependência instalada, emissão fiscal, integração externa, commit ou alteração de branch realizada pelo agente.

## Implementação e contratos

- `src/tarvo/notas.py`: deriva propostas somente das comissões validadas, com Decimal, sem recalcular taxas, participação ou arredondamentos. RN-42: uma proposta por CNPJ/competência de checkout com saldo positivo. RN-44: uma proposta por competência para a Ponte, somando os saldos dos lojistas, incluindo contribuições negativas elegíveis de ajuste. Serviço e tomador vêm das regras; não há condição específica por nome ou total conhecido.
- RN-43: saldo zero/negativo vira pendência financeira `SEM_NOTA:`, com valor assinado, próximo passo e todas as origens; não gera nota nem transporte para outra competência. Atlas sem comissão calculável não recebe nota nem saldo zero inventado.
- RN-45/RN-61: discriminação com serviço e competência; configuração TOML com fonte, aprovação, aprovador/papel documentado e data. Competência e identidade vêm do contrato interno da comissão, confrontadas com os campos publicados.
- D-10 continua pendente de confirmação financeira. Ajustes já calculados por A3 abatem o saldo uma única vez. A proposta com ajuste inclui a ressalva na discriminação e nos motivos; o rastro mantém a referência original e a pendência de A3 continua disponível. Os exemplos fornecidos não contêm esse ajuste; os testes usam dados sintéticos.
- NOTAS_CHECKOUT depende de CHECKOUT + regras; NOTAS_REMESSA depende de REMESSAS + regras. Divergências e devolução não bloqueiam comissão/proposta válida. Comissão provisória gera proposta provisória do subconjunto conhecido, com situação explícita no manifesto. Falha de configuração, rastro ou projeção bloqueia somente o resultado dependente.
- O rastro das propostas replica exatamente as contribuições das comissões, inclusive zeros, negativos e metadados do original, alterando apenas ID de destino e natureza. Não entram valores de devolução, contestação ou acompanhamento. A publicação reconfere a projeção sem corrigir adulterações silenciosamente.

As seis saídas e seus campos oficiais foram preservados. Manifesto versão 6, etapa ALVO_A4, parâmetros de notas e situação por resultado. Cobertura das partes NOTAS conta saldos de comissão de origem, não transações físicas nem quantidade de notas. No escopo padrão, os seis CSVs do mínimo conservam seus bytes. Somente classificação bancária permanece futura; fechamento integral do alvo continua PROVISORIO.

## Resultados conferidos

| Verificação | Resultado |
| --- | --- |
| Notas checkout | 20 propostas, **R$ 203.740,84** |
| Nota Ponte | Uma proposta, **R$ 39.543,45**, para o CNPJ configurado 75374179000146 |
| Total das propostas | 21 propostas, **R$ 243.284,29** |
| Saldo checkout da Casa | **−R$ 5,50**; sem nota, com pendência Financeiro e 119 contribuições de origem; sem transporte |
| RN-64 | **R$ 15.396,77** em 118 origens; estorno isento de R$ 9,08 abatido e estorno de agosto fora da devolução |
| Checkout preservado | 1.957 linhas = 1.900 contribuições + 57 pendências Atlas; comissão **R$ 203.735,34** |
| Saída alvo A4 | 35 comissões, 115 divergências, 21 propostas, 81 pendências, 4.894 rastros; zero classificados |
| Isolamento anterior | Todos os registros A1–A3 idênticos aos de `saida/alvo-a3/`, excluindo somente os novos IDs NOTA:/SEM_NOTA: |
| Mínimo | Retorno 0; seis CSVs idênticos em bytes aos de `saida/alvo-a1/` |
| Alvo A4 | Retorno 2, PROVISORIO; notas completas e bancos ainda bloqueados |
| Repetição | Seis CSVs e manifesto idênticos em duas pastas novas |
| Preservação | 87 arquivos originais/referências com SHA-256 idêntico antes/depois, incluindo Context, data pack, data/raw, saídas anteriores e os dois documentos oficiais de regras/layout |

O total positivo de checkout nas propostas supera a comissão líquida de checkout em R$ 5,50 porque o saldo negativo permanece separado em pendência. A devolução da Casa é outra natureza e não compõe a nota. Totais conhecidos serviram exclusivamente para validação, sem constantes no motor.

## Testes e matriz de falhas

**176 testes passaram:** os 159 anteriores e 17 novos de A4. Cobrem tomador configurável, CNPJ versus nome, outros meses/datasets, positivos/zeros/negativos, ausência de transporte entre competências, nota única líquida da Ponte, D-10 sem reaplicação de 50%, referências originais, exclusão de duplicatas/negativos irregulares/pendências da soma, dependências provisórias, fontes ausentes, configuração inválida e adulteração em memória e após publicação.

`tests/auditoria_a4.py` usa somente biblioteca padrão, sem importar o motor. A partir dos CSVs de comissão já auditados, reconstrói saldos por identidade/competência, confere o tomador, a discriminação, o conjunto exato de propostas/pendências e cada contribuição/metadado com suas origens. Rejeita adulteração mesmo com hash de saída atualizado. O auditor principal conserva a validação independente das fontes do mínimo/A2/A3.

| Fonte ausente em cópia isolada | Notas checkout | Notas remessa | Auditor |
| --- | --- | --- | --- |
| Ponte | COMPLETO | BLOQUEADO | Retorno 0 |
| Orbe | BLOQUEADO | COMPLETO | Retorno 0 |
| Planilha de taxas | BLOQUEADO | PROVISORIO, preservando o saldo realizado conhecido | Retorno 0 |

No último caso, os pedidos negativos sem contrato permanecem desconhecidos/provisórios em A3 e a proposta herda essa ressalva. O auditor confirma a coerência do resultado parcial; não o transforma em fechamento completo. Testes também confirmam que divergência corrompida não bloqueia proposta válida, e comissão corrompida bloqueia somente suas próprias notas.

## Reprodução e evidências

Com o ambiente já instalado, na raiz:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida/alvo-a4 --regras regras.toml --escopo alvo
.\.venv\Scripts\python.exe tests/validar_saida.py --dados Tarvo_Data_Pack_set2026 --saida saida/alvo-a4 --regras regras.toml --esperar COMPLETO --esperar-fechamento PROVISORIO
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Execução retorna 2 enquanto houver etapas do alvo bloqueadas; auditor retorna 0 para esse estado esperado. Usar um destino novo em reproduções para preservar as evidências. Em macOS/Linux, substituir o executável por `.venv/bin/python`.

Executado em Windows/Python 3.12.10, com o ambiente existente, inclusive fora da raiz, sem PYTHONPATH/PYTHONHOME, chaves ou site-packages do usuário. Nenhuma instalação foi feita nesta sessão; macOS/Linux não foram executados. Evidências: `saida/alvo-a4/` com os seis CSVs e manifesto; `.tmp/aceite-a4/resultado.json`, logs, auditorias, matriz e repetição; `.tmp/testes-a4.log`. `git diff --check` sem erros.

## Limites mantidos

D-10 aguarda confirmação financeira, Atlas aguarda contrato e metadados sem data continuam NAO_INFORMADO. Propostas exigem revisão humana, não significam nota fiscal emitida. A5, A6, A7 e extras não foram implementados; este aceite preserva o mínimo e valida A4, sem declarar o alvo integralmente concluído. Documentos, dados oficiais, gabaritos e saídas anteriores permaneceram intactos.
