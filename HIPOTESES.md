# Hipóteses, limites e decisões pendentes

## Escopo autorizado

Arquitetura consolidada e Entregas 1 e 2 autorizadas pelo usuário nesta conversa em 17/10/2026. Escopo atual: identidade, faixas e vigências das vendas de checkout, com rastro. Não implementar alvo nem antecipar estornos, antecipações e reversões da Entrega 3. O `AGENTS.md` do usuário foi relido e preservado.

## Premissas e decisões técnicas da Entrega 1

Registro histórico do primeiro incremento. E1-02 e E1-03 são ampliadas pelas decisões da Entrega 2 abaixo; os demais controles continuam válidos.

| ID | Premissa/decisão | Motivo e impacto |
| --- | --- | --- |
| E1-01 | Consumir somente Orbe e taxas. | Recorte explicitamente aprovado; prevalece sobre RF-02 local que chama a leitura das seis fontes de mínima. Fontes do alvo ausentes não bloqueiam. |
| E1-02 | Calcular somente VENDA simples, com vínculo direto por EC, contrato único, início explícito e sem observação. | Não interpretar condições financeiras ainda não implementadas. Parcelamentos, estornos, antecipações, reversões e condições especiais ficam pendentes. |
| E1-03 | Data isolada em Vigência representa início inclusivo. | Compatível com as linhas simples do case. Venda anterior não é calculada. Vigências textuais e sobreposições ficam para a Entrega 2. |
| E1-04 | Arquivo Orbe com uma competência, derivada de data_movimento. | Múltiplos meses ou ausência de data válida bloqueiam o cálculo. Não escolher mês arbitrário. |
| E1-05 | CSVs mostram somente contribuições calculadas; o manifesto explicita a cobertura parcial. | Nunca apresentar o subtotal como fechamento completo nem comissão desconhecida como zero. Pendências com ID conhecido preservam a referência. |
| E1-06 | Fonte ausente/inválida bloqueia somente dependentes; o manifesto identifica os resultados atuais. | Fechamento parcial informado pelo usuário, atualização posterior ao contexto local. Não cria módulos futuros. |
| E1-07 | Testes com unittest em vez de pytest. | Mesma verificação automatizada, sem adicionar dependência de desenvolvimento ao primeiro incremento. |

## Decisões financeiras ainda pendentes

| ID | Questão | Orientação conhecida | Tratamento nesta entrega |
| --- | --- | --- | --- |
| D-07 | Atlas fora ou zerada nas comissões? | Usuário informou que ambas são opções do time; identidade pode vir da aba antiga, mas taxas não. | Não ratificada. A identidade histórica está implementada; seus eventos continuam pendentes para o Comercial, sem comissão estimada. O arquivo não ganha linha zerada por contrato desconhecido. Isso é tratamento provisório, não decisão sobre apresentação final. Recuperação futura não implementada. |
| D-08 | Ratificar devolução da Casa pelo cobrado e recorte elegível? | Usuário relatou fala de Helena: “o que foi cobrado eu devolvo”; referência corrigida para R$ 15.396,77. Concessão paga pela Tarvo, fora da cobrança à Orbe. | A isenção confirmada é aplicada às vendas por data, independentemente de D-08. Não calcular devolução nem usar valor_taxa como comissão. O estorno anterior à isenção permanece para a Entrega 3. |
| D-10 | Ajuste Ponte deve abater 50%? | Usuário informou nova linha negativa `AJUSTE REF PC-…`, abatendo nossa participação na nota do mês e vinculada ao original. | Fora do escopo. Confirmar se o valor da linha é spread integral ou participação antes de aplicar 50%. |
| P-VALORES | Como representar dois valores da pendência de spread negativo? | Preservar valor reportado e diferença até o contrato solicitada à Ponte. | Definir posteriormente valor_brl, colunas adicionais e valor reconciliado no rastro. |
| P-AJUSTE | Como representar ajuste e operação histórica no rastro? | Preservar a linha atual e o vínculo à operação original, sem dupla contagem. | Definição reservada ao alvo. |

Não se atribuiu aprovação financeira às escolhas técnicas acima. As novas respostas foram fornecidas pelo usuário; não houve consulta direta ao Slack nem contato com integrantes do time.

## Decisões técnicas e fontes da Entrega 2

| ID | Decisão | Fonte e limite |
| --- | --- | --- |
| E2-01 | Resolver EC para CNPJ por vínculo direto ou configuração explícita. | RN-01 a RN-05. Os três ECs complementares vêm de RN-03; CNPJs conferidos nas linhas vigentes do XLSX. Nomes semelhantes não são evidência de vínculo. |
| E2-02 | Usar taxas das faixas débito, vista, 2–6x, 7–12x e Pix. | RN-08 e RN-09. Taxa de antecipação não é consumida nesta entrega. Coluna parcelada ausente não recebe taxa de outra faixa. |
| E2-03 | Aceitar data isolada, “até” e “a partir de”, com limites inclusivos e outro limite aberto. | RN-10 e formatos efetivamente presentes na planilha. Não escolher contrato por ordem de linha ou “mais recente”; lacunas/sobreposições/formatos novos geram pendência. |
| E2-04 | Explicitar observações conhecidas por CNPJ/texto, sem interpretação livre. | Bridge: notas apenas explicam a renegociação descrita nas vigências; Kiwi: EC confirmado em RN-03; Casa: RN-13/RN-14 esclarecem condição; Mundo Aberto: nota refere-se exclusivamente a remessa. Essas são interpretações técnicas documentadas, não novas aprovações de taxas. Texto novo volta a ser pendência. |
| E2-05 | Importar da aba antiga apenas identidade. | Atualização do usuário. Atlas: EC em RN-15; CNPJ/nome conferidos em ANTIGO 2025 - nao usar L8. Semelhança de nome ou taxas históricas não são usadas para contrato. |
| E2-06 | Aplicar taxa zero da Casa apenas no intervalo configurado e registrar regra no rastro. | RN-13/RN-14 e atualização do usuário sobre data da venda. A comissão zero confirmada não equivale a comissão desconhecida; não confundir com devolução de D-08. Exige contrato único vigente, sem ignorar novas observações. |
| E2-07 | Manter bloqueio comercial da Atlas até confirmação documentada. | RN-15/RN-16. Mesmo se surgir linha nova na planilha, retirar bloqueio exige registro de confirmação; D-07 continua pendente. Todos os eventos conhecidos da Atlas são encaminhados ao Comercial. |

Metadados de regra registram as fontes disponíveis. Onde os documentos só informam horário ou papel aprovador, a configuração declara que a data/pessoa não foi informada. Não foi fabricada uma aprovação financeira.

## Nova entrada durante a validação

A pasta local recebeu `06_orbe_ajustes_tardios_set2026.csv` durante a Entrega 2. O contrato atual exige uma única fonte Orbe: com duas candidatas o checkout fica bloqueado, sem fusão, seleção silenciosa ou deduplicação inventada. O processamento do arquivo adicional não foi incorporado nesta etapa. A evidência em `saida/entrega2/` usa cópias intactas das duas entradas originais; o manifesto na raiz de `saida/` registra a limitação da pasta completa. Os resultados isolados não cobrem ajustes tardios.

## Atualizações recebidas que não devem ser perdidas

- Bridge é divergência confirmada: contrato prevalece sobre aviso à Orbe. Mundo Aberto também é divergência; Casa é concessão da Tarvo.
- Estorno com taxa errada entra negativamente nas divergências; faixa vem da própria linha do estorno.
- Isenção da Casa depende da data da venda. Linhas da Casa em divergências são opcionais; não confundir com cobrança à Orbe.
- Spread negativo irregular não é ajuste reconhecido. A regra geral de exclusão não pode descartar `AJUSTE REF PC-…`.
- Provisões novas de folha e impostos são da contabilidade; futura classificação dos pagamentos bancários permanece no alvo.
- Não haverá pacote oficial de outubro. Usar amostras sintéticas para outros meses; a banca pode fornecer novas entradas.
- Pendência de acompanhamento não equivale a divergência financeira.
- IA futura poderá receber chave exclusiva da banca com limite de gasto, fornecida separadamente. O mínimo não precisa de chave.

Os arquivos locais de Context ainda contêm informações anteriores, incluindo o valor antigo da Casa e RF-12 com outra numeração. Esta atualização registra o relato do usuário sem sobrescrever esses materiais.
