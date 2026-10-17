# Gambito — fechamento Tarvo (nível alvo)

Monólito modular em Python, sem servidor ou banco. Processa os arquivos locais como recebidos e gera comissões de checkout e remessas, divergências, propostas de notas, classificação dos dois bancos, pendências e rastro. Não emite notas, executa pagamentos ou acessa Slack/e-mail externos. Há módulos extras de rascunhos de contestação, snapshot de pendências para continuidade e alerta de antecipação; o faturamento posterior da Atlas continua desabilitado.

## Instalar do zero

Python **3.11+**. Na raiz do projeto, em PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

Em macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

Não precisa ativar o ambiente. A dependência direta é `openpyxl`; a instalação também obtém suas dependências e o backend de build no índice de pacotes. Em algumas distribuições Linux, `venv` requer o pacote de sistema correspondente. Execução validada em **Windows/Python 3.12.10**; macOS/Linux não executados.

Não é necessária chave de API, `.env`, rede em execução, Context ou resultados anteriores. `.env.example` reserva eventual configuração de IA, fora do alvo e não consumida pelo motor.

Se o Windows restrito negar acesso à pasta temporária durante a instalação, antes de criar o ambiente:

```powershell
New-Item -ItemType Directory -Force .tmp | Out-Null
$env:TEMP = (Join-Path $PWD '.tmp')
$env:TMP = $env:TEMP
```

## Entradas e execução do alvo

Coloque as fontes originais em `data/raw/` ou outra pasta: todos os CSVs Orbe, XLSX de taxas, e-mail `.eml` da Ponte com anexo XLSX, plano Fênix CSV, extrato Aurora CSV e Meridiano OFX. Não edite, renomeie ou mova os originais para adequá-los ao código. Data pack e Context são materiais locais não versionados; a banca fornece as entradas.

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados data/raw --saida saida --regras regras.toml --escopo alvo
.\.venv\Scripts\python.exe tests/validar_saida.py --dados data/raw --saida saida --regras regras.toml --esperar COMPLETO --esperar-fechamento COMPLETO
```

Com o pack local fornecido, substitua **em ambos os comandos** `data/raw` por `Tarvo_Data_Pack_set2026`. Em macOS/Linux, use `.venv/bin/python` com os mesmos argumentos.

O leitor descobre CSVs Orbe por cabeçalho e reúne relatório/ajustes antes de relacionar estornos e reversões. Outras fontes são reconhecidas pelo conteúdo/formato, sem nome mensal fixo. Vários candidatos incompatíveis bloqueiam a dependência; não se escolhe silenciosamente um arquivo.

Parâmetros da CLI (`python -m tarvo --help`):

| Parâmetro | Comportamento |
| --- | --- |
| `--dados PASTA` | Obrigatório; fontes somente para leitura |
| `--saida PASTA` | Padrão `saida`; destino diferente das entradas |
| `--regras ARQUIVO` | Padrão `regras.toml` |
| `--escopo alvo` | Publica todos os resultados e avalia sua conclusão integrada |
| `--escopo checkout` | Padrão mantido por compatibilidade com o mínimo; publica somente sua fatia nos seis contratos |
| `--competencia AAAA-MM` | Seleção explícita necessária quando há vários meses; sem seleção, a competência vem das fontes |

Retorno **0** = COMPLETO, **2** = PROVISORIO, **1** = BLOQUEADO/erro. Pendências de negócio, como Atlas, não tornam automaticamente um resultado provisório (D-13). Fonte ausente/inválida ou rastro quebrado bloqueia os resultados dependentes; os demais permanecem disponíveis. Fontes presentes com linhas não reconhecidas geram diagnóstico e resultado provisório, sem estimar taxas/valores.

Para verificar apenas o mínimo sem substituir a entrega do alvo, use **outra pasta**, por exemplo `--saida .tmp/minimo --escopo checkout`. A auditoria aceita `--esperar` para o checkout e `--esperar-fechamento` para o agregado do alvo; use expectativas correspondentes às fontes fornecidas. O pacote completo no alvo deve passar com ambas COMPLETO.

## Saídas e entrega

Os seis arquivos obrigatórios ficam **diretamente em `saida/`**, conforme [FORMATO_SAIDA.md](docs/FORMATO_SAIDA.md):

- `comissoes_por_lojista.csv`
- `divergencias_taxa.csv`
- `notas_a_emitir.csv`
- `lancamentos_classificados.csv`
- `pendencias.csv`
- `rastro.csv`

CSV UTF-8, separador `;`, decimal com ponto, datas ISO e CNPJ numérico com 14 dígitos. Colunas extras registram regras, vínculos, natureza do valor e próximo passo, sem substituir o contrato obrigatório. Cada saída monetária tem rastro assinado cuja soma fecha exatamente; valor desconhecido permanece vazio e explicitamente identificado, nunca zero inventado.

`manifesto.json` é o marcador de publicação: guarda hashes, fontes, cobertura, status/motivos por parte e relatório, limitações e decisões pendentes. Consulte-o antes de consumir os CSVs. A versão atual é 9/etapa EXTRA_E3, com alertas de antecipação sem efeito nos cálculos financeiros. Bloqueio é diagnosticado no resumo/manifesto; partes bloqueadas não publicam valores. Se todas estiverem bloqueadas, os seis CSVs têm apenas cabeçalhos.

A CLI só substitui arquivos próprios com manifesto reconhecido e hashes anteriores intactos. Arquivo externo/modificado causa erro e exige destino novo. Publicação interrompida deixa marcador bloqueado; acesso transitório do Windows recebe até quatro tentativas, com espera total máxima de 350 ms. Erro persistente continua explícito.

**Os seis CSVs finais e o manifesto devem integrar a entrega no Git**, e não apenas ser reproduzíveis. O `.gitignore` permite esses sete arquivos na raiz de `saida/`, mantendo subpastas de ensaios ignoradas. O comando acima regenera a entrega a partir das entradas fornecidas. Não utilizar o escopo checkout nesse mesmo destino ao preparar a entrega do alvo.

`PROMPTS/` também integra a entrega obrigatória: `MOMENTOS.md` e os transcripts/exports/links originais de todas as sessões de IA. O time incluirá esse histórico como última etapa em `PROMPTS/sessoes/`, sem edição além da remoção de segredos/dados pessoais. Por orientação explícita do usuário, essa inclusão foi adiada e não bloqueia o aceite técnico desta revisão. Os resumos não versionados criados pelo agente foram removidos a seu pedido; os arquivos já versionados foram preservados.

## Regras e decisões

O cálculo usa `Decimal` e HALF_UP por evento. Fórmulas ficam nos módulos; condições comerciais, identidades e padrões ficam em `regras.toml`, com fonte, aprovação, aprovador/papel, data e natureza. Cada regra traz o horário da resposta do Slack que a sustenta ou da decisão do time; nenhuma decisão fica pendente. Não há valores de gabarito no motor.

- Checkout usa o contrato vigente, identidade explícita e faixas da operação. Nome semelhante não confirma identidade; taxa histórica não resolve contrato atual. Duplicatas idênticas entre CSVs contam uma vez; conflitos ficam pendentes.
- Estorno usa sua própria faixa e a condição da data da venda. Reversão de antecipação anula exatamente a contribuição original, sem usar a taxa atual.
- RN-64: devolução pelo efetivamente cobrado nas operações isentas, abatendo estornos elegíveis pela origem e vigência da venda. Referência validada: R$ 15.405,85 − R$ 9,08 = **R$ 15.396,77**, com 118 origens; estorno de agosto não isento permanece fora. Esses totais servem apenas à regressão.
- Atlas fica fora das comissões (D-07), identificada pelo CNPJ da aba antiga, sem importar taxa antiga nem estimar divergência. O contrato é decisão do comercial (Diego) e aparece como pendência operacional; quando a taxa for confirmada, setembro é faturado junto com outubro.
- RN-65 trata o ajuste pela linha, pois o layout não distingue arquivo principal de ajuste. Estorno ou reversão com original do próprio mês ausente em todos os CSVs entra na comissão pelos dados do evento e taxa contratada na data original declarada, com pendência para o Financeiro obter a original e fechamento provisório. Arquivos presentes na pasta são presumidos recebidos antes da aprovação. O operador deve colocar ajustes posteriores à aprovação na pasta/competência seguinte; a entrada não informa horários de chegada ou aprovação, portanto o motor não pode verificar essa premissa.
- Ponte usa participação pelo spread realizado; negativo irregular não vira receita. Ajuste AJUSTE REF preserva a origem e abate a participação uma vez. **D-10 respondida** (Financeiro, Slack 11:33; confirmada no retorno do checkpoint 2): o ajuste é mais uma operação, 50% do Spread R$ negativo, aplicado uma vez, abatendo a nota única do mês. Em setembro não há linha de ajuste.
- D-02: tolerância inclusiva de 0,01 p.p. de spread, equivalente à fração 0,0001. Valores reportado/solicitado do negativo têm naturezas distintas (D-11).
- Notas são propostas por saldo positivo validado; saldos não positivos geram pendência, sem transporte automático entre meses. Não somam divergência/devolução como receita.
- Classificação bancária usa conta analítica permitida e regra única por histórico/sinal. Sem correspondência, vira pendência. Recursos de lojistas e baixas de passivo não são receita; não são geradas provisões do mês nem conciliação entre bancos. Aurora preserva linha física (L9 no exemplo); Meridiano preserva FITID e dia local.

[HIPOTESES.md](HIPOTESES.md) conserva premissas e registros históricos, com o estado mais recente primeiro. Aceite técnico não ratifica decisões financeiras nem autoriza emissão/pagamento. Não há IA nem frontend. O módulo de contestação gera apenas rascunhos locais, e o snapshot da Atlas não autoriza faturamento; consulte [EXTRA_ASSISTENCIA_CONTESTACOES.md](docs/EXTRA_ASSISTENCIA_CONTESTACOES.md) e [EXTRA_CONTINUIDADE_ALERTAS.md](docs/EXTRA_CONTINUIDADE_ALERTAS.md). O alerta de antecipação está ativo como pendência revisável, sem alterar comissões ou notas.

## Testes e reprodução

Após instalar, sem configurar PYTHONPATH:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Em Windows restrito, use TEMP/TMP graváveis como indicado na instalação. Testes usam dados sintéticos/cópias isoladas e biblioteca padrão; não alteram os oficiais. O auditor independente relê as fontes e valida fórmulas, cobertura, contas, origens, contratos e rastros sem importar o motor.

Para repetir o aceite integrado completo, escolha **dois destinos novos**:

```powershell
.\.venv\Scripts\python.exe tests/aceite_integrado.py --dados Tarvo_Data_Pack_set2026 --regras regras.toml --saida .tmp/reproducao/saida --evidencias .tmp/reproducao/evidencias
```

Essa rotina exige todas as fontes, executa fora da raiz, compara determinismo e exercita perda/layout inválido de cada família, configuração ausente, remoção de resultados antigos e outro mês sintético com ajuste tardio. Sem configuração, verifica apenas o bloqueio estrutural, sem certificar cálculos. `resultado.json` só indica aprovação após todas as verificações.

As referências locais opcionais `--referencia saida/alvo-a6 --minimo saida/alvo-a1` servem apenas à regressão do mesmo pack; não são necessárias para rodar e não acompanham um clone. Nunca julgar outro dataset por totais conhecidos.

## Organização e evidências

`src/tarvo/` contém leitores, cadastro, regras financeiras, validação, coordenação por parte e exportação. Bancos dependem do respectivo extrato/plano/regras; notas da respectiva comissão; Ponte não depende do checkout. `tests/` reúne regressões e auditores. `regras.toml` é a configuração operacional; `discovery/` é análise exploratória opcional, fora das dependências de execução.

Os aceites `docs/ACEITE_MINIMO.md` e `docs/ACEITE_A1.md` a `docs/ACEITE_A7.md` são evidências históricas de decisões/regressões, não instruções para executar etapas antigas sobre o pacote final. Foram preservados; alguns apontam para logs locais ignorados. A referência de arquitetura/evolução é [EVOLUCAO_ALVO.md](docs/EVOLUCAO_ALVO.md), sem alteração de escopo nesta revisão.

A7 registrou 233 testes e aceite integrado em ambiente virtual novo. As verificações finais desta entrega têm evidências locais em `.tmp/revisao-entrega/`: 233 testes aprovados, 21 cenários integrados mais reprodução do mínimo, auditoria do pacote final e integridade de 108 arquivos oficiais/referências. A anexação posterior dos históricos originais de IA e o envio/publicação cabem aos participantes.
