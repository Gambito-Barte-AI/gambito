# A2 — divergências de checkout e devolução da Casa

A2 autorizada e implementada; A3 e etapas seguintes não iniciadas. Mantidos o mínimo, o isolamento de A1 e os seis layouts oficiais. Evidência atual: `docs/ACEITE_A2.md` e `saida/alvo-a2/`.

- **RN-64, recorte confirmado pelo usuário em 17/10/2026 nesta conversa:** somente VENDA e ANTECIPACAO elegíveis, sem nenhum ESTORNO. Referência recalculada: 117 linhas / R$ 15.405,85. O valor anterior de R$ 15.396,77 incluía TX88446763 (−R$ 9,08); não é mais a referência vigente. O estorno de agosto continua fora da devolução e preservado na comissão. A fonte da decisão de recorte é o usuário, não uma aprovação financeira inventada no Slack.
- **RN-20 a RN-27:** divergência por taxa aplicada versus contratada, HALF_UP por linha, sinais de estornos preservados. Mesma taxa com truncamento do valor cobrado não gera divergência. Sem tolerância de spread no checkout: D-02 é de remessa, futura.
- **Casa / D-09:** só pendência de devolução e detalhe no rastro; nenhuma cobrança contratual à Orbe. Pagamento e contestação dependem de revisão humana; não são executados.
- **Atlas:** continua fora das comissões e divergências por ausência de contrato confirmado, com as 57 pendências de negócio no exemplo. D-07 resolvida; D-13 preservada.
- **D-10:** confirmação financeira da natureza do ajuste Ponte continua pendente. Não foi implementada remessa. Datas de aprovação ausentes continuam NAO_INFORMADO.
- Campos de taxa aplicada/cobrança inválidos tornam provisória apenas a análise que depende deles; não descartam automaticamente o evento contratual do mínimo. IDs das saídas derivadas são distintos das comissões e da cobertura física.

Os registros abaixo são históricos e descrevem o escopo vigente em cada entrega anterior; seus números e afirmações de não implementação não substituem esta revisão.

---

# A1 — isolamento aprovado de resultados e dependências

Apenas A1 foi autorizada nesta sessão. Mantidos os valores, os seis CSVs do mínimo e todas as decisões financeiras; A2 e os leitores/cálculos futuros não foram implementados.

- ResultadoParte separa payload, rastro, cobertura, fontes, resultados requeridos, situação e motivos. CHECKOUT e PENDENCIAS_CHECKOUT são adaptados a partir do contrato existente; cada um é revalidado antes da publicação.
- O padrão --escopo checkout exige o mínimo (comissões e pendências existentes). --escopo alvo exige todas as partes declaradas, sem ativar etapas não implementadas. O agregado é completo somente se todas forem completas; provisório se houver parte disponível e alguma incompleta; bloqueado se nenhuma estiver disponível. Códigos 0/2/1 seguem o escopo escolhido. O case normal continua retornando 0 no padrão.
- Manifesto versão 3 preserva os campos legados de checkout. situacao_comando, fechamento, partes e resultados explicam o escopo e a composição dos arquivos. Em falha isolada, o código pode ser 2 mesmo com checkout bloqueado, se pendências independentes forem válidas; o total do checkout fica null.
- Fontes futuras não lidas têm estado NAO_AVALIADA, não DISPONIVEL nem AUSENTE por suposição. As etapas correspondentes ficam bloqueadas como não implementadas. A1 não faz detecção ou parsing financeiro da Ponte/bancos.
- Falha de rastro, esquema ou cobertura bloqueia a parte afetada e seus dependentes. Conflito de id_saida bloqueia os produtores envolvidos. Arquivos compostos recebem apenas linhas de partes validadas; registros monetários bloqueados não viram zero. Falha de escrita mantém o marcador global de publicação bloqueado.
- Testes de bancos/remessa usam saídas normalizadas sintéticas para exercitar dependências, sem leitores ou regras desses produtos. Não constituem aceite financeiro do alvo.
- Contrato da Atlas, pergunta financeira de D-10 e datas de aprovação ausentes continuam explícitos, sem novas aprovações ou valores inferidos. Interpretação histórica RN-13/RN-65 preservada.

Evidência vigente de A1: docs/ACEITE_A1.md e saida/alvo-a1/. Os registros abaixo permanecem como histórico das entregas anteriores.

---

# Revisão final do mínimo antes do alvo

A solicitação atual autorizou a exportação das pendências existentes, embora RF-11 esteja originalmente classificado no alvo. Não foram implementados novos cálculos do alvo. Os seis CSVs oficiais passam a ser publicados; divergências, notas e classificação ainda têm apenas cabeçalhos e status BLOQUEADO com motivo no manifesto.

`pendencias.csv` e o rastro monetário das pendências atendem D-07/RN-58: as 57 origens da Atlas preservam o cobrado pela Orbe, separado da comissão. Em outros casos, bruto conhecido é identificado explicitamente como BRUTO_REFERENCIA. Valor desconhecido fica vazio/NAO_INFORMADO, não zero, e não gera rastro monetário; pendências/rastro ficam provisórios quando isso ocorrer. Não é autorização para cobrança ou faturamento.

O status principal continua sendo do checkout; o manifesto versão 2 explicita esse escopo e apresenta o status de cada CSV. A configuração do usuário, os relatórios e os registros anteriores foram preservados. D-07 e RN-64 já são decisões documentadas; não existem mais avisos de decisão financeira pendente para D-07/D-08 na execução normal. A referência docs/documentação-geral.md existe e está versionada nesta branch.

A proposta de alvo está em docs/EVOLUCAO_ALVO.md, exclusivamente como planejamento. Evidência desta revisão: saida/revisao-pre-alvo/ e docs/ACEITE_MINIMO.md. Os registros abaixo refletem entregas anteriores quando divergirem desta revisão.

---

# Atualização P0/P1 — fonte atual e tratamentos aprovados

A referência atual é `docs/documentação-geral.md` da develop, que prevalece sobre a numeração e o estado histórico abaixo. Arquitetura monolítica modular e escopo checkout mínimo preservados.

- **D-07 documentada:** Atlas fora das comissões, sem faturamento estimado; identidade e `valor_taxa` da Orbe preservados por linha no manifesto. O contrato segue pendente para o Comercial. As 57 origens ficam nas pendências, sem inserir comissão fictícia no rastro de valores calculados.
- **RN-64 (antiga D-08) confirmada:** Casa usa cobrança efetiva nas linhas elegíveis para a devolução. Referência R$ 15.396,77. Devolução não implementada no mínimo; a comissão segue a isenção e a vigência original.
- **D-10 pendente de confirmação financeira:** decisão do time de aplicar 50% do Spread R$ negativo registrada; é preciso confirmar se a linha já representa a participação. Nenhuma remessa implementada.
- **RN-61:** aprovador, data e natureza separados nas regras. Datas não presentes no registro técnico/time ficam `NAO_INFORMADO` e aparecem no manifesto; completar quando houver evidência. Isso não representa aprovação financeira.
- **RN-65/RF-22:** reunir CSVs por cabeçalho. Repetição idêntica entre arquivos conta uma vez; conteúdo conflitante fica integralmente pendente. Origem canônica dos idênticos escolhida pela ordem de nomes, sem dependência de nome específico. Duplicata dentro do mesmo arquivo continua invalidando essa fonte por ambiguidade de origem.
- **RN-13 versus referência ausente em RN-65:** preservado o caso confirmado de estorno de mês anterior sem relatório histórico, usando referência/data declaradas; referência do próprio mês ausente, reversão sem original e referência conflitante viram pendências. Não exigir agosto evita rejeitar o exemplo explicitamente aprovado. Validar com o time se RN-65 pretendia revogar esse caso histórico; nenhuma taxa é estimada.
- **D-12/D-13:** bloqueio gera cabeçalhos e total indisponível. Pendência de negócio não torna o resultado provisório; pendência de dados ou aviso de fonte rejeitada torna. Fonte rejeitada tem hash/motivo e não entra na cobertura de linhas lidas com sucesso.
- **D-14:** `--competencia AAAA-MM` quando necessário; contabilizar separadamente eventos de outros meses. Reversão com original fora do recorte continua pendente, sem reconstrução histórica.
- **D-02 e D-04:** tolerância de 0,01 p.p. e Aurora iniciando em L9 físico pertencem aos módulos futuros. Nenhum cálculo de spread ou leitura bancária antecipado.

Os registros seguintes descrevem o histórico das Entregas 1–4; menções a D-07/D-08 abertas e ao bloqueio por dois arquivos foram superadas por esta atualização. Evidência vigente: `docs/ACEITE_MINIMO.md`, `saida/aceite-multiorbe/`.

---

# Hipóteses, limites e decisões pendentes

## Escopo autorizado

Arquitetura consolidada e Entregas 1 a 4 autorizadas pelo usuário nesta conversa em 17/10/2026. Escopo atual: checkout com vendas, estornos, antecipações e reversões, mantendo identidade, faixas, vigências e rastro; aceite e reprodução do mínimo. Não implementar alvo. O `AGENTS.md` do usuário foi relido e preservado.

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
| D-08 | Ratificar devolução da Casa pelo cobrado e recorte elegível? | Usuário relatou fala de Helena: “o que foi cobrado eu devolvo”; referência corrigida para R$ 15.396,77. Concessão paga pela Tarvo, fora da cobrança à Orbe. | A isenção confirmada é aplicada independentemente de D-08. Estorno anterior à isenção agora usa a taxa anterior, sem apagar saldo negativo. Não calcular devolução nem usar valor_taxa como comissão. |
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

## Decisões técnicas e limites da Entrega 3

| ID | Decisão ou tratamento conservador | Fonte e limite |
| --- | --- | --- |
| E3-01 | Estorno na competência do movimento, com faixa da própria linha e taxa/isenção pela data original. | RN-07/RN-11/RN-14 e atualização do usuário sobre faixa. Não reabre o mês da venda. Referência e data original ausentes/inconsistentes ficam pendentes. |
| E3-02 | Venda de mês anterior pode estar ausente do arquivo corrente. | O data pack contém nove estornos sem venda local, com referências/datas originais. Selecionar contrato comprovável pela data declarada não inventa o valor de uma venda histórica. O rastro identifica essa referência, mas não inventa arquivo de origem ausente. |
| E3-03 | Venda do próprio mês referenciada mas ausente, tipo/EC/data incompatíveis ou estornos acumulados acima do bruto conhecido exigem revisão. | Tratamento técnico conservador de inconsistências, não nova regra de aprovação financeira. Não escolher qual estorno manter ou inferir dados faltantes. Estornos parciais coerentes usam o bruto da própria linha; relações históricas sem arquivo não permitem conferir limite acumulado. |
| E3-04 | Antecipação usa taxa da coluna específica e data do próprio evento. | RN-08/RN-12 e formato do relatório: antecipações não indicam venda individual/data original. Não há constante de 2,10% nem inferência de uma data de venda; referência temporal diferente vira pendência. |
| E3-05 | Reversão é o negativo exato da contribuição da antecipação referenciada. | RN-12. Confere original disponível/calculável, tipo, EC, data e bruto integral oposto; preserva taxa, regra, contrato e base temporal originais. A ordem física do arquivo não interfere. |
| E3-06 | Reversão parcial, múltiplas reversões do mesmo original ou original ausente ficam pendentes. | Esses cenários não têm tratamento confirmado nos documentos. Não ratear a comissão, reconstruir por taxa atual ou escolher a primeira reversão. Confirmar com o financeiro antes de ampliar. |
| E3-07 | Contribuição da reversão tem origem na linha nova e vínculo ao original como metadado. | Preserva a soma do rastro sem duplicar valores. O validador também exige anulação exclusiva do original. Comissão negativa/zero não gera nota ou transporte de saldo nesta entrega. |

Os tratamentos conservadores não ratificam D-07, D-08 ou D-10. Não há emissão de nota, relatório de divergência, devolução, recuperação da Atlas ou processamento automático dos ajustes tardios.

## Aceite técnico da Entrega 4

Reprodução feita em cópia limpa dos arquivos atuais do workspace, com venv novo, instalação pelo README e sem Context/PYTHONPATH/chaves. Passaram 81 testes e duas execuções produziram CSVs/manifesto idênticos em bytes. Um verificador independente conferiu a cobertura por referência, hashes, datas e soma do rastro.

O aceite se limita às duas entradas originais: 1.886 eventos calculados e 57 pendentes da Atlas, totalizando 1.943 destinos únicos. Os resultados são provisórios, sem ratificar D-07, D-08 ou D-10. A pasta completa com dois CSVs Orbe permanece bloqueada; isso não é aceite dos ajustes tardios. Ambiente efetivamente executado, limites e evidências estão em `docs/ACEITE_MINIMO.md` e `saida/entrega4/aceite.json`.

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
