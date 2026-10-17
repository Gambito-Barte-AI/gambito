# E0 — contratos e divisão do desenvolvimento extra

**Atualização aprovada após E0 (E3, 17/10/2026):** pico é o maior saldo ao fim de cada dia, sem limiar, somente contratos explicitamente bloqueados. "Sem histórico" não é inferido. Reversão sem original disponível no período é listada sem abater; exposição anterior é desconhecida. Uma pendência ALERTA_ANTECIPACAO por CNPJ e seu rastro são publicados no escopo alvo quando `[extras.alertas].habilitado=true`. Essa aprovação substitui, para E3, a previsão de artefato JSON separado/ativação por `--extras`; E1/E2 continuam em módulos e E4 não foi iniciada. Critérios e aceite em [E3](EXTRA_CONTINUIDADE_ALERTAS.md#e3--alertas-de-antecipação). D-10 foi confirmada pelo Financeiro às 11:33, conforme retorno do checkpoint 2: participação de 50% aplicada uma vez. Os trechos históricos de E0 abaixo não reabrem essas decisões.

## Estado e base comum

E0 autorizada pelo usuário: **definição documental dos contratos e da propriedade dos arquivos**. Não implementa E1–E5, opções de CLI, novos modelos ou artefatos. Os caminhos, funções e formatos futuros descritos abaixo são decisões internas de integração, não novos contratos oficiais do parceiro.

Base alvo: **82c087cfd3b8315b2178f6a0ab02b8dffd57cef3**, branch observada `feat/core-engine`, árvore limpa antes de E0. Essa base contém mínimo/A1–A7 e o pacote final em `saida/`. Referências: [documentação oficial](documentação-geral.md), RF-17 a RF-20, RN-18/RN-63/D-03; [formato oficial](FORMATO_SAIDA.md); [aceite A7](ACEITE_A7.md).

Após revisão e autorização para commit, E0 deve ser registrada uma única vez sobre essa base. **As duas branches deverão partir do mesmo commit que incluir E0**, cujo SHA ainda não existe. Não iniciar em HEADs diferentes nem depender de arquivos locais ignorados. Cada computador instala seu ambiente pelo README e recebe cópias íntegras das entradas, verificadas por hash.

| Branch proposta | Responsabilidade | Entregas futuras |
| --- | --- | --- |
| `codex/extra-continuidade-alertas` (frente 1) | Continuidade, alertas e integração central | E2, E3 e ligação/aceite integrado E5 |
| `codex/extra-assistencia-contestacoes` (frente 2) | Contestações determinísticas e assistência opcional | E1 e E4 |

Nenhuma branch foi criada por E0. O histórico integral de IA permanece adiado pelo usuário; não criar novos resumos substitutos nesta etapa.

## Invariantes compartilhados

- Manter Python, Decimal, processamento local e a arquitetura modular existente; sem banco, servidor, framework ou mecanismo de plugins.
- Não alterar as fórmulas aprovadas, RN-64, D-07 ou o tratamento atual de D-10. Preservar identidade, competência, natureza dos valores e referências desde a origem.
- Sem ativação explícita dos extras, os seis CSVs do mínimo/alvo devem manter os mesmos bytes da base. Nenhum extra altera silenciosamente a conclusão do alvo ou o código de retorno do comando existente.
- Sugestões, alertas e textos não aprovam lançamentos, contratos, notas ou pagamentos. IA não calcula totais e não escolhe identidades por semelhança.
- Todas as entradas e resultados recebidos por funções de extra são somente leitura. Retornar dados próprios, sem modificar `Resultado`, `ResultadoParte`, eventos, contextos bancários, arquivos originais ou configurações recebidas.
- Usar funções concretas e dicionários/listas com os campos abaixo; E0 não exige criar classes, interfaces abstratas ou arquivos de contratos em Python.
- Erros de um recurso extra ficam no seu diagnóstico. Não impedir a publicação de um alvo válido por indisponibilidade de API ou erro ao produzir um rascunho.

## Interfaces de integração — versão 1

### Dados de entrada

A frente 1 monta as projeções somente após a validação das partes do alvo. A frente 2 não importa a CLI, não chama novamente o fechamento e não relê fontes financeiras para recalcular resultados.

| Entrada | Campos e garantias |
| --- | --- |
| `visao` | `versao=1`, `competencia` (AAAA-MM ou null), `fontes` (identificadores/hashes), `partes` (situação, validado, motivos), `relatorios` (nome oficial → lista de linhas publicáveis dos seis CSVs). Preservar IDs e colunas existentes; incluir somente linhas de produtores validados. Estados de partes bloqueadas continuam visíveis, mesmo sem linhas. Não confundir `Resultado.pendencias`, que é de checkout, com todas as pendências do alvo. |
| `candidatos` | Lista de pendências bancárias `CLASSIFICACAO_NAO_RESOLVIDA` cujo motivo seja ausência de regra, sem erro de leitura e sem ambiguidade entre regras. Cada item: `id_pendencia`, `banco`, `origem` (`arquivo`, `ref`, `linha`), `data`, `descricao`, `valor`. Derivada das pendências e dos contextos bancários já normalizados. |
| `contas_permitidas` | Mapa `codigo` → `descricao`, `origem`, `tipo`, `aceita_lancamento`, limitado às contas analíticas permitidas do plano validado. IA recebe apenas os dados mínimos necessários; não recebe documentos completos, configurações com segredos ou o pack inteiro. |
| `config` | Somente a seção do recurso; parâmetros com fonte/proveniência. Segredos são obtidos por variável de ambiente pelo adaptador, nunca colocados nessa seção, nos logs ou nos artefatos. Ausência de parâmetro indispensável diagnostica o extra, sem inventar regra. |

Dinheiro e percentuais em memória usam Decimal; datas usam os tipos já existentes. Na projeção serializável, dinheiro vira string decimal com duas casas, datas AAAA-MM-DD, valores desconhecidos null e CNPJ string de 14 dígitos. Percentuais preservam a precisão e a unidade declarada, sem float. Ordenação determinística por banco/origem/ID; ordenação cronológica quando necessária ao cálculo do pico, com critério de desempate explícito.

### Funções futuras e retornos

As assinaturas abaixo são contratos documentais; não existem nesta etapa:

| Função | Dono | Retorno |
| --- | --- | --- |
| `contestacoes.construir_contestacoes(visao, config)` | Frente 2 | Pacote `contestacoes` com registros/textos por contraparte |
| `assistencia.sugerir_classificacoes(candidatos, contas_permitidas, config, consultar=None)` | Frente 2 | Pacote `assistencia`; `consultar` é função injetável para testes, sem framework |
| `continuidade.exportar_pendencias(resultado, config)` | Frente 1 | Pacote `continuidade`, usando eventos normalizados e fontes, não apenas o CSV resumido |
| `continuidade.ler_pendencias(documento)` | Frente 1 | Pacote de continuidade validado; não calcula nem altera a competência corrente |
| `alertas.analisar_antecipacoes(eventos, elegibilidade, config)` | Frente 1 | Pacote `alertas`; elegibilidade exige evidência de contrato/histórico, não ausência presumida |

Todos os pacotes têm `versao=1`, `recurso`, `situacao`, `motivos` (lista) e `registros` (lista). Domínio exclusivo dos extras: `COMPLETO`, `PARCIAL`, `BLOQUEADO`, `DESATIVADO`. COMPLETO significa processamento técnico concluído, não aprovação humana. Lista vazia com COMPLETO é válida quando não há casos; não gerar alarme fictício. Resultado financeiro global e código de retorno do alvo continuam separados.

Cada registro tem `id` estável, `origens` (lista de arquivo/ref/linha e hash da fonte quando disponível) e os campos específicos da seção seguinte. IDs não podem depender da ordem de execução, horário atual, computador ou nome Atlas. Usar identidade do recurso e da operação/pendência, preservando colisões/conflitos como diagnóstico, sem escolha financeira arbitrária. Versão desconhecida ou campo obrigatório inválido é rejeitado explicitamente.

### Conteúdo específico

**E1 / RF-18 — contestação.** Registro: `contraparte` (ORBE/PONTE), `ids_pendencias`, `ids_divergencias`, `texto`. Referências ao rastro existente devem permitir localizar todas as operações citadas. Criar no máximo um rascunho por contraparte/competência; sem casos, nenhum texto. Copiar valores validados, distinguindo realizado, diferença contratual e solicitado. Totais podem agregar grupos distintos da mesma natureza, com Decimal e reconciliação; não somar pendências agregadas e suas divergências novamente. Casa, acompanhamento, ajustes D-10 e cadastro não entram como cobrança contratual indevida. Parte bloqueada não gera contestação definitiva; sinalizar a limitação no pacote/texto quando houver um subconjunto válido. Sem IA e sem envio externo.

**E2 / RF-19 — continuidade.** Registro: `id_pendencia`, `cnpj` (ou null se desconhecido), `competencia_origem`, `evento` com todos os campos de Evento, `origens`, `motivo`, `quem_decide`, `proximo_passo`, `referencias_necessarias`. Serializar também os eventos referenciados disponíveis (venda/antecipação), identificados como contexto para não faturá-los duas vezes. Preservar campos de erro e valores desconhecidos. Referência ausente não é reconstruída. O vínculo da pendência/evento é obrigatório; não exportar apenas valores agregados.

Reutilizar leitura/seleção contratual/cálculo e regras de deduplicação existentes; não criar um segundo cálculo financeiro. Hash evidencia a fonte, não autoriza escolher um valor em conflito. A importação só ocorre por argumento explícito, nunca por varredura automática de JSONs. Sem condição comercial aprovada, os eventos continuam pendentes. Distinguir competência de origem e faturamento posterior: não relabelar setembro como outubro nem reabrir seu fechamento. **Contrato de controle de já faturados e projeção das notas posteriores ainda depende da decisão E2-P abaixo; E0 não autoriza somar backlog às notas atuais.**

**E3 / RF-20 — alertas.** Registro: `cnpj`/`ec`, `motivo_elegibilidade`, `evidencias_elegibilidade`, `pico_brl`, `data_pico`, `refs_antecipacoes`, `refs_reversoes`, `regra_id`, `texto`, `quem_decide`. Quem decide: Financeiro e Comercial. Valor de exposição não é comissão, faturamento ou sugestão de repasse. Não comparar com vendas do mês nem fixar lojista/total do exemplo. Sem evidência ou parâmetros suficientes, diagnóstico explícito; não inferir que um lojista é novo porque não recebemos seu histórico. Cálculo do pico e limiar dependem de E3-P.

**E4 / RF-17 — assistência.** Registro: `id_pendencia`, `banco`, `metodo` (IA/HUMANO), `conta_sugerida` (ou null), `confianca` (string decimal de 0 a 1 ou null sem sugestão), `justificativa`, `revisao_obrigatoria=true`, `provedor`, `modelo`. Contas fora da lista permitida, campos inválidos, erros de API e respostas sem fundamentação não viram sugestão válida. Registrar diagnóstico/encaminhamento humano. Sem IA, os candidatos recebem HUMANO nesse artefato, sem criar lançamento classificado ou mudar REGRA nos lançamentos existentes. O vínculo mantém a pendência oficial aberta; sugestão é metadado dessa pendência, não uma nova comissão ou um lançamento aprovado. Eventual aprovação humana e alteração de regras não fazem parte de E4.

A validação atual de classificação recalcula a saída determinística em `classificacao.validar`. Não inserir sugestões diretamente em `lancamentos_classificados.csv`, contornar o validador ou alterar sua cobertura para aparentar classificação aprovada. Se no futuro forem necessários campos extras na pendência oficial, a frente 1 deverá planejar juntos produtor, esquema e auditor; não é uma exigência deste contrato.

## CLI, configuração e publicação — decisões para implementação futura

- Preservar `--escopo checkout|alvo` e defaults. Não introduzir um terceiro escopo financeiro.
- Opção futura `--extras` recebe lista separada por vírgulas dos recursos `contestacoes,continuidade,alertas,assistencia`; ausência significa nenhum extra. É válida somente com `--escopo alvo`. Recurso desconhecido é erro de argumento antes de publicar.
- Opção futura `--sem-ia` impede qualquer chamada externa, inclusive se assistência foi selecionada; mantém encaminhamento HUMANO. Sem chave, assistência também funciona sem IA. IA real requer ativação explícita da assistência e configuração/chave válidas; sua ausência não invalida o alvo.
- Opção futura `--retomar-pendencias CAMINHO` exige seleção de continuidade e competência explícita. Retomada com efeito financeiro só será ligada após fechar E2-P e concluir seu aceite; nunca ativar apenas porque existe um arquivo na pasta.
- Seções futuras em `regras.toml`: `[extras.contestacoes]`, `[extras.continuidade]`, `[extras.alertas]`, `[extras.assistencia]`. A frente 2 documenta suas chaves em seu próprio documento; só a frente 1 as incorpora no TOML central. Limites de custo/tempo, provedor/modelo e credenciais de IA serão definidos em E4-P, sem fixar fornecedor a partir do placeholder atual de `.env.example`.
- Artefatos adicionais em `<saida>/extras/`: `contestacao_orbe.md`, `contestacao_ponte.md`, `continuidade.json`, `alertas.json`, `assistencia.json`, conforme recursos selecionados. JSONs usam o pacote versão 1. Textos são renderizados dos registros de contestação, sem cálculos novos. Esses arquivos não são novos CSVs oficiais.
- Um `extras/manifesto.json` próprio registra versão, hashes da base/fontes/configuração não secreta, arquivos produzidos e estados/motivos por recurso. A publicação dos seis CSVs e seu manifesto permanece independente; se a base mudar, o extra anterior não é válido para a nova base. Validar hashes antes de consumir.
- Frente 1 publica somente artefatos próprios com verificação de integridade, usando staging/marcador final e rejeitando sobrescrita de arquivo externo/modificado. Evitar saída antiga parecer atual após falha ou desativação; marcador do extra deve identificar o conjunto vigente. Não alterar as garantias de publicação do alvo. Sem extra selecionado, não consumir artefatos de execuções anteriores.
- Não incluir timestamps voláteis em conteúdo determinístico. Chamada de IA pode variar: registrar modelo/proveniência e separar do determinismo financeiro; testes usam retorno injetado. Nunca registrar chave ou payload financeiro integral em log.
- Artefatos extras locais continuam ignorados pela regra atual de `saida/`. Inclusão no pacote final e ajuste pontual do ignore ficam para E5, após sua validação, sem versionar ensaios.

## Propriedade dos arquivos

Todos os caminhos abaixo são futuros, salvo os arquivos existentes citados. Não criar diretórios ou módulos vazios para reservar espaço.

| Dono exclusivo | Arquivos/módulos |
| --- | --- |
| Frente 1 — seus recursos | `src/tarvo/extras/continuidade.py`, `alertas.py`; `tests/test_extra_continuidade.py`, `test_extra_alertas.py`; `docs/EXTRA_CONTINUIDADE_ALERTAS.md` |
| Frente 2 — seus recursos | `src/tarvo/extras/contestacoes.py`, `assistencia.py`; `tests/test_extra_contestacoes.py`, `test_extra_assistencia.py`; `docs/EXTRA_ASSISTENCIA_CONTESTACOES.md` |
| Frente 1 — integração compartilhada | `extras/__init__.py` e coordenação/publicação concreta em `extras/execucao.py`; `src/tarvo/__main__.py`, `execucao.py`, `modelos.py`, `partes.py`, `exportacao.py`, `contratos.py`, `notas.py` e eventual ajuste de `classificacao.py`; `regras.toml`, `pyproject.toml`, `.env.example`, `.gitignore`, README, HIPOTESES e este contrato; auditorias comuns e testes integrados |
| Preservar, sem alteração unilateral | Leitores/cálculos validados, documentos oficiais, pack, referências de saída e aceites históricos. Qualquer necessidade concreta de mudança é comunicada ao responsável pela integração antes de editar. |

A propriedade não é uma lista de arquivos a alterar: modificar apenas os indispensáveis à entrega autorizada. Frente 2 não edita os arquivos centrais; informa a necessidade e fornece testes/contrato. Suas funções não podem depender de um helper que ainda não exista na outra branch; usam os dados/formatos acima e fixtures sintéticas próprias. A frente 1 também não importa módulos ainda ausentes da frente 2 antes do merge. Não refatorar o motor para encaixar recursos futuros.

## Sequência, integração e aceite

1. Após commit autorizado de E0, confirmar mesmo SHA em ambos os computadores. Preservar alterações locais que apareçam antes de trocar branches; nunca usar reset/clean para preparar a divisão.
2. Frente 2 implementa E1 e depois E4, cada uma com testes de função e fixtures próprias. Frente 1 implementa E2 e E3, respeitando os bloqueios abaixo. Aprovação de E0 não autoriza começar nenhuma delas.
3. Integrar a frente 2 primeiro. A frente 1 incorpora essa base e faz a ligação única de CLI, configuração e publicação. Só nessa ligação os recursos passam a ter aceite de ponta a ponta; testes de módulo isolado não equivalem a CLI integrada validada.
4. Não resolver conflitos dos arquivos financeiros escolhendo “ours/theirs”. Conferir intenção, contrato, rastro e invariantes; gerar saídas finais somente após integração. Usar destinos locais novos durante desenvolvimento.
5. E5 exige a suíte existente (233 testes na base), os novos testes por recurso, auditor independente dos seis CSVs, matriz parcial, determinismo, outro mês sintético, RN-64, D-10 explícita e hashes dos oficiais. Sem extras, seis CSVs idênticos à base. Com assistência/alertas/textos/exportação de continuidade, valores financeiros também idênticos. Retomada financeira aprovada exige diferenças esperadas e rastreáveis por evento, teste de duplicação e competência, sem mudança retroativa dos originais.
6. Testar ausência de chave, `--sem-ia`, timeout/resposta inválida/conta proibida, modo sem recursos, extra bloqueado com alvo válido, artefato alterado ou obsoleto e falha de publicação. Repetir instalação pelo README nos dois computadores; informar SO/Python efetivamente testados. Contagem de exemplos é só regressão, nunca condição do motor.

## Decisões pendentes e limites de E0

| ID | Falta definir | Impacto e responsável |
| --- | --- | --- |
| E2-P | Controle persistente/arquivo de eventos já faturados, evidência de aprovação comercial e apresentação da competência original na nota do mês posterior | Comercial confirma condição/vigência; Financeiro valida apresentação/liberação; time define mecanismo mínimo e versionado de idempotência. Exportação/leitura podem ser desenvolvidas após autorização, mas não faturar backlog antes dessa definição. Nenhuma nova taxa é presumida. |
| E3-P | Resolvida pelo usuário para o recorte sem contrato: saldo de fim de dia, sem limiar, bloqueio explícito no TOML e pendência/rastro no alvo | Só a ampliação para ausência de histórico continua futura, exigindo lista explícita com evidência. Não inferir histórico nem horário. |
| E4-P | Provedor/modelo, dados mínimos enviados, limites de custo/tempo e credencial | Definição técnica antes de chamada real; chave exclusivamente em ambiente. Mocks e fallback não exigem API. Nenhuma dependência nova é autorizada por este documento. |
| D-10 | Respondida: spread inteiro, participação de 50% aplicada uma vez | Financeiro 11:33; retorno do checkpoint 2 às 16:01; decisão já registrada na branch e preservada em E3. |
| Atlas/RN-61 | Contrato comercial e datas/aprovações sem evidência | Continuam pendentes; não usar taxa antiga ou preencher metadado fictício para habilitar retomada. |

**E0 está documentalmente definida; a implementação extra continua não iniciada.** Não cria schema oficial novo, resolve decisão financeira, implementa integração externa, gera novos resultados ou autoriza commits. Mudança incompatível nesses contratos exige revisão coordenada antes de as duas frentes adotarem versões diferentes.
