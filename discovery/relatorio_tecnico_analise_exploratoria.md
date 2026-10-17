# Análise exploratória dos dados do fechamento financeiro da Tarvo

**Projeto:** Gambito — Desafio Barte AI  
**Competência analisada:** setembro de 2026  
**Data da consolidação:** 17 de outubro de 2026

## 1. Objetivo e delimitação

A análise exploratória teve como objetivo identificar as condições necessárias para transformar os arquivos operacionais da Tarvo em resultados de fechamento reproduzíveis, contabilmente coerentes e rastreáveis. O trabalho examinou a estrutura das fontes, a integridade dos registros, as relações entre operações e as exceções que interferem no cálculo de comissões e na classificação dos movimentos bancários.

A investigação foi organizada em cinco notebooks, do inventário do ambiente à incorporação dos ajustes tardios da Orbe. Os resultados foram interpretados à luz da [documentação de negócio](../docs/documentação-geral.md), especialmente das regras de identidade, comissão, competência, classificação contábil e fechamento parcial.

Este relatório distingue três níveis de evidência: resultados calculados nos notebooks; tratamentos definidos pelo financeiro ou pelo time na documentação; e requisitos cuja implementação ainda precisa ser validada no motor. A execução dos notebooks não representa, por si só, aprovação do fechamento ou validação integrada dos seis CSVs obrigatórios.

## 2. Procedimentos de análise

Foram examinados o relatório original da Orbe, a planilha de taxas vigentes, o e-mail da Ponte e seu anexo, os extratos Aurora e Meridiano, o plano de contas Fênix e o arquivo adicional de ajustes tardios.

Os procedimentos compreenderam inspeção de formatos e encodings, identificação de cabeçalhos e campos, contagem de registros, verificação de duplicatas, análise de referências e conferência de identidades aritméticas. Na análise bancária e nos cálculos incrementais, os valores monetários foram tratados com `Decimal`. O arredondamento das comissões foi realizado por linha com `ROUND_HALF_UP`, conforme RN-09.

As fontes foram mantidas intactas. As referências de origem foram preservadas por meio de `id_transacao` na Orbe, número da operação na Ponte, linha física no Aurora e FITID no Meridiano. Os notebooks também registram hashes das fontes utilizadas, permitindo identificar a versão dos arquivos analisados.

## 3. Identidade dos lojistas e qualidade contratual

A principal restrição à integração é a ausência de uma chave comum a todas as fontes. A Orbe identifica estabelecimentos por EC; a planilha contratual utiliza CNPJ; os extratos apresentam históricos com nomes frequentemente truncados. A existência de múltiplas grafias para o mesmo EC demonstra que o nome não deve ser utilizado como chave de identidade.

A planilha também combina percentuais numéricos em formato de fração e percentuais escritos como texto. A vigência dos contratos aparece como data inicial, limite final ou expressão textual. Essas diferenças exigem normalização explícita: converter valores sem reconhecer sua unidade pode alterar a taxa em cem vezes; selecionar um contrato sem considerar sua vigência pode aplicar uma condição comercial incorreta.

Os vínculos ausentes devem seguir as associações aprovadas na RN-05. A aba antiga pode apoiar a identificação da Atlas, mas não fornecer sua taxa vigente, conforme RN-07. A ausência de contrato é uma pendência comercial, não uma autorização para estimar a comissão ou recuperar uma taxa desatualizada.

**Consequência para a solução:** a resolução de identidade e contrato precisa anteceder o cálculo. O cadastro deve preservar a fonte do vínculo, a vigência e a decisão que autoriza seu uso. Nomes podem apoiar a inspeção; não substituem uma associação documentada.

## 4. Relatório original da Orbe

O relatório original contém 1.943 movimentos:

| Tipo de lançamento | Quantidade |
|---|---:|
| Venda | 1.840 |
| Estorno | 59 |
| Antecipação | 38 |
| Reversão de antecipação | 6 |
| **Total** | **1.943** |

Não foram identificados IDs de transação duplicados nem diferenças na identidade `valor_bruto − valor_taxa = valor_liquido`. Esse resultado sustenta a consistência aritmética dos campos, mas não comprova que as taxas aplicadas correspondam aos contratos.

Dos 59 estornos, 50 possuem referência localizada no relatório e nove apontam para operações ausentes desse arquivo. As seis reversões de antecipação possuem referência presente. A ausência de uma venda no arquivo mensal não torna seu estorno inválido: a operação original pode pertencer a outra competência. O motor precisa distinguir ausência de histórico, incompatibilidade de referência e impossibilidade efetiva de calcular a taxa contratada.

A comissão da Tarvo deve ser calculada pelo bruto e pela taxa contratada, conforme RN-08. O valor de taxa informado pela adquirente é uma observação do que foi cobrado. Sua igualdade com o cálculo contratual não pode ser presumida.

No estorno, a competência é determinada pela data do próprio movimento, enquanto a vigência contratual considera a data da venda original, conforme RN-13. Modalidade e parcelas são obtidas da própria linha do estorno, conforme RN-10. Confundir essas funções das datas pode deslocar indevidamente o resultado entre meses ou aplicar a taxa errada.

## 5. Ajustes tardios e alteração da base de fechamento

O arquivo adicional contém 14 movimentos: dez estornos, três reversões de antecipação e uma venda. Nenhum ID se repete dentro do lote ou em relação à base original. As 13 referências foram localizadas de forma única no relatório principal, com coerência de EC, tipo e data. Os valores observados de bruto, taxa e líquido são opostos aos das operações referenciadas. Não houve excesso de reversão acumulada sobre os valores originais verificados.

A consolidação resulta em 1.957 movimentos. O impacto incremental calculado sobre a comissão, utilizando os contratos e as regras aplicáveis, é de **−R$ 3.304,39**, distribuído entre sete estabelecimentos.

| Medida | Resultado | Interpretação |
|---|---:|---|
| Movimentos adicionais | 14 | Ampliação da base do fechamento |
| Comissão incremental calculada | −R$ 3.304,39 | Efeito contratual dos ajustes |
| Soma de `valor_taxa` no adicional | −R$ 3.304,32 | Valor observado na Orbe |
| Diferença entre os dois resultados | R$ 0,07 em magnitude | Reforça a necessidade de cálculo próprio por linha |
| Novas divergências de taxa no lote | 0 | As taxas aplicadas coincidem com as contratadas nas linhas calculadas |

A documentação registra comissão de checkout de referência de R$ 207.039,73 antes do adicional e R$ 203.735,34 após sua inclusão. A diferença coincide com o impacto incremental apurado. Essa correspondência constitui uma conferência auxiliar: o notebook 04 calculou o delta, sem refazer integralmente o fechamento e suas exceções comerciais.

A RN-65 confirma que os ajustes entram na competência da `data_movimento`. Sua chegada tardia não configura, isoladamente, erro ou bloqueio. O RF-22 exige reconhecer todos os arquivos Orbe pelo cabeçalho, sem depender do nome do relatório principal.

O ensaio de reenvio confirmou que entregar o mesmo lote novamente não amplia a base consolidada nem altera seus totais. O notebook também verificou a criação de pendências no cenário de repetição, conforme RN-65. Os cenários de divergência com estorno negativo e taxa inferior à contratada foram testados com dados sintéticos; não representam ocorrências adicionais nos arquivos reais.

**Consequência para o negócio:** uma execução encerrada antes da chegada dos ajustes pode produzir comissões e notas desatualizadas. A solução precisa identificar as fontes de cada execução, recalcular os resultados afetados e impedir que um lote já incorporado seja somado novamente.

## 6. Relatório de remessas da Ponte

O anexo da Ponte apresenta 233 linhas e 232 números de operação distintos. Uma operação aparece duas vezes, com a segunda ocorrência identificada como reprocessada. As duas linhas devem permanecer no histórico de ingestão; a apuração financeira deve considerar uma única operação, acompanhada de pendência para correção do relatório, conforme RN-34.

| Base examinada | Linhas | Soma do spread |
|---|---:|---:|
| Relatório integral | 233 | R$ 78.073,59 |
| Cenário com uma ocorrência por operação | 232 | R$ 77.251,71 |

A diferença de R$ 821,88 corresponde ao spread da ocorrência repetida. Esses totais ainda incluem spreads negativos e não constituem a base final de comissão aprovada.

Foram identificadas quatro operações com spread negativo, somando **−R$ 1.834,05**, associadas à observação de taxa travada no pedido. A RN-35 determina sua exclusão da comissão e da nota, com pendência que explicite o valor reportado e a diferença até o contrato. A decisão D-11 define como esses valores devem ser apresentados. Não se deve confundir esse evento com ajustes posteriores identificados por “AJUSTE REF”, cujo tratamento é distinto na RN-37.

Seis operações apresentam contratação em setembro e liquidação em outubro. Para a comissão de remessa, prevalece a contratação, conforme RN-33. Utilizar a liquidação deslocaria essas operações para uma competência inadequada.

O notebook 02 preserva a exploração anterior à consolidação das regras finais. Seus cenários ajudam a demonstrar os efeitos das duplicatas e dos negativos, mas não substituem a execução do cálculo final com todas as regras de remessa.

## 7. Extratos bancários e plano de contas

A normalização preservou 184 movimentos: 84 do Aurora e 100 do Meridiano. O encadeamento de saldos do Aurora foi verificado sem divergências:

| Componente | Valor |
|---|---:|
| Saldo inicial | R$ 612.334,81 |
| Movimentação líquida | −R$ 2.532.423,41 |
| Saldo final | −R$ 1.920.088,60 |

O saldo negativo não deve ser interpretado como erro de leitura: a RN-56 o associa à conta garantida. A mesma regra exclui a conciliação parcela a parcela da Orbe contra o banco do escopo da solução.

No Meridiano, o saldo final é de R$ 1.320.453,26. O saldo inicial implícito, calculado a partir dos movimentos, é de R$ 204.118,03. Como não há saldo anterior independente no extrato analisado, esse cálculo não constitui validação externa do saldo inicial.

O plano Fênix contém 52 contas, das quais 32 aceitam lançamento. A verificação estrutural não identificou inconsistências nos vínculos hierárquicos ou na relação entre tipo de conta e aceitação de lançamentos. A existência de uma conta analítica é condição necessária, mas não suficiente, para justificar sua utilização: a contrapartida deve representar a natureza econômica do movimento, conforme RN-46.

### 7.1 Tratamentos definidos pelas regras finais

| Evento | Tratamento | Implicação operacional |
|---|---|---|
| Folha e tributos pagos | Baixa do passivo provisionado — RN-47 | Evitar reconhecimento duplicado de despesa |
| Comissão anterior recebida da Ponte | Baixa de comissão a receber — RN-49 | Separar recebimento de receita da competência corrente |
| Tarifas, aluguel, cloud, assinaturas e serviços | Despesa do mês — RN-50 | Aplicar padrões documentados de contrapartida |
| PIX de R$ 7.350 sem identificação | Conta 1.1.09.002, com pendência — RN-52 | Não reconhecer receita sem sustentação |
| Devolução de PIX de R$ 12.400 | Conta 2.1.01.001 — RN-53 e D-06 | Preservar a obrigação ainda devida ao lojista e investigar o motivo |
| Transferência de R$ 300 mil | Conta 1.1.09.001, em trânsito — RN-54 | Não tratar ausência de par no mês como perda financeira |
| PIX de R$ 18.240 da Ponte Aérea | Conta 2.1.02.001 — RN-55 | Reconhecer recursos para remessa, sem confundir o lojista com a Ponte Câmbio |

A análise bancária identificou uma transferência sem par no período, compatível com o caso de trânsito posteriormente confirmado pelo financeiro. A entrada em outubro é informação documental; não foi verificada em um extrato de outubro nesta análise.

O notebook 03 foi elaborado antes da disponibilização das regras finais e ainda contém a classificação de todos os movimentos como hipóteses, com 184 pendências de validação documental. Essa contagem é um estado histórico da exploração, não uma mensuração atual de exceções reais. As contas candidatas e as pendências precisam ser revistas conforme a documentação final; em particular, a decisão D-06 prevalece sobre a conta inicialmente sugerida para a devolução.

## 8. Dimensão de negócio e governança

Os achados indicam que a dificuldade do fechamento não se restringe à heterogeneidade dos arquivos. A identidade fragmentada dos lojistas, a vigência contratual em texto livre e as condições comerciais fora da planilha afetam diretamente a atribuição de receitas, a emissão de notas e a identificação do responsável por uma diferença.

A distinção entre divergência contratual e concessão comercial é especialmente relevante. A documentação final trata a isenção da Casa do Estudante como devolução suportada pela Tarvo, separada da cobrança à Orbe. O valor de referência de R$ 15.396,77 decorre do que foi efetivamente descontado nas linhas elegíveis, conforme RN-64. Esse valor não foi recalculado integralmente nos notebooks revisados e não deve ser apresentado como resultado independente desta exploração.

Da mesma forma, os R$ 2.995,08 de divergências contratuais registrados na documentação são referência de negócio, não um total integralmente reproduzido pela análise incremental. O adicional não introduziu novas divergências nas linhas examinadas; essa conclusão não equivale a revalidar todas as divergências anteriores.

A solução deve manter separadas as responsabilidades: comercial para cadastro, contrato e condições; financeiro para classificação, contestação, regras de fechamento e liberação. Uma pendência precisa permitir uma ação: identificar as operações, explicar o motivo, quantificar o valor correspondente e indicar o próximo passo.

Uma pendência de negócio prevista pelas regras, como ausência de contrato da Atlas, não torna automaticamente toda a execução provisória. O estado do resultado deve refletir suas dependências e validações, conforme D-13. Ausência de informação não pode ser representada como valor zero calculado.

## 9. Requisitos de implementação derivados da exploração

| Prioridade | Requisito | Justificativa e critério de verificação |
|---|---|---|
| 1 | Ingestão de múltiplos arquivos Orbe por layout | Relatório e adicional devem compor a mesma base, com origem preservada e sem depender de nome mensal |
| 1 | Identidade e contrato resolvidos antes do cálculo | Toda contribuição deve possuir vínculo aprovado, faixa e vigência; ambiguidades geram pendência |
| 1 | Controle de referências e reenvios | Mesmo ID conta uma vez; conflitos de conteúdo exigem revisão; nenhuma ocorrência bruta desaparece |
| 1 | Cálculo monetário por contribuição | Decimal e arredondamento por linha; reversão vinculada à antecipação; comparação de taxas separada do truncamento |
| 1 | Rastro validado antes da publicação | Soma das contribuições por `id_saida` igual ao valor publicado; vínculos documentais não duplicam valores |
| 2 | Atualização da análise e classificação bancária | Aplicar RN-46 a RN-57 e D-06; distinguir conta bancária de contrapartida e classificar somente contas permitidas |
| 2 | Tratamento final de remessas | Duplicata, spread negativo irregular e ajuste posterior precisam seguir regras distintas |
| 2 | Reavaliação de notas após ajustes | Recalcular o saldo mensal por lojista; saldo não positivo não gera nota, conforme RN-43 |
| 2 | Manifesto e fechamento parcial | Registrar fontes, hashes, regras, cobertura e estado dos resultados; não reapresentar saída antiga como nova |

Para `rastro.csv`, a contribuição deve corresponder à natureza da saída: comissão para resultados de comissão; divergência para resultados de divergência; valor bancário para lançamentos. O valor bruto não pode ser utilizado indistintamente como rastro de qualquer resultado. O arquivo e a referência devem compor a identidade de auditoria; uma linha como L9 não identifica globalmente uma origem sem o arquivo correspondente.

## 10. Conclusão

A exploração estabeleceu uma base verificável para os leitores e para a modelagem dos controles do fechamento. Foram demonstradas a integridade aritmética do relatório original da Orbe, a conservação dos movimentos bancários, a consistência estrutural do plano de contas e a incorporação dos ajustes tardios com rastreabilidade e controle de reenvio.

O resultado financeiro incremental mais relevante foi a redução de R$ 3.304,39 na comissão de checkout. A chegada do arquivo adicional mostrou, no próprio caso analisado, que a completude do fechamento depende das fontes efetivamente recebidas e registradas em cada execução.

A próxima etapa é converter essas verificações em componentes do motor e validar o fluxo integrado: leitura, identidade, cálculo, pendência, rastro e publicação. Os números de referência devem apoiar a conferência, enquanto o aceite depende da correção por evento, da cobertura das entradas e da igualdade entre cada resultado e suas contribuições de origem.

## Referências internas

- [Inventário e ambiente](00_teste_ambiente.ipynb).
- [Exploração das fontes e da Orbe](01_exploracao.ipynb).
- [Relatório de remessas da Ponte](02_ponte_cambio.ipynb).
- [Extratos e plano de contas Fênix](03_analise_extratos.ipynb).
- [Análise incremental dos ajustes tardios](04_analise_ajustes_tardios.ipynb).
- [Documentação de negócio, regras e arquitetura](../docs/documentação-geral.md), versão das 14h de 17/10/2026.
- [Contrato dos arquivos de saída](../docs/FORMATO_SAIDA.md).
