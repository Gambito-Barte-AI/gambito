# Aceite A5 — plano de contas e Aurora

A5 autorizada pelo usuário e implementada em 17/10/2026, seguindo AGENTS.md. Preservados o mínimo, A1–A4, a RN-64 corrigida, D-10 pendente e os materiais oficiais. A6 não iniciada; nenhuma dependência instalada, integração externa, commit ou alteração de branch realizada pelo agente.

## Implementação e regras

- `leitores/plano_contas.py`: identifica o CSV Fênix pelo cabeçalho, lê o encoding original e valida códigos, duplicidades, descrição, tipo, natureza e aceitação de lançamento. Conta sintética ou sem permissão nunca é utilizada. Mais de um candidato bloqueia a dependência, sem selecionar por nome de arquivo.
- `leitores/aurora.py`: encontra o cabeçalho bancário, normaliza datas/valores para tipos próprios e preserva descrição, sinal, arquivo e linha física inicial. O primeiro movimento do exemplo é L9; preâmbulo variável e registros multilinha não provocam deslocamento artificial. Saldos e rodapé conhecidos ficam explícitos no inventário; linhas posteriores desconhecidas são pendências, sem descarte silencioso.
- `classificacao.py`: uma regra configurada deve corresponder ao histórico normalizado e ao sinal; conta precisa existir, ser ANALITICA e aceitar lançamento. Nenhuma correspondência ou várias correspondências gera pendência de negócio. Dados inválidos ou conta indisponível tornam Aurora provisório. Valor desconhecido fica vazio, sem rastro monetário inventado.
- RN-46 a RN-48/RN-50: contrapartida correta; pagamentos de folha, INSS, FGTS, ISS e DARFs conhecidos baixam passivos. Despesas conhecidas são classificadas conforme o plano; não são criadas provisões. RN-56: créditos Orbe baixam recebíveis; não há conciliação parcela a parcela nem inferência de receita pelo crédito/saldo bancário.
- RN-52/RN-53/D-06: crédito sem identificação em transitória e repasse devolvido ainda devido ao lojista, ambos com pendência de revisão. A regra de devolução limita-se à contraparte confirmada, sem estender a natureza a qualquer retorno de Pix. Transferência própria exige o destino configurado; não confirma a chegada no outro banco. Históricos novos exigem revisão, sem identificação por semelhança de nome.
- RN-58/RN-61: motivo, próximo passo, responsável, fonte, aprovador/papel e data registrados. O TOML distingue critério financeiro e interpretação técnica da conta, sem aprovação individual fictícia. D-04 e D-06 passam a constar nas decisões documentadas; datas sem evidência continuam NAO_INFORMADO.

Mantidos monólito modular, CLI, Decimal, TOML e os seis layouts. Acrescentados ContaContabil/MovimentoBanco, dois leitores e um módulo de classificação. Não houve mudança nas fórmulas financeiras existentes. Manifesto versão 7, etapa ALVO_A5; campos legados continuam exclusivos do checkout. Nenhum código, nome, valor, data ou total do exemplo foi incorporado como condição fixa ao motor; critérios específicos documentados ficam na configuração.

## Isolamento e integridade

EXTRATO_AURORA depende somente de Aurora, plano e regras. Sua competência vem das próprias datas; vários meses exigem seleção explícita. Registros com data inválida continuam no recorte para revisão. Falhas de checkout/Ponte não impedem Aurora; falhas de plano/Aurora não impedem A1–A4. A publicação revalida a projeção contra o contexto normalizado e bloqueia somente a parte adulterada.

Cada movimento selecionado tem um destino principal, classificado ou pendente. As duas pendências adicionais de revisão não duplicam a cobertura física. Classificação e pendência monetária têm IDs/naturezas próprios e rastro assinado. O classificado também aponta à regra e à linha da conta no plano.

`tests/auditoria_a5.py` relê plano, Aurora e regras com biblioteca padrão, sem importar tarvo. Confere hashes, inventário físico, competência, destinos, contas permitidas, regras, datas, descrições, sinais, valores, rastros e cobertura. O auditor principal também foi ajustado para não exigir competência de checkout bloqueado sem movimentos no recorte; continua proibida a publicação de suas comissões. Isso permite auditar Aurora válido de outro mês sem mudar o comportamento ou as fórmulas do mínimo.

## Resultados conferidos nas fontes

| Verificação | Resultado |
| --- | --- |
| Plano Fênix | 52 contas lidas; somente contas analíticas permitidas usadas |
| Aurora | **84 movimentos**, todos classificados; primeiro L9, último L92 |
| Valor assinado dos movimentos | **−R$ 2.532.423,41**, preservado exatamente |
| Pendência L50 | Crédito sem identificação, R$ 7.350,00, conta 1.1.09.002; sem receita |
| Pendência L65 | Repasse devolvido, R$ 12.400,00, conta 2.1.01.001, conforme D-06 |
| Folha e impostos | Classificados em passivos; nenhuma provisão criada |
| Atlas | Repasses bancários classificados independentemente do contrato de checkout pendente |
| RN-64 preservada | **R$ 15.396,77**, com 118 origens; estorno elegível abatido e agosto fora da devolução |
| Saídas A5 | 35 comissões, 115 divergências, 21 propostas, 84 classificados, 83 pendências, 4.980 rastros |
| Regressão do mínimo | Retorno 0; seis CSVs idênticos em bytes aos de `saida/alvo-a1/` |
| Regressão A1–A4 | Todos os registros idênticos aos de `saida/alvo-a4/`, excluindo somente os novos IDs AURORA:/PENDENCIA_AURORA: |
| Alvo | Retorno 2, PROVISORIO: EXTRATO_AURORA completo, Meridiano bloqueado como não implementado |
| Determinismo | Seis CSVs e manifesto idênticos em duas pastas novas |
| Tempo da execução alvo no ambiente | 1,423 segundo, incluindo subprocesso e publicação; observação desta execução, sem garantia para outros volumes |
| Integridade | **94 arquivos oficiais/referências** com hashes SHA-256 idênticos antes/depois |

As contagens e os valores foram calculados/confrontados com as fontes e servem como evidência, nunca como constantes de processamento. A referência documental de 184 movimentos é dos bancos no alvo, não uma quantidade fixada para Aurora. Classificados e fechamento integral continuam PROVISORIO porque Meridiano ainda está fora desta entrega.

## Testes e reprodução

**197 testes passaram**, sendo os 176 anteriores e 21 novos de A5. A suíte direcionada de A5 também passou após o ajuste do auditor para o checkout bloqueado por ausência de movimentos no recorte. Cobrem encoding, nomes livres, referência física, preâmbulo deslocado, descrição multilinha, contas ausentes/sintéticas/proibidas, duplicidade no plano, múltiplos candidatos, metadados obrigatórios, regex inválida, sinais, zero, históricos novos/sobrepostos, recorte mensal independente, linhas/rodapés inválidos, origem sem valor, ausência de fontes, preservação/determinismo e adulteração coerente de valor/conta/data. O auditor rejeita conta alterada mesmo com hash da saída atualizado.

Os testes de coordenação de A1 continuam usando resultados bancários sintéticos e isolam a validação de domínio de A5; os testes novos exercitam os leitores e o domínio reais. Nenhum teste edita materiais oficiais: entradas modificadas são sintéticas ou cópias isoladas.

| Matriz executada com cópias isoladas | A1–A4 | Aurora | Auditor |
| --- | --- | --- | --- |
| Sem Aurora | Disponíveis | BLOQUEADO | Retorno 0 |
| Sem plano Fênix | Disponíveis | BLOQUEADO | Retorno 0 |
| Somente plano e Aurora | Bloqueados pelas próprias fontes ausentes | COMPLETO | Retorno 0 |

Execução instalada fora da raiz, sem PYTHONPATH/PYTHONHOME, chaves ou site-packages do usuário; Windows/Python 3.12.10, ambiente já existente. Nenhuma instalação realizada; macOS/Linux não executados.

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida/alvo-a5 --regras regras.toml --escopo alvo
.\.venv\Scripts\python.exe tests/validar_saida.py --dados Tarvo_Data_Pack_set2026 --saida saida/alvo-a5 --regras regras.toml --esperar COMPLETO --esperar-fechamento PROVISORIO
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Primeiro comando retorna 2 e auditor retorna 0 ao confirmar esse estado parcial esperado. Usar destino novo em reproduções para preservar referências. Em macOS/Linux, substituir o executável por `.venv/bin/python`. Evidências: `saida/alvo-a5/`, `.tmp/aceite-a5/resultado.json`, logs, auditorias, repetição, matriz e `integridade.json`; `.tmp/testes-a5-final.log` e `.tmp/testes-a5-direcionados.log`. `git diff --check` sem erros de whitespace.

## Limites

D-10 aguarda confirmação financeira; Atlas aguarda contrato; RN-64 permanece corrigida. A5 não lê OFX nem implementa regras específicas de Meridiano (A6), não confirma transferências entre bancos e não declara o alvo integralmente validado. Nenhum pagamento, lançamento externo ou emissão fiscal realizado. Arquivos oficiais, gabaritos, documentos e saídas anteriores preservados integralmente.
