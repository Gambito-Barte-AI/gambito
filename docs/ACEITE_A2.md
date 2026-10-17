# Aceite A2 — divergências de checkout e devolução da Casa

Implementação autorizada pelo usuário em 17/10/2026, limitada a A2. A arquitetura modular e o isolamento de A1 foram preservados; A3 e etapas seguintes não foram implementadas. Nenhum commit foi criado.

## Decisão confirmada durante a implementação

O confronto das fontes revelou que a referência anterior da Casa (118 linhas / R$ 15.396,77) incluía o estorno TX88446763, de −R$ 9,08. As vendas e antecipações elegíveis somam 117 linhas / R$ 15.405,85. Consultado sobre o recorte, o usuário respondeu: **“Não, manter apenas vendas e antecipações; revisar a referência documental.”**

Aplicado esse recorte: nenhum estorno integra a devolução, inclusive o de setembro. O estorno da venda de agosto permanece fora da devolução e sua comissão negativa continua preservada. `regras.toml`, README, HIPOTESES e a referência oficial `documentação-geral.md` registram a revisão e a origem da aprovação; o valor anterior permanece explicado como histórico. A confirmação do usuário não foi atribuída ao Financeiro no Slack. Totais e quantidades não são constantes de cálculo.

## Alterações

- Orbe preserva taxa aplicada e cobrança efetiva. Campo financeiro adicional ausente ou inválido gera revisão na análise dependente, sem eliminar automaticamente o evento contratual do mínimo.
- `divergencias.py` recebe eventos e contribuições com identidade, faixa e vigência já resolvidas. Compara taxas, calcula bruto × diferença das frações e arredonda HALF_UP por linha. Taxa menor também diverge, estorno conserva sinal negativo, truncamento com mesma taxa não diverge.
- Cada divergência tem origem e rastro próprios. Na pendência agregada, ref_origem é um id_transacao real representativo (primeiro na ordenação), com arquivo/linha correspondentes; todas as operações estão no rastro pelo id_saida, sem inventar um identificador composto na coluna oficial. Contestação líquida por competência/lojista é outra pendência, reconciliada com suas operações. Casa isenta é concessão separada; Atlas sem contrato não recebe taxa presumida nem divergência calculada.
- Devolução da Casa agrega o efetivamente cobrado menos a comissão contratada nas vendas/antecipações isentas. Pendência com total e detalhe no rastro; nenhuma linha opcional de concessão é exportada nas divergências.
- DIVERGENCIAS_CHECKOUT e DEVOLUCAO_CASA têm estados, cobertura e validação independentes, usando as fontes Orbe/taxas/regras. Falha em uma análise ou em seu rastro preserva as partes irmãs válidas. Nenhum pagamento, contestação externa ou emissão de nota é executado.
- Manifesto versão 4, etapa ALVO_A2. Escopo padrão continua CHECKOUT + PENDENCIAS_CHECKOUT; `--escopo alvo` publica também A2. Produtor fora do escopo não aparece como relatório publicado e concluído. Contrato dos seis CSVs e colunas obrigatórias preservado.

## Resultados com os arquivos atuais

Entradas: pasta `Tarvo_Data_Pack_set2026`, incluindo todos os CSVs Orbe reconhecidos por conteúdo (01 e 06), XLSX e `regras.toml`.

| Verificação | Resultado observado |
| --- | --- |
| Competência / cobertura física do mínimo | 2026-09; 1.957 = 1.900 contribuições + 57 pendências Atlas, zero sem destino |
| Comissão checkout | 21 lojistas; R$ 203.735,34 |
| Regressão do mínimo | Seis CSVs idênticos em bytes aos de `saida/alvo-a1/`; comando padrão retorna 0 |
| Divergências checkout | 92 operações; R$ 1.576,23 líquidos; inclui quatro estornos negativos |
| Bridge | 5 divergências; R$ 29,95 |
| Rota Global | 87 divergências; R$ 1.546,28 |
| Casa | 117 vendas/antecipações; pendência R$ 15.405,85; dois estornos excluídos da devolução |
| Pendências no escopo alvo | 60 = 57 Atlas + 2 contestações líquidas Orbe + 1 devolução Casa |
| Rastro no escopo alvo | 2.258 = 1.900 comissões + 57 Atlas + 92 divergências + 92 detalhes de contestação + 117 devolução |
| Partes implementadas | CHECKOUT, PENDENCIAS_CHECKOUT, DIVERGENCIAS_CHECKOUT e DEVOLUCAO_CASA completos |
| Fechamento alvo | PROVISORIO, retorno 2: seis partes futuras bloqueadas, sem simular sua conclusão |
| Determinismo | Seis CSVs e manifesto idênticos em duas pastas distintas |
| Fontes | Hashes antes/depois iguais; entradas e evidências anteriores preservadas |

As contagens derivadas do rastro não são novas linhas de entrada. Valores de comissão, cobrança de referência, diferença contratual e devolução são naturezas distintas e não devem ser somados como receita.

## Reprodução e verificação

No ambiente instalado, a partir da raiz:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida/alvo-a2 --regras regras.toml --escopo alvo
.\.venv\Scripts\python.exe tests/validar_saida.py --dados Tarvo_Data_Pack_set2026 --saida saida/alvo-a2 --regras regras.toml --esperar COMPLETO --esperar-fechamento PROVISORIO
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

O primeiro comando retorna 2 enquanto as etapas futuras estiverem bloqueadas; o auditor retorna 0 ao confirmar esse resultado parcial esperado. Em macOS/Linux, substituir o executável por `.venv/bin/python`.

**128 testes passaram** (115 existentes e 13 de A2). Novos casos verificam taxa igual com truncamento, diferença arredondada a zero, taxas maiores/menores, HALF_UP negativo, contestação líquida, vigência pela data original, faixa própria do estorno, limites da isenção, antecipação, exclusão de ambos os estornos da devolução, campos financeiros inválidos sem zero inventado, falha isolada de análise/rastro/comissão e adulteração da fórmula mesmo com rastro reconciliado. Log completo: `.tmp/testes-a2.log`. `git diff --check` sem erros.

Evidência principal: `saida/alvo-a2/manifesto.json` e seis CSVs. Verificações adicionais em `.tmp/aceite-a2/resultado.json`, logs e auditorias dessa pasta; execução repetida em `.tmp/aceite-a2/alvo-repeticao/`. O mínimo atual está em `.tmp/aceite-a2/minimo/`. Esses diretórios locais são ignorados pelo Git, conforme a configuração existente.

O comando instalado foi executado fora da raiz do código, sem PYTHONPATH/PYTHONHOME, chaves de API ou site-packages do usuário. Ambiente existente reutilizado, sem instalar dependências. Windows, Python 3.12.10; macOS/Linux têm instruções, mas não foram executados nesta sessão.

O auditor independente usa apenas biblioteca padrão, sem importar o motor: verifica fontes/hashes, contratos CSV, cobertura física do mínimo, fórmulas de divergência pelas fontes, vigências e origens resolvidas, contestação líquida, recorte da devolução, cobrança efetiva, completude contra contribuições publicadas e somas por natureza. A seleção contratual original continua coberta pelos testes do checkout.

## Pendências e limite do aceite

- Atlas: confirmação de contrato pelo Comercial segue pendente. D-07 está aplicada e D-13 preservada: pendência de negócio não torna a parte automaticamente provisória.
- D-10: natureza financeira do ajuste Ponte segue aguardando confirmação; a decisão do time de 50% não é apresentada como ratificação financeira. Nenhuma remessa calculada.
- Datas não documentadas continuam NAO_INFORMADO. D-08 não foi reaberta; base pelo cobrado e recorte explícito da Casa estão registrados separadamente.
- Aceite de A2 e regressão do mínimo não significam aceite integral do alvo. Notas, Ponte, extratos e extras continuam futuros.
