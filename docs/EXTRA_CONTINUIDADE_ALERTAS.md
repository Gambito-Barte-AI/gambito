# Frente 1 — E2: continuidade das pendências

E2 autorizada pelo usuário e implementada conforme [E0](EXTRA_E0.md). E3 foi autorizada posteriormente e está descrita ao fim deste documento. Preservados alvo, RN-64 corrigida, E1 e arquivos oficiais. Sem novas dependências, branches ou commits. Histórico de IA continua adiado pelo usuário.

## O que está entregue

`src/tarvo/extras/continuidade.py` oferece duas funções sem I/O ou mutação das entradas:

```python
from tarvo.extras.continuidade import exportar_pendencias, ler_pendencias

pacote = exportar_pendencias(resultado_validado, {})
# O chamador serializa o pacote com json.dumps; a função não grava arquivos.
recebido = ler_pendencias(conteudo_json)  # também aceita dict ou bytes UTF-8
```

A exportação recebe `Resultado` do motor, utiliza a parte validada `PENDENCIAS_CHECKOUT` e associa suas linhas aos eventos normalizados pela origem exata (arquivo, referência, linha física). Não depende de nome de lojista, data, nome do arquivo mensal ou quantidade do exemplo. Pendências de bancos/Ponte não são misturadas ao reprocessamento de checkout; RF-19 trata os eventos pendentes da Orbe, incluindo Atlas.

**Configuração E2: `{}`.** Não há parâmetro que habilite cobrança. A leitura recebe conteúdo explícito, nunca abre caminhos, varre pastas ou acessa rede. JSON inválido, chaves duplicadas, versão desconhecida ou pacote adulterado geram `ErroEntrada`; a exportação retorna diagnóstico local sem alterar o fechamento financeiro.

## Contrato persistido — versão 1

Envelope E0: `versao`, `recurso=continuidade`, `situacao`, `motivos`, `registros`. Extensões necessárias ao snapshot:

| Campo | Responsabilidade |
| --- | --- |
| `fontes` | Nomes e SHA-256 disponíveis de Orbe, taxas e configuração de origem; não copia segredos nem o pack completo |
| `cobertura` | Pendências lidas, exportadas e não exportadas; cada pendência tem registro ou diagnóstico |
| `diagnosticos` | ID da pendência e motivo quando não é possível obter um Evento recuperável |
| `origem_provisoria` | Conserva a limitação da parte que originou o snapshot |
| `faturamento_habilitado` | Sempre false nesta entrega; a leitura rejeita true |
| `limitacoes_financeiras` | E2-P, D-10 e necessidade de condição comercial documentada, sem inventar aprovação |
| `sha256_conteudo` | Hash da representação JSON canônica sem esse próprio campo; detecta alteração do conteúdo |

Cada registro preserva os campos definidos em E0: ID estável `CONTINUIDADE:<id_pendencia>`, ID da pendência, CNPJ ou null, competência original, todos os campos de Evento, motivo, próximo passo, responsável, origens e referências necessárias. Acrescenta `tipo`, `categoria`, `natureza_valor`, `valor_pendencia_brl` para não confundir bruto de referência, cobrança informada pela Orbe e valor desconhecido. Isso não cria comissão ou direito de cobrar.

Dinheiro é string decimal com ponto e duas casas, sem arredondar dado de entrada; percentuais preservam unidade em pontos percentuais e precisão de `Evento.taxa_aplicada_pct`. Datas ISO, parcelas inteiras ou null, CNPJ numérico de 14 dígitos ou null. Campos de erro e valores desconhecidos são preservados; não viram zero. A leitura verifica tipos, precisão, datas reais, vínculo do ID com a origem e competência, fontes, cobertura e campos obrigatórios.

## Estornos, reversões e conflitos

- Venda/antecipação original disponível é incluída em `contextos`, com papel obrigatório `CONTEXTO_NAO_FATURAVEL`. Pode também ser uma pendência principal em seu próprio registro: repetição de contexto não a transforma em segunda cobrança.
- `referencias_necessarias` informa origem disponível ou estado AUSENTE/AMBIGUA/CICLICA. Vínculos não são adivinhados nem aprovados financeiramente pelo snapshot. Ciclos terminam com diagnóstico; referência histórica ausente não é reconstruída.
- Referência ambígua conserva as candidatas disponíveis como contexto, sem escolher uma. Conflito no ID do evento principal impede exportá-lo; pendência fica no original e recebe diagnóstico no pacote.
- Linha inválida sem Evento normalizado recebe diagnóstico de não exportação. Não é fabricado um evento a partir de valores agregados ou do CSV de pendências. O arquivo oficial permanece íntegro para revisão.
- A leitura confere consistência de eventos/contextos entre registros, rejeita duplicação de pendências e referências disponíveis omitidas em outro registro. Contextos não relacionados, hash inconsistente ou tentativa de tornar contexto faturável são rejeitados.

Estado COMPLETO significa exportação/leitura tecnicamente consistente, **não liberação financeira**. Referência incompleta, fonte provisória ou perda de evento gera PARCIAL, ou BLOQUEADO se não há registro recuperável. Falha global/schema inválido não conserva registros aparentemente utilizáveis. Sem pendências e com parte validada, o pacote vazio é COMPLETO.

O hash de conteúdo detecta corrupção, não é assinatura de aprovação nem prova de autenticidade. Hashes de fonte são preservados como evidência; a leitura sem I/O não compara arquivos externos. A futura integração deve validar o vínculo ao manifesto/base correspondente, conforme E0. Um documento refeito por terceiros não adquire autorização financeira por ter um hash correto.

## Limite financeiro e próxima integração

O pacote pode ser lido no mês seguinte, mas **ainda não é somado às comissões ou notas desse mês**. Competência original é preservada; não se renomeia o movimento antigo como movimento atual, não se reabre fechamento e não se altera regra aprovada.

E2-P continua pendente: controle persistente do que já foi faturado, evidência de aprovação comercial e apresentação da competência de origem na nota posterior. IDs estáveis e rejeição de duplicatas dentro do snapshot são entregues; **não substituem esse controle entre fechamentos**. Ler o mesmo pacote novamente retorna o mesmo conteúdo, sem criar lançamento ou registrar suposto faturamento.

Até fechar E2-P, não há caminho automático de cobrança, mesmo que um contrato seja acrescentado ao TOML. Contrato da Atlas continua pendente; D-10 está confirmada, com 50% aplicada uma vez. A taxa histórica não é importada como condição vigente. Nenhum cálculo financeiro alternativo foi criado. A leitura de snapshots antigos de E2 preserva seus textos históricos e hashes; novas exportações informam D-10 confirmada. Texto histórico não representa pendência atual.

CLI/publicação de E1/E2 ainda aguardam integração central; não há argumento `--retomar-pendencias` funcionando. A futura integração deve carregar conteúdo explicitamente e preservar a publicação independente do alvo. E3 foi ligada posteriormente aos CSVs por autorização específica, sem ligar retomada financeira ou E4.

## Validação

Testes em `tests/test_extra_continuidade.py`, sem depender dos arquivos oficiais: roundtrip, precisão/erros, origem/CNPJ desconhecidos, venda anterior, estorno/reversão, contexto não faturável, referências ausentes/ambíguas/cíclicas, conflitos/duplicatas, fonte provisória/bloqueada, versão/hash/schema adulterados, competência, cobertura, JSON truncado/chaves duplicadas, determinismo, não mutação e leitura de outra competência sem alterar fechamento.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_extra_continuidade.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Em macOS/Linux, substituir por `.venv/bin/python`. Executar conforme TEMP/TMP do README em Windows restrito. A primeira execução direcionada revelou uma expectativa de posição no teste de contexto; corrigida para selecionar pelo conteúdo, sem alterar ordenação do módulo.

No pack recebido, **57 pendências exportadas e relidas, zero não exportadas, com três eventos de contexto**. Pacote técnico COMPLETO, `faturamento_habilitado=false`. Referência local: `.tmp/extra-e2/continuidade.json`; números são somente evidência de regressão. Os seis CSVs oficiais não foram sobrescritos.

Validação final em Windows/Python 3.12.10: **274 testes aprovados em 59,011 s**, sendo 254 anteriores (incluindo E1) e 20 de E2. Auditor independente do alvo permaneceu COMPLETO. Conferência SHA-256 dos 158 arquivos preexistentes protegidos (motor/E1, teste E1, configurações, documentos oficiais, fontes e saídas) não encontrou alterações. Evidências em `.tmp/extra-e2/testes-final.log`, `testes-direcionados-final.log` e `integridade.json`. Ensaios anteriores foram preservados em logs separados; os casos de fixture foram corrigidos antes da suíte final.

## E3 — alertas de antecipação

Critério aprovado explicitamente pelo usuário em 17/10/2026, a partir de RN-63, D-03 e Slack 12:50. O Financeiro aceitou o uso de pico e delegou o critério ao time; os detalhes abaixo são decisão do time/usuário, sem atribuir aprovação individual fictícia ao Financeiro.

- **Pico:** maior saldo acumulado ao fim de cada dia, somando brutos antecipados e reversões integralmente vinculadas às antecipações disponíveis no período. Todas as operações do dia entram antes da comparação; não existe ordem intradia inventada. Empate conserva a primeira data do pico.
- **Gatilho:** qualquer antecipação positiva de lojista elegível; sem corte monetário. Antecipação e reversão no mesmo dia podem produzir alerta de pico zero, com rastro zero líquido. Saldo final zero não apaga um pico de dia anterior.
- **Elegibilidade:** CNPJ explicitamente presente em `contratos_bloqueados`, resolvido por EC/cadastro/vínculo forte. Falha de contrato/fonte bloqueia a parte; não prova ausência de contrato. ECs do mesmo CNPJ são agrupados em uma pendência. Ausência de histórico não é deduzida; essa metade da RN-63 não foi implementada e exigirá fonte/lista explícita mantida pelo time.
- **Reversão sem original disponível no período:** data, valor e referência são listados como não abatidos. Não reconstrói exposição anterior. Referência incompatível, duplicidade ou reversão repetida é diagnosticada, sem publicar pico definitivo desse lojista.
- **Abrangência:** exposição observada somente nos eventos fornecidos, com referência inicial computacional zero. A exposição anterior é declarada desconhecida; o pico não é o saldo completo da agenda. Não se compara com vendas nem se cria limite de repasse.

Implementação em `src/tarvo/extras/alertas.py`: API E0 `analisar_antecipacoes(eventos, elegibilidade, config)` sem I/O/mutação; adaptador para `ResultadoParte` e revalidação por recomposição antes da publicação. Configuração `[extras.alertas]` no TOML, com fonte, aprovação, aprovador, data e natureza DECISAO_TIME. Configuração inválida ou fonte indisponível produz diagnóstico isolado; comissões, divergências, notas e bancos conservam suas dependências.

### Saída e execução

Uma linha por CNPJ/competência em `pendencias.csv`: ID `ALERTA_ANTECIPACAO:<competencia>:<cnpj>`, tipo ALERTA_ANTECIPACAO, valor=pico, quem_decide="Financeiro e Comercial", próximo passo de avaliar o risco enquanto o contrato não for confirmado. Motivo inclui data do pico, total antecipado, saldo final, cada reversão (data, valor, referência e se abatida) e exposição anterior desconhecida.

O rastro do pico contém somente contribuições até o dia do pico, inclusive reversões abatidas até essa data. Sua soma é exatamente o pico; reversões posteriores não reduzem retroativamente esse número e permanecem no motivo. Natureza PICO_EXPOSICAO_OBSERVADA distingue alerta de comissão, cobrança, devolução e faturamento. Não somar o alerta a outros valores do fechamento.

Parte independente ALERTAS_ANTECIPACAO depende de Orbe/taxas/regras, com validação e status no manifesto. Manifesto versão 9/EXTRA_E3 quando o critério está ativado; sem configuração do alerta, preserva versão 8. O comando continua o mesmo:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida --regras regras.toml --escopo alvo
.\.venv\Scripts\python.exe tests/validar_saida.py --dados Tarvo_Data_Pack_set2026 --saida saida --regras regras.toml --esperar COMPLETO --esperar-fechamento COMPLETO
```

`habilitado=false` desativa E3; sem seção, também não é ativada. Escopo checkout continua publicando os seis CSVs do mínimo sem alertas. Não foi acrescentado frontend, IA, `--extras`, publicação de E1/E2 ou retomada financeira. E4 não iniciada.

### Evidência E3

Nos arquivos 01+06, uma pendência da Atlas: **pico R$ 183.581,24 em 24/09**, total antecipado **R$ 235.943,10**, saldo final observado **R$ 127.230,96**. As reversões de R$ 52.361,86 (17/09) e R$ 56.350,28 (26/09) são explicitadas. **Seis contribuições no rastro do pico**: três antecipações de 15/09, a reversão de 17/09 e duas antecipações de 24/09. Esses números ficam apenas em evidências/testes, nunca como condições no motor.

Auditor independente `tests/auditoria_e3.py` relê Orbe e identidade do XLSX/TOML com biblioteca padrão, sem importar tarvo. Confere elegibilidade, cobertura, pico diário, motivo/reversões e origens/valores do rastro. `tests/test_extra_alertas.py` usa dados sintéticos para limites, dias mistos, vínculos, isolamento e adulteração. A matriz de A7 foi estendida somente para reconhecer a nova dependência de Orbe/taxas.

D-10 já estava confirmada na branch: regra D-10_AJUSTE_PONTE e notas já descontavam 50% uma vez. E3 apenas atualiza avisos antigos em E1/E2 e preserva leitura de snapshots legados. Os documentos originais e os aceites históricos não foram reescritos.

Aceite final E3 em Windows/Python 3.12.10: **296 testes aprovados**, matriz integrada com **21 cenários**, determinismo e regressão do mínimo aprovados. Logs em `.tmp/extra-e3/testes-reproducao-final.log` e `.tmp/extra-e3/matriz.log`. Auditor independente executado novamente sobre `saida/`: COMPLETO, seis contratos CSV, hashes de fontes e rastro exato.

Com autorização explícita do usuário, o pacote desatualizado da raiz (CSVs do mínimo incompatíveis com o manifesto do alvo) foi integralmente copiado para `.tmp/extra-e3/entrega-anterior`, com conferência de hashes, antes da regeneração. `saida/` contém agora 35 comissões, 115 divergências, 21 notas, 184 lançamentos, 84 pendências e 5.086 linhas de rastro. Os quatro CSVs financeiros são byte a byte idênticos à execução alvo anterior a E3; pendências e rastro anteriores permanecem iguais após retirar somente os registros do alerta. Os 17 arquivos de fontes/documentação protegidos conferidos por SHA-256 permaneceram intactos. Evidência em `.tmp/extra-e3/integridade.json`. Backup e logs são locais, ignorados pelo Git; não substituem os arquivos oficiais preservados. Nenhum commit realizado; E4 não iniciada.
