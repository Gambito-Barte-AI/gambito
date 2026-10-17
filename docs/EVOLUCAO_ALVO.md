# Proposta de evolução para o nível alvo

**A1, A2 e A3 implementadas; A4–A7 permanecem somente planejamento.** A1 não acrescenta cálculos financeiros. Aceite em `docs/ACEITE_A1.md`. Referência principal: `docs/documentação-geral.md`, especialmente RF-02/RF-07 a RF-16 e Parte IV; layouts em `docs/FORMATO_SAIDA.md`. A2 acrescenta divergências contratuais de checkout e pendência de devolução da Casa; aceite em `docs/ACEITE_A2.md`.

## Ponto de partida e arquitetura

Manter Python 3.11+, biblioteca padrão, openpyxl, Decimal, regras TOML, CLI e processamento em memória. Não introduzir servidor, banco de dados, filas, serviços externos ou motor genérico de regras. O volume e os formatos atuais não justificam outra infraestrutura.

Hoje: checkout, identidade, contratos, múltiplos CSVs Orbe e validação de contribuições já funcionam. A revisão final passou a exportar as pendências existentes e seus valores no rastro; os seis nomes oficiais são publicados, mas notas e classificação ainda contêm somente cabeçalhos e estão bloqueados. Divergências de checkout e devolução da Casa são publicadas no escopo alvo. Isso não é aceite funcional do alvo.

Fluxo proposto:

```text
Pasta + regras.toml
  -> inspeção de fontes / coordenador de dependências (execucao.py)
     -> Orbe + taxas -> checkout existente -> divergências checkout / Casa
     -> e-mail Ponte -> remessas -> divergências remessa (com contrato)
     -> Aurora + plano de contas -> classificação Aurora
     -> Meridiano + plano de contas -> classificação Meridiano
  -> notas derivadas das comissões validadas
  -> pendências + origens + cobertura + status por parte
  -> validação de cada resultado
  -> seis CSVs + manifesto + resumo no mesmo comando
```

Acrescentar arquivos somente na etapa que os utiliza:

| Local | Alteração futura |
| --- | --- |
| `leitores/ponte.py` | Ler MIME com `email` da biblioteca padrão e XLSX em memória com openpyxl; normalizar números, datas, operações e origens sem extrair anexos por caminhos fornecidos pelo e-mail |
| `leitores/plano_contas.py`, `leitores/aurora.py`, `leitores/meridiano.py` | Leitores independentes; plano latin-1, referência física Aurora e FITID Meridiano; validar o formato real OFX antes de escolher o parser |
| `modelos.py` | Acrescentar os tipos de operação Ponte, movimento bancário e conta; enriquecer Evento/Contrato apenas com os campos necessários às divergências |
| `remessas.py`, `divergencias.py`, `notas.py`, `classificacao.py` | Funções de cálculo e decisão sem I/O; recebem modelos e regras, retornam valores, origens e pendências |
| `execucao.py`, `validacao.py`, `exportacao.py`, `__main__.py` | Coordenar dependências explícitas, agregar resultados válidos, validar e publicar os layouts já existentes |
| `regras.toml` | Parâmetros documentados, condições comerciais e padrões bancários com fonte, aprovador e data; não colocar fórmulas no TOML |
| `tests/` | Casos de regras, contratos, cobertura, falhas independentes e aceite dos seis resultados |

A1 acrescentou apenas ResultadoParte, partes.py e contratos.py para coordenação e layouts compartilhados. Leitores e cálculos futuros só serão criados nas etapas autorizadas; não criar classes abstratas, repositórios de persistência ou interfaces de plugin. Reutilizar Origem, Pendencia, Cadastro, arredondamento e a proteção da publicação.

A3 acrescentou OperacaoPonte/ContratoRemessa, o leitor MIME/XLSX e remessas.py. A fonte `contratos_remessa` tem leitura e estado independentes do cadastro de checkout, embora venha do mesmo XLSX. REMESSAS não depende de CHECKOUT nem de sua soma; DIVERGENCIAS_REMESSA usa os contratos, sem depender do rastro válido das comissões. Acompanhamento e D-11 ficam na parte REMESSAS; pedido de negativo sem contrato permanece desconhecido/provisório, mantendo a comissão disponível. Aceite em `docs/ACEITE_A3.md`.

## Contratos e dependências

Cada parte devolve dados tipados, contribuições assinadas, pendências, fontes, contagens de destino e situação com motivos. Em A1, Resultado foi ampliado com ResultadoParte para comportar partes independentes; não transformar a ausência de uma fonte em falha global.

| Resultado | Dependências |
| --- | --- |
| Comissão checkout | Orbe + cadastro/taxas + regras |
| Comissão remessa | Relatório Ponte + regras; CNPJ fora da planilha não impede calcular a participação pelo realizado (RN-40) |
| Divergências checkout / Casa | Orbe, taxas aplicadas/cobradas, contrato e regras da data original |
| Divergências remessa | Ponte + spread contratado/PTAX/valor em moeda estrangeira + regras |
| Notas checkout / Ponte | Respectivas comissões validadas; falha de uma linha de negócio não bloqueia a outra |
| Classificação de cada banco | Respectivo extrato + plano de contas + regras; um banco não depende do outro |
| Pendências e rastro | Resultados e diagnósticos das partes disponíveis; nenhum valor desconhecido pode virar zero |

Como há arquivos compartilhados (comissões, notas, divergências, rastro), o manifesto precisa detalhar as partes, por exemplo CHECKOUT e REMESSA, além do arquivo agregado. Se publicar apenas um subconjunto, explicitar a limitação e a parte bloqueada; não chamar o fechamento total de completo. Manter D-13 para os módulos, D-12 para resultados bloqueados e a lista/hash exata do que foi produzido na execução atual. A1 definiu: padrão --escopo checkout com mínimo preservado; --escopo alvo com conclusão agregada de todas as partes. Códigos 0/2/1 para completo/provisório/bloqueado; manifesto versão 5 conserva os campos legados do checkout e acrescenta partes, fechamento, situacao_comando e produtores de cada CSV.

IDs devem ser estáveis e distintos por natureza/competência/contraparte. Um evento pode alimentar comissão, divergência e pendência: isso são destinos derivados diferentes, não três linhas de entrada. Cobertura física/econômica e reconciliação monetária por id_saida são invariantes distintas. A nota soma contribuições já validadas sem lançar o mesmo valor duas vezes no mesmo id_saida. Metadado de referência à operação original não repete o valor original.

## Plano incremental

Cada etapa mantém o checkout e os contratos já aceitos funcionando. Os relatórios ainda não implementados permanecem explicitamente bloqueados. Não usar totais de exemplo como constantes de cálculo.

| Entrega / prioridade | Objetivo e componentes | Dependências | Critérios de aceite, testes e evidência |
| --- | --- | --- | --- |
| **A1 / P0 — implementada: isolamento por resultado** | Ampliar Resultado/execução/validação/publicação para partes independentes e resumo por resultado; definir status agregado e compatibilidade do comando | Mínimo revisado | Fonte Ponte ausente mantém checkout válido; testes de rastro quebrado isolam só a parte afetada; seis layouts, motivos e hashes corretos. Evidência: manifestos de casos completo/parcial/bloqueado e regressão do checkout sem alteração de valores |
| **A2 / P1 — implementada: divergências checkout e Casa** | Preservar taxa aplicada na leitura; comparar contratada versus aplicada por transação; exportar divergências e pendência de devolução, mantendo identidades e vigências existentes | A1 | RN-20 a RN-27/RN-64 e D-09: truncamento com mesma taxa não é divergência; estorno com taxa errada entra negativo e pela própria faixa; Bridge conforme contrato; Atlas não vira divergência. Casa só em pendência, com soma do valor_taxa elegível, com abatimento de estornos de vendas isentas pela origem e vigência original, conforme esclarecimento do usuário em 17/10/2026. Testes de centavos, datas-limite, antecipações e rastro; evidência: CSVs e reconciliação separados por natureza |
| **A3 / P1 — implementada: Ponte de ponta a ponta** | Leitor .eml/XLSX, comissão pelo realizado e divergências contratuais em remessas.py/divergencias.py; parâmetros no TOML | A1; pode ser desenvolvido após A2 para reaproveitar o contrato de divergências | RN-31 a RN-41: 50% por operação com HALF_UP; competência pela contratação; duplicata uma vez com pendência; ressalva não exclui; novo CNPJ gera cadastro pendente sem perder comissão. Ajuste AJUSTE REF reconhecido antes de negativo irregular e duplicata; amostra sintética obrigatória. RN-35/D-11: valor reportado e solicitado distintos, rastro do valor principal. RN-30/D-02: limites abaixo, igual e acima de 0,01 p.p.; conversão explícita para fração 0,0001. Evidência: relatório de remessas, origens no anexo, cobertura e somas exatas; ausência da planilha não impede realizado, apenas comparação que dependa do contrato |
| **A4 / P1 — notas a emitir** | Gerar notas.py a partir das comissões validadas; estender pendências/rastro | A1 e comissões checkout já validadas; A3 para notas de remessa. Divergências de A2 não bloqueiam notas | RN-42 a RN-45: uma nota por lojista com saldo positivo no checkout; uma nota total para a Ponte; zero/negativo sem nota, sem transporte para mês seguinte e com pendência; ajuste abate a nota do mês. Evidência: reconciliação de cada nota e ausência de nota para Atlas/Casa conforme resultado real; somente arquivo de proposta, sem emissão fiscal externa |
| **A5 / P1 — plano + Aurora** | Leitor do plano, leitor Aurora e classificação determinística | A1; independente da Ponte | RN-46 a RN-57: primeira transação física L9, mesmo com linhas de preâmbulo; contas existentes e que aceitam lançamento; folha/impostos baixam passivo, não geram provisão; valores preservados; não conciliar Orbe parcela a parcela. Padrão ambíguo vira pendência, sem conta inventada. Evidência: cobertura real de cada movimento e rastro; arquivo ausente não altera checkout |
| **A6 / P1 — Meridiano** | Leitor OFX e reutilização da classificação, sem acoplar os bancos | A5 para regras/plano/classificador; validação do leitor pode começar antes | FITID estável, encoding/data/sinal preservados; duplicidades e IDs ausentes explícitos; retorno de repasse e transferências próprios tratados pelas regras; falta de Aurora não bloqueia Meridiano e vice-versa. Evidência: ambos no CSV oficial com domínio banco correto; confrontar a quantidade real com a referência documental de 184 movimentos, sem fixá-la no motor |
| **A7 / P0 de aceite — fechamento alvo** | Auditor dos seis resultados, matriz de falhas, resumo, README e instruções de reprodução | A1–A6 | Instalação e comando únicos, execução repetida idêntica, outro mês sintético, chegada tardia de ajustes, perda de cada fonte e falhas de rastro/contrato. Todas as linhas têm destino explicado e todos os id_saida monetários reconciliam; nenhuma saída antiga reaparece como atual. Evidência: logs, hashes, status por parte e teste do zero no ambiente suportado; testar de fato macOS/Linux antes de afirmar compatibilidade executada |

A1, A2 e A3 foram autorizadas e implementadas. A4–A7 continuam futuras. Próxima etapa: **A4**, somente após nova aprovação explícita; não iniciada nesta sessão.

## Riscos, decisões e limites

- **D-10:** existe decisão do time de usar 50% do Spread R$ do ajuste, porém a pergunta financeira sobre a natureza do valor segue aberta. Manter parâmetro e proveniência explícitos; não anunciar confirmação do financeiro, nem aplicar 50% duas vezes. Regular e ajuste precisam de testes distintos.
- **Atlas:** contrato continua pendente para o Comercial. D-07 sobre apresentação está resolvida; taxa antiga segue proibida. Recuperação/faturamento posterior pertence ao extra, não ao alvo.
- **Casa:** RN-64 resolveu a base da devolução; D-09 escolheu só pendência, sem linhas opcionais de divergência. Confirmar dados elegíveis pelo cálculo, nunca fixar totais. Referência atual: 117 vendas/antecipações, R$ 15.405,85, menos R$ 9,08 de estorno de venda isenta = R$ 15.396,77 líquidos em 118 linhas. Estorno de agosto não isento fica fora. A interpretação anterior de exclusão genérica foi corrigida pelo esclarecimento do usuário. Não reabrir D-08 como decisão pendente.
- **D-02, D-05 e D-06:** decisões existentes do time, não regras novas a inventar. Preservar tolerância de spread, critério percentual da Mundo Aberto e conta 2.1.01.001 para repasse devolvido, com fonte/data no TOML quando implementados.
- **Aprovações:** completar as datas que não constam nos registros técnicos/time com evidência; não deduzir aprovação financeira de timestamp do Git.
- **RN-13/RN-65:** preservar o estorno histórico explicitamente confirmado sem exigir agosto. Se a regra de referência ausente for interpretada de modo mais restrito, registrar validação do time antes de alterar esse comportamento e o aceite.
- **Anexos e OFX:** conferir nomes de abas, unidades de percentuais, encoding e estrutura real; não seguir URLs, executar conteúdo ou gravar anexos usando caminhos arbitrários. Sem integração de e-mail/Slack nesta etapa; arquivos são fornecidos localmente.
- **Classificação:** correspondência por chave forte/regra explícita; não usar semelhança de nome como identidade. Ausência de conta analítica válida vira pendência. Não emitir provisões do mês corrente.
- **Saídas compartilhadas:** maior risco de retrabalho é misturar valor de comissão, valor cobrado, diferença contratual e pedido de contestação. Tipar/conservar cada valor com sua natureza e referência desde a leitura; testar cobertura separadamente da quantidade de registros do rastro.
- **Escopo:** IA opcional, alertas de antecipação, contestação em texto, reaproveitamento da Atlas e frontend permanecem extras/depois do alvo. Não acrescentar API, banco ou dependência apenas para reservar espaço futuro.
