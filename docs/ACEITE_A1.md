# Aceite A1 — isolamento de resultados e dependências

**A1 implementada e validada. O mínimo permanece válido; A2 não foi iniciada.** Não foram acrescentados leitores de Ponte/bancos, fórmulas financeiras, dependências de instalação, alterações em regras.toml ou no contrato oficial dos seis CSVs.

## Alteração e contrato

- ResultadoParte descreve fontes, resultados requeridos, relatórios, payload, rastro, cobertura, situação e motivos. partes.py coordena as dependências explícitas e a validação; contratos.py centraliza os layouts antes definidos na exportação.
- CHECKOUT conserva o cálculo e a validação financeira existentes. PENDENCIAS_CHECKOUT é validado separadamente, com as mesmas dependências de dados; falha na soma de comissão não apaga uma pendência válida. Partes futuras ficam bloqueadas como não implementadas.
- Fontes não lidas são NAO_AVALIADA: A1 não afirma que um anexo/banco foi validado ou que falta por inferência de nome. A ausência do relatório Ponte não altera o checkout; o leitor e sua detecção definitiva pertencem à etapa correspondente.
- Validação do contrato monetário, cobertura e rastro por parte. Uma falha bloqueia a produtora e seus dependentes, preservando partes independentes. Colisão de id_saida bloqueia os produtores envolvidos. O isolamento é por parte (por exemplo CHECKOUT ou EXTRATO_AURORA), não por lojista dentro de uma mesma parte.
- Publicação composta inclui só partes validadas; CSV sem produtor válido tem apenas cabeçalho. O manifesto final lista os hashes da execução. Erro físico de escrita mantém o marcador de publicação global bloqueado, sem apresentar arquivos parcialmente substituídos como válidos.

## Escopos e compatibilidade

| Campo / comando | Significado |
| --- | --- |
| Sem --escopo, ou --escopo checkout | Exige CHECKOUT + PENDENCIAS_CHECKOUT; preserva o resultado normal do mínimo |
| --escopo alvo | Exige todas as partes declaradas; não ativa leitores ou cálculos futuros |
| Códigos 0 / 2 / 1 | Todas as partes exigidas completas / há parte válida e alguma incompleta / todas bloqueadas; erros de uso/escrita também retornam 1 |
| situacao, escopo_situacao, rastro_validado, total_parcial_brl | Campos legados: continuam exclusivamente relativos ao checkout |
| situacao_comando, escopo_comando | Conclusão usada pelo código de saída; pode ser provisória se comissão ou pendência falhar isoladamente |
| fechamento | Sempre o agregado do alvo, inclusive etapas futuras: completo se todas completas, bloqueado se todas bloqueadas e provisório nos demais casos |
| partes | Dependências, estado observado das fontes, implementação, validação, cobertura e motivos de cada parte |
| resultados | Produtores por CSV, partes bloqueadas, situação no escopo e situacao_alvo; só parcelas validadas entram nos arquivos |

Manifesto versão **3**, etapa ALVO_A1. Dados e ordenação do mínimo permanecem os mesmos; metadados foram ampliados. A cobertura global conta somente destinos validados, registrando como bloqueadas as origens cujo destino perdeu validade. As contagens de partes derivadas não devem ser somadas como se fossem novas linhas de entrada.

## Execução e regressão com os dados reais

| Verificação | Resultado observado |
| --- | --- |
| Competência | 2026-09, derivada dos movimentos |
| Cobertura | 1.957 linhas = 1.900 contribuições + 57 pendências da Atlas; nenhuma sem destino |
| Comissões | 21 lojistas, R$ 203.735,34 |
| Pendências / rastro | 57 pendências e seus 57 rastros; 1.957 registros de rastro no total; valores de pendência separados das comissões |
| Comparação ao mínimo anterior | **Seis CSVs idênticos em bytes** aos de saida/revisao-pre-alvo/ |
| Repetição | Seis CSVs e manifesto idênticos em bytes em duas pastas distintas |
| Padrão checkout | Checkout e pendências completos, retorno 0; alvo agregado provisório |
| Escopo alvo | Mesmo conteúdo financeiro, retorno 2; sete partes futuras bloqueadas, sem simular conclusão do alvo |
| Sem fontes do alvo | Pasta só com os dois CSVs Orbe e taxas gera o mesmo manifesto do mínimo e mantém retorno 0 |
| Sem taxas | Retorno 1 em alvo; todas as partes bloqueadas; seis cabeçalhos e total checkout null |
| Checkout corrompido em memória | Só CHECKOUT bloqueado; pendências continuam completas e publicadas; 57 pendentes e 1.900 origens bloqueadas na cobertura, total checkout null |
| Fontes | Hashes antes/depois iguais; dados originais e evidências anteriores preservados |
| Tempos de duas execuções | 1.5882 s e 1.4497 s, incluindo inicialização |

A corrupção acima foi injetada no resultado em memória, nunca nos arquivos originais. O auditor independente validou as saídas normais, o escopo alvo, o bloqueio total e a preservação das pendências com checkout bloqueado. --esperar conserva o significado de expectativa do checkout; --esperar-fechamento verifica o agregado do alvo.

## Testes e ambiente

**115 testes passaram**, incluindo os 100 testes anteriores atualizados apenas onde A1 muda o bloqueio global para isolamento. Casos novos cobrem códigos de escopo, Ponte ausente/não lida, corrupção isolada de comissão ou pendência, dependentes bloqueados, fonte de um banco ausente, rastro bancário inválido, plano ausente, contribuição independente sem tabela de taxas, esquema inválido, colisão de IDs, ciclo de dependências e agregação completa/parcial/bloqueada. Os casos bancários e de remessa usam payloads normalizados sintéticos; não implementam nem validam regras desses produtos.

Windows, Python 3.12.10, openpyxl 3.1.5 e et-xmlfile 2.0.0; pip check sem inconsistências. Ambiente virtual existente reutilizado, sem nova instalação nesta sessão. Subprocessos rodaram fora da raiz do código, sem PYTHONPATH/PYTHONHOME, site-packages do usuário ou chaves de API. macOS/Linux têm instruções no README, mas não foram executados nesta revisão.

## Pendências financeiras e limite de escopo

- Contrato da Atlas continua pendente para o Comercial; D-07 sobre apresentação já está aplicada.
- D-10 conserva a decisão do time de usar 50% e a pergunta financeira ainda aberta sobre a natureza do ajuste; nenhuma remessa foi calculada.
- Datas de aprovação não documentadas continuam NAO_INFORMADO; não se fabricaram aprovações.
- RN-64 e a interpretação RN-13/RN-65 permanecem registradas, sem cálculo de devolução da Casa ou alteração do estorno histórico.
- Divergências, notas, devoluções, remessas e classificação bancária continuam bloqueadas em produção. A2 exige nova autorização; nenhuma etapa seguinte foi iniciada.

## Evidências

saida/alvo-a1/ contém os seis CSVs, manifesto, aceite.json com hashes de código/fontes/saídas, testes.log e logs das execuções/auditorias. .tmp/aceite-alvo-a1/ preserva repetição, escopo alvo, pasta sem Ponte, bloqueio total e corrupção isolada. Os diretórios de evidência continuam sujeitos ao .gitignore existente; presença local não implica versionamento. Nenhum commit, push ou alteração de branch.
