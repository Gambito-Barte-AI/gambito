# Estado atual: nenhuma decisão financeira sem tratamento registrado

Todas as decisões estão respondidas pelo Financeiro ou registradas como decisão do time. As seções abaixo são o histórico, do mais recente para o mais antigo: onde um registro antigo diz "D-10 pendente", "decisões pendentes" ou "NAO_INFORMADO", vale este estado atual.

- **D-10:** respondida pelo Financeiro (11h33) e confirmada no retorno do checkpoint 2.
- **D-03:** o corte original foi decidido pelo time (Alice, 17h36). A ativação posterior de E3 foi aprovada pelo usuário e está em `[extras.alertas]` do `regras.toml`; gera apenas pendência revisável, sem alterar os números financeiros.
- **Datas de aprovação:** as 34 regras que estavam com `NAO_INFORMADO` receberam o horário da resposta do Slack que as sustenta (critério do Financeiro) ou da decisão do time. O manifesto não lista mais metadados incompletos.
- **O que segue aberto é operacional, não decisão:** contrato da Atlas (o Diego, do comercial, decide), pagador do Pix de R$ 7.350 (o Caio identifica), contestações com a Orbe e a Ponte e conferência do crédito da Ponte em 06/10. Cada um é uma pendência no `pendencias.csv`, com motivo, próximo passo e dono.
- **Premissas operacionais RN-65 confirmadas pelo usuário:** o layout não distingue relatório principal de ajuste. Estorno ou reversão com original do próprio mês ausente em todos os arquivos é tratado pela linha recebida: calcula-se a contribuição com os dados dessa linha e a taxa contratada da data original declarada, com pendência derivada para o Financeiro pedir e conferir a original à Orbe. O fechamento permanece provisório até a revisão. Estorno de mês anterior sem arquivo histórico segue a RN-13. Todos os arquivos presentes na pasta são considerados recebidos antes da aprovação do fechamento; ajuste novo após a aprovação pertence ao mês seguinte e deve ser apresentado na pasta/competência seguinte pelo operador. Não há nos arquivos registro de chegada ou da aprovação, logo o motor não consegue detectar uma colocação equivocada na pasta.

---

# Respostas do Financeiro e da organização (15h47 às 16h52) e D-10

Registro de 17/10/2026. As respostas abaixo foram dadas no canal a outros times, mas valem para todos. O Financeiro disse às 16h08 que não confere conta por conta: vale o critério registrado aqui. Conferido com uma execução do alvo sobre o pacote completo (7 arquivos): os seis resultados saem COMPLETO.

- **D-10 respondida.** A resposta das 11h33 (ajuste é linha nova, com Spread R$ negativo, que abate a nossa participação do mês na nota única, com rastro para a operação original e sem nota complementar) foi confirmada pela organização no retorno do checkpoint 2 (16h01). Critério: o Spread R$ do ajuste é spread; a participação é 50% dele, aplicada uma vez (no exemplo da PC-0926-0434, a nota cai R$ 117,87). Em setembro não há linha de ajuste. A D-10 saiu de `decisoes_pendentes` e foi para `decisoes_documentadas` no `regras.toml`.
- **Nota da Ponte (16h40).** Sai pela nossa regra, com spread negativo fora e operação repetida contada uma vez: **R$ 39.543,45**, e não o número líquido da Ponte. Se o crédito de 06/10 vier diferente, a diferença vira pendência do Financeiro, junto com a contestação. A Ponte não retém imposto; o ISS da nota vai no DAMSP do mês seguinte, fora deste fechamento.
- **Prazo de contestação.** Ainda está valendo, porque o fechamento é esta semana. As pendências de contestação (Orbe, Mundo Aberto, spreads negativos e duplicata) seguem abertas para o Financeiro.
- **Mundo Aberto (D-05).** O Financeiro disse que a diferença é de centavos e pediu para escolher e registrar. Mantemos **R$ 1.418,85**, pelo Spread %.
- **Estorno de venda com divergência.** As duas linhas ficam em `divergencias_taxa.csv`, com o estorno negativo; na cobrança da Orbe elas se anulam.
- **Orbe cobrou menos que o contrato.** É divergência, decidida caso a caso pelo Financeiro. Não aconteceu em setembro.
- **Fluente, Pix a 0,79%.** É condição negociada. Não gera divergência nem pendência.
- **Casa do Estudante.** Isenção de 01/09/2026 a 31/12/2026. Renovar em 2027 é decisão do comercial, ainda sem previsão. A devolução segue pelo que a Orbe tirou (RN-64, R$ 15.396,77).
- **Atlas.** Quem decide a taxa é o Diego, do comercial, sem previsão. Quando a taxa for confirmada, setembro é faturado junto com outubro, desde 10/09. Até lá, segue fora das comissões (D-07), com pendência.
- **CNPJ e razão social.** CNPJ tem sempre 14 dígitos; completar o zero à esquerda é correto. O tomador da nota usa o nome da planilha com o CNPJ; a razão social do contrato de adesão é conferida na emissão.
- **`ref_origem` do Aurora (organização, 16h52).** Linha física do arquivo como veio, contada a partir de 1, incluindo cabeçalho do banco e linha de colunas. Confirma a D-04: o primeiro lançamento é **L9**, o Pix sem pagador é a L50 e a transferência para o Meridiano é a L92.
- **Extratos e plano de contas.** Despesa do mês vai direto na despesa; recurso de lojista fica no passivo; aplicação não tem efeito no resultado. Critérios aplicados:
  - IOF das remessas é do cliente: o TED para a Ponte baixa inteiro `2.1.02.001`, sem despesa da Tarvo;
  - IOF de R$ 48,21 (MRD2026090586) é de operação de crédito do Meridiano: `4.3.01`;
  - juros da conta garantida vêm no extrato do mês seguinte: nada a lançar em setembro;
  - rendimento do CDB (R$ 3.912,66) é receita do mês: `3.2.01`; aplicação e resgate: `1.1.02.001`;
  - seguro (R$ 1.830,44) vai direto na despesa: `4.2.05`;
  - o único Pix enviado que não é repasse é o da contabilidade (R$ 6.800, L53): `4.2.06`; Pix para quem não é lojista vira pendência;
  - Pix de R$ 7.350 sem pagador (L50): `1.1.09.002` com pendência; quem vai atrás do pagador é o Caio, com o banco, até o fechamento de outubro;
  - devolução de R$ 12.400 da Mundo Aberto (L65): `2.1.01.001` (D-06; o Financeiro aceita as duas contas);
  - transferência de R$ 300 mil para o Meridiano (L92): `1.1.09.001`, em trânsito; se a entrada não aparecer em outubro, vira pendência da tesouraria;
  - Pix de R$ 18.240 da Ponte Aérea: `2.1.02.001`; a baixa sai quando a remessa liquidar, pelo relatório de outubro da Ponte;
  - folha de agosto baixada em setembro: a provisão foi feita pelo valor pago, então a baixa é pelo valor cheio do lançamento. A solução não gera a provisão do mês.
- **Colunas extras.** Podem ficar, desde que as colunas pedidas estejam presentes e com os nomes certos.

Revisão completa do canal às 17h30 (63 respostas do Financeiro e da organização, de 16/10 19h59 a 17/10 16h52). Além do que já estava registrado, entram estes critérios das respostas da tarde:

- **Isenção da Casa na antecipação (13h34).** Vale pela data da antecipação: é um serviço prestado no dia. Antecipação feita entre 01/09 e 31/12 é isenta, sem procurar as vendas de origem. O motor já usa a data do movimento da antecipação.
- **Ajuste tardio da Orbe depois da aprovação (13h34).** Se chegar antes da aprovação do fechamento, entra no mês do movimento (como o arquivo 06). Se chegar depois, entra no mês seguinte. A aprovação é do Financeiro e não é registrada nos arquivos; quem roda o fechamento escolhe a competência com `--competencia`.
- **Correção de linha com o mesmo `id_transacao` (13h34).** Nunca aconteceu; o critério é nosso. A linha idêntica em dois arquivos conta uma vez. Se os valores forem diferentes, não escolhemos nenhum: as linhas viram pendência para o Financeiro.
- **Ajuste órfão (14h10; premissa operacional posterior do usuário).** A ausência de original do próprio mês é avaliada por linha, em qualquer CSV da Orbe. A contribuição entra a partir dos dados do evento e do contrato vigente na data original declarada, com pendência e fechamento provisório para o Financeiro solicitar a original. Em setembro não há esse caso.
- **Bandeira no estorno (14h08).** A bandeira não muda a taxa. Estorno com bandeira diferente da venda segue vinculado pela referência, sem contestação e sem pendência (7 casos no arquivo 06).
- **Alerta de antecipação (D-03).** O Financeiro disse que o alerta é para ele e para o comercial, que não muda nenhum número e que o critério é nosso (11h37, 11h49, 12h50). Decisão do time (Alice, 17h36): o alerta não entra nesta entrega. Critério para quando entrar: só lojista com contrato bloqueado (hoje a Atlas), sem corte em reais, pico pelo maior saldo ao fim de cada dia (antecipações menos reversões vinculadas) e uma pendência por lojista para Financeiro e Comercial. Referência de setembro: Atlas, R$ 183.581,24 em 24/09.

---

# A7 — aceite integrado e reprodução final

A7 autorizada pelo usuário e validada tecnicamente em 17/10/2026 no ambiente Windows/Python 3.12.10. Preservados mínimo, A1–A6, RN-64 corrigida e D-10 pendente. Extras não iniciados. Evidências finais em `docs/ACEITE_A7.md` e `saida/alvo-a7-final/`; registros anteriores permanecem históricos.

- **Aceite técnico:** seis arquivos, origens/cobertura, valores e rastro, determinismo, perda/layout inválido das fontes, publicação parcial sem saída antiga reaparecer e outro mês sintético foram conferidos. Nenhuma regra financeira alterada. Aprovação técnica não ratifica D-10 nem libera pagamento, lançamento externo ou nota fiscal.
- **Reprodução:** cópia limpa e ambiente virtual novo, sem Context, ambiente anterior ou dados/resultados embutidos. Instalação usa índice de pacotes; execução não usa API/rede. macOS/Linux não executados: não declarar certificação dessas plataformas. Em ambiente restrito, TEMP/TMP graváveis no workspace foram necessários para inicializar pip.
- **Publicação Windows:** WinError 5 voltou a ocorrer em substituição de arquivo durante os testes. Acrescentadas até quatro tentativas somente para PermissionError Windows 5/32/33, com espera total máxima de 350 ms. Causa externa do bloqueio não determinada; falha persistente continua explícita e não libera o manifesto final. Casos transitório/persistente testados; demais erros não são repetidos.
- **Auditoria integrada:** produtor validado por resultado, IDs únicos entre arquivos, domínios, precisão, datas e reconciliação global complementam as auditorias por origem. Resultados conhecidos servem apenas à regressão; o cenário sintético usa outros CNPJs, valores, nomes e competência 2032-10.
- **Pendências preservadas:** D-10 continua aguardando confirmação financeira; Atlas aguarda contrato e não tem comissão estimada; datas sem evidência continuam NAO_INFORMADO. O aceite não elimina as pendências operacionais/financeiras dos relatórios.

---

# A6 — Meridiano

A6 autorizada e implementada em 17/10/2026, preservando mínimo, A1–A5 e RN-64 corrigida. A7 não iniciada. Evidências em `docs/ACEITE_A6.md` e `saida/alvo-a6/`; registros anteriores permanecem históricos.

- **RN-46/RN-49/RN-51/RN-55:** fundos de lojistas, inclusive adiantamento de remessa, são passivo; liquidação à Ponte baixa os recursos a liquidar. Ponte Aérea é lojista, sem confundir com Ponte Câmbio. Comissão recebida baixa o recebível; não gera outra receita. Mapeamentos técnicos sob o critério de contrapartida, sem aprovação individual fictícia, ficam no TOML com proveniência.
- **Aplicações:** principal de aplicação/resgate usa a conta da aplicação; somente rendimento explicitamente descrito vai a receita financeira. Não inferir rendimento pela diferença entre movimentos nem executar conciliação entre bancos.
- **RN-57 / integridade:** preservar FITID e dia local do DTPOSTED; linhas físicas só complementam o diagnóstico. OFX SGML cp1252/UTF-8 declarado, sem reparo de mojibake por suposição. Campos-folha podem ter fechamento opcional; agregados precisam estar completos. Estrutura truncada, múltiplas contas/arquivos, status de erro ou moeda incompatível bloqueiam o banco.
- **FITID repetido:** política técnica conservadora, sem regra financeira de escolha/deduplicação bancária aprovada: todas as ocorrências ficam pendentes, mesmo se iguais. Não escolher por ordem ou ocultar conflito pelo recorte de competência. FITID ausente não é inventado; linha física aparece somente na pendência diagnóstica. Valores conhecidos são preservados, desconhecidos ficam vazios.
- **Isolamento:** os bancos compartilham o plano e a lógica de classificação, mas não dependem um do outro, do checkout ou da Ponte. Regras/valor/rastro inválidos de um banco não bloqueiam o outro. Não houve alteração das fórmulas ou registros de A1–A5.
- **Limite da autorização:** status computacional COMPLETO pode ocorrer no pacote fornecido, sem significar aceite integrado de A7. A7 continua pendente de aprovação; extras não iniciados. D-10 continua pendente de confirmação financeira; contrato da Atlas e datas não comprovadas continuam explícitos. Nenhuma integração, instalação ou commit.

---

# A5 — plano de contas e Aurora

A5 autorizada e implementada em 17/10/2026, preservando mínimo, A1–A4 e RN-64 corrigida. A6 não iniciada. Evidências em `docs/ACEITE_A5.md` e `saida/alvo-a5/`; os registros anteriores permanecem históricos.

- **RN-46 a RN-51:** plano original lido sem correções manuais. Contrapartida deve existir, ser ANALITICA e aceitar lançamento. Baixas de folha/impostos usam passivos, sem gerar provisões do mês. Mapeamentos conta/histórico são interpretações técnicas sob o critério documentado do Financeiro, não aprovações individuais inventadas; fonte/papel/data no TOML.
- **Classificação conservadora:** uma única regra compatível com histórico normalizado e sinal. Aliases confirmados de repasses ficam na configuração; destinatário novo exige revisão. Não há casamento por semelhança de nome nem dependência do cadastro/contrato de checkout. Crédito sem identificação não é receita. Devolução da RN-53 fica em 2.1.01.001 conforme D-06; padrão limitado à contraparte confirmada, sem estender a qualquer retorno de Pix. Transferência própria exige o destino configurado; não confirma sua chegada no outro banco.
- **RN-52/RN-53/RN-58:** classificação conhecida pode ter pendência adicional de revisão, sem contar o movimento duas vezes na cobertura. Natureza MOVIMENTO_BANCARIO distingue valores do extrato de comissões, devolução da Casa e contestações.
- **RN-56/RN-57/D-04:** Orbe somente classificada em recebíveis, sem conciliação parcela a parcela. Saldo negativo não gera receita/despesa ou pendência artificial. Saldo anterior/final e rodapé conhecidos são explicitados no inventário; não são movimentos. Referência é a linha física inicial, inclusive em CSV com registro multilinha; L9 pertence ao exemplo, não é constante.
- **Dados inválidos:** linhas posteriores ao cabeçalho sem formato reconhecido permanecem pendentes. Data/valor inválido não é estimado, preenchido por zero nem descartado silenciosamente. Conta ausente/proibida ou linha inválida torna Aurora provisório; histórico sem regra e ambiguidades viram pendência de negócio, sem impor provisório por si só (D-13).
- **Competência e isolamento:** banco deriva seu próprio mês; vários meses exigem --competencia. Datas inválidas permanecem para revisão no recorte. Falha de plano/Aurora ou de configuração de classificação não bloqueia A1–A4; falta de Orbe/Ponte/taxas não impede Aurora. Auditor relê fontes; publicação reconfere contexto e não repara adulteração silenciosamente.
- **Pendências existentes:** D-10 continua aguardando confirmação financeira, Atlas aguarda contrato e RN-64 não foi alterada. Datas não comprovadas continuam NAO_INFORMADO. Nenhuma integração externa, nova dependência ou commit. Meridiano e extras permanecem futuros.

---

# A4 — notas a emitir

A4 autorizada pelo usuário e implementada em 17/10/2026, preservando o mínimo, A1–A3 e a RN-64 corrigida. A5 e etapas seguintes não iniciadas. Evidências em `docs/ACEITE_A4.md` e `saida/alvo-a4/`; os registros anteriores permanecem históricos.

- **RN-42 a RN-45:** propostas derivadas exclusivamente das comissões validadas, com valores já arredondados. Checkout por CNPJ/competência; remessa em uma única proposta por competência à Ponte configurada, incluindo contribuições negativas regulares de ajuste na soma. Sem notas por lojista da remessa nem nota complementar.
- **RN-43:** saldo zero/negativo não gera nota; gera pendência financeira com valor assinado e origens completas. Não existe transporte automático, compensação entre competências ou recuperação de comissões de meses anteriores. Estabelecimento sem comissão calculável, como Atlas sem contrato, não recebe proposta estimada nem pendência fictícia de saldo zero.
- **D-10:** permanece pendente de confirmação financeira. A4 utiliza a contribuição já calculada por A3, sem reaplicar o percentual. Ajuste aparece no rastro, na pendência existente e na discriminação/motivos da proposta; proposta não representa liberação fiscal/financeira.
- **Isolamento:** NOTAS_CHECKOUT depende de CHECKOUT validado + regras; NOTAS_REMESSA depende de REMESSAS validado + regras. Falha de divergência/devolução não bloqueia proposta de comissão válida. Comissão provisória gera proposta provisória do subconjunto conhecido, com status no manifesto; dados desconhecidos não viram zero. Configuração de notas ausente/inválida bloqueia somente a parte correspondente.
- **Contratos internos:** competência e CNPJ vêm do ID estável da comissão, confrontado com sua linha de negócio/identidade; não vêm da data da venda original. Cobertura de notas conta saldos de origem; o rastro replica todas as contribuições, preservando sinais, valores, regras e vínculos, com ID/natureza próprios.
- **RN-61:** descrições de serviço, tomador da remessa e fonte/aprovação ficam em `regras.toml` e no manifesto versão 6. Papéis documentados não são apresentados como nomes pessoais de aprovadores. Não houve alteração de regra financeira, nova dependência, integração fiscal ou commit.

---

# A3 — Ponte de ponta a ponta

A3 autorizada e implementada, preservando mínimo, A1 e RN-64 corrigida. A4/notas e etapas seguintes não iniciadas. Evidência atual: `docs/ACEITE_A3.md`, `saida/alvo-a3/` e `.tmp/aceite-a3/`. Os registros abaixo passam a ser históricos das entregas anteriores.

- **D-10 permanece pendente:** contribuição do ajuste = participação configurada × Spread R$ negativo, aplicada uma vez, conforme decisão existente do time. Não equivale à confirmação do Financeiro. Pendência individual por ajuste, referência original e motivo explícito; nota não é gerada.
- **Competência do ajuste (RN-37):** mês declarado no novo relatório; se não declarado, parâmetro explícito --competencia. Sem ambos, considera-se a contratação da nova linha como indicação do mês de chegada. Não inferir o mês a partir do Nº Operação original nem da liquidação; confirmar o período se esses dados não representarem o novo mês. Relações incompatíveis ou autorreferentes ficam pendentes.
- **Duplicatas:** observação reprocessada não muda o valor; escolher a ocorrência canônica pela ordenação arquivo/linha só quando os campos financeiros e a aprovação forem compatíveis. Conflitos e ocorrência ilegível do mesmo número deixam todas pendentes, sem escolha financeira silenciosa.
- **Contratos de remessa:** leitura própria da aba vigente; blank/padrão usa RN-32 só para cadastro existente. CNPJ inexistente não recebe spread presumido, mas conserva participação pelo realizado (RN-40). Sem planilha disponível, não declarar todos os lojistas como cadastro inexistente. Vigência da Mundo Aberto só desde julho, conforme RN-28/observação; antes disso exige aprovação contratual.
- **D-11:** valor principal e rastro = realizado − contratado × PTAX × ME; realizado e solicitado em extras distintos, com sinal original. Sem contrato/PTAX/ME, pedido vazio e provisório; o valor reportado conhecido continua explícito. Não usar o Spread % para reconstruir o Spread R$ negativo.
- **Isolamento:** ausência/falha da Ponte não muda o checkout; ausência de Orbe ou planilha não impede participação pelo realizado. REMESSAS e DIVERGENCIAS_REMESSA têm rastro/validação separados. Fontes/dados contratuais faltantes bloqueiam/provisorizam a comparação pertinente.
- **Acompanhamento (RN-39):** valor é participação calculada a conferir com o TED efetivo, sem previsão de recebimento/desconto. Pendência de negócio não gera alarme nem força situação provisória por si só.
- **Metadados:** datas do time ausentes continuam NAO_INFORMADO; fontes e papéis registrados, sem inventar ratificação financeira. Sem novas dependências, serviços externos ou commits.

---

# A2 — divergências de checkout e devolução da Casa

A2 autorizada e implementada; A3 e etapas seguintes não iniciadas. Mantidos o mínimo, o isolamento de A1 e os seis layouts oficiais. Evidência atual: `docs/ACEITE_A2.md` e `saida/alvo-a2-rn64/`.

- **RN-64, esclarecimento atual do usuário em 17/10/2026:** estornos elegíveis de vendas isentas abatem a devolução; a origem e a vigência da venda determinam a elegibilidade. Confirmado nos dados: 117 vendas/antecipações, R$ 15.405,85, menos TX88446763, −R$ 9,08, vinculado à venda isenta TX88441917 = R$ 15.396,77 líquidos em 118 linhas. TX88445133, da venda de agosto, fica fora da devolução e preservado na comissão pela taxa original. A interpretação anterior de exclusão de todos os estornos foi incorreta e está substituída por este esclarecimento; não foi uma nova mensagem do Financeiro no Slack. Referência, tipo, EC, data e limites de estorno continuam validados pelo checkout antes da devolução; dado insuficiente vira pendência, sem abate estimado.
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
- **RN-13 e RN-65 (atualização posterior):** estorno de mês anterior sem relatório histórico usa referência/data declaradas. Estorno ou reversão com original do próprio mês ausente entra pelo próprio evento, com pendência derivada e resultado provisório. Referência conflitante ou dados insuficientes seguem sem cálculo. O tratamento antigo descrito nas seções históricas abaixo foi substituído pela premissa operacional registrada no início deste arquivo.
- **D-12/D-13:** bloqueio gera cabeçalhos e total indisponível. Pendência de negócio não torna o resultado provisório; pendência de dados ou aviso de fonte rejeitada torna. Fonte rejeitada tem hash/motivo e não entra na cobertura de linhas lidas com sucesso.
- **D-14:** `--competencia AAAA-MM` quando necessário; contabilizar separadamente eventos de outros meses. Reversão com original fora do recorte continua pendente, sem reconstrução histórica.
- **D-02 e D-04:** tolerância de 0,01 p.p. e Aurora iniciando em L9 físico pertencem aos módulos futuros. Nenhum cálculo de spread ou leitura bancária antecipado.

Os registros seguintes descrevem o histórico das Entregas 1–4; menções a D-07/D-08 abertas e ao bloqueio por dois arquivos foram superadas por esta atualização. Evidência vigente: `docs/ACEITE_MINIMO.md`, `saida/aceite-multiorbe/`.

---

# Hipóteses, limites e decisões da entrega 1 (registro histórico)

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
