# Frente 1 — E2: continuidade das pendências

E2 autorizada pelo usuário e implementada conforme [E0](EXTRA_E0.md). **E3/alertas não foi iniciada.** Preservados alvo, RN-64 corrigida, E1, decisões financeiras e arquivos oficiais. Sem novas dependências, branches ou commits. Histórico de IA continua adiado pelo usuário.

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

Até fechar E2-P, não há caminho automático de cobrança, mesmo que um contrato seja acrescentado ao TOML. D-10 e contrato da Atlas continuam explícitos. A taxa histórica não é importada como condição vigente. Nenhum cálculo financeiro alternativo foi criado.

Conforme E0 e o limite já aplicado a E1, CLI/publicação de extras ainda aguardam integração central; não há novo argumento `--retomar-pendencias` funcionando nesta etapa. A futura integração deve carregar conteúdo explicitamente e preservar a publicação independente do alvo. Esta entrega não cria coordenador, marcador compartilhado ou opções vazias para E3/E4.

## Validação

Testes em `tests/test_extra_continuidade.py`, sem depender dos arquivos oficiais: roundtrip, precisão/erros, origem/CNPJ desconhecidos, venda anterior, estorno/reversão, contexto não faturável, referências ausentes/ambíguas/cíclicas, conflitos/duplicatas, fonte provisória/bloqueada, versão/hash/schema adulterados, competência, cobertura, JSON truncado/chaves duplicadas, determinismo, não mutação e leitura de outra competência sem alterar fechamento.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_extra_continuidade.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Em macOS/Linux, substituir por `.venv/bin/python`. Executar conforme TEMP/TMP do README em Windows restrito. A primeira execução direcionada revelou uma expectativa de posição no teste de contexto; corrigida para selecionar pelo conteúdo, sem alterar ordenação do módulo.

No pack recebido, **57 pendências exportadas e relidas, zero não exportadas, com três eventos de contexto**. Pacote técnico COMPLETO, `faturamento_habilitado=false`. Referência local: `.tmp/extra-e2/continuidade.json`; números são somente evidência de regressão. Os seis CSVs oficiais não foram sobrescritos.

Validação final em Windows/Python 3.12.10: **274 testes aprovados em 59,011 s**, sendo 254 anteriores (incluindo E1) e 20 de E2. Auditor independente do alvo permaneceu COMPLETO. Conferência SHA-256 dos 158 arquivos preexistentes protegidos (motor/E1, teste E1, configurações, documentos oficiais, fontes e saídas) não encontrou alterações. Evidências em `.tmp/extra-e2/testes-final.log`, `testes-direcionados-final.log` e `integridade.json`. Ensaios anteriores foram preservados em logs separados; os casos de fixture foram corrigidos antes da suíte final.
