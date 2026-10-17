# Gambito — A7: aceite integrado e reprodução final

Checkout Tarvo com vendas, estornos, antecipações e reversões, preservando o mínimo validado e o isolamento de A1. A2 calcula divergências contratuais de checkout e a pendência de devolução da Casa; A3 acrescenta comissão realizada da Ponte, divergências de spread e pendências com rastro. A4 gera propostas de notas a partir das comissões validadas. A5 lê o plano Fênix e classifica o Aurora; A6 acrescenta o OFX do Meridiano, com `--escopo alvo`. Os seis CSVs oficiais continuam obrigatórios. O aceite integrado de A7 está registrado em `docs/ACEITE_A7.md`, com reprodução em ambiente Python novo no Windows e preservação das entregas anteriores. Atlas continua com contrato pendente, sem estimar comissão ou divergência. Não há emissão fiscal externa.

## Instalação

Python 3.11 ou superior. Na raiz do repositório, em PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

Em **macOS ou Linux**, na raiz do repositório (Python 3.11+ disponível como `python3`):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

Não é necessário ativar o ambiente: os exemplos usam seu executável diretamente. Em algumas distribuições Linux, o módulo `venv` é fornecido pelo pacote de sistema da distribuição. As instruções para macOS/Linux foram documentadas; o ambiente efetivamente testado está no aceite.

A única dependência de execução é `openpyxl` (XLSX). Não há servidor, banco, acesso a API ou chave obrigatória. `.env.example` fica reservado à eventual IA, fora desta entrega. Nenhuma variável desse arquivo é consumida agora.

## Executar

Coloque os arquivos originais do mês em uma pasta. Não os edite antes de executar:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados data/raw --saida saida --regras regras.toml
```

O padrão é `--escopo checkout`: exige concluir checkout e exportação das pendências existentes. Para consultar a conclusão do alvo, sem ativar funcionalidades futuras:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados data/raw --saida saida-alvo --regras regras.toml --escopo alvo
```

Em macOS/Linux, use `.venv/bin/python` com os mesmos argumentos. No alvo validado, com o pacote completo fornecido, `--escopo alvo` retorna `0` (`COMPLETO`). Ausência/falha de uma fonte pode produzir `2` (`PROVISORIO`) ou `1` (`BLOQUEADO`), conforme os resultados disponíveis. O aceite técnico não representa ratificação financeira de D-10 nem liberação de pagamentos ou notas. O comando padrão preserva o resultado do mínimo: no case atual retorna `0`. O escopo muda o critério de conclusão e a agregação dos relatórios; não executa leitores ou fórmulas inexistentes.

Para o data pack local, se disponível:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida --regras regras.toml
```

Execução, testes e auditoria em **macOS/Linux**:

```bash
.venv/bin/python -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida --regras regras.toml
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tests/validar_saida.py --dados Tarvo_Data_Pack_set2026 --saida saida --regras regras.toml --esperar COMPLETO --esperar-fechamento COMPLETO
```

Substitua `Tarvo_Data_Pack_set2026` por `data/raw` ou pela pasta recebida. Para escolher um mês, acrescente `--competencia AAAA-MM` ao comando de execução. Os mesmos códigos de saída documentados abaixo valem nas três plataformas.

O data pack e `Context/` não estão versionados. A banca fornece os arquivos originais. O leitor reconhece **todos os CSVs Orbe pelo cabeçalho**, sem nomes fixos, e um único XLSX de taxas. Relatório e ajustes são reunidos antes das referências. A aba vigente é configurada em `regras.toml`; várias planilhas candidatas continuam bloqueando essa dependência.

A competência vem de `data_movimento`, nunca da data da venda original. Com vários meses, escolha explicitamente, por exemplo `--competencia 2026-09`. Linhas válidas de outros meses ficam fora do cálculo e são contadas em `ingestao.fora_competencia`. Linhas com data inválida permanecem pendentes, pois não é seguro atribuir um mês. Uma reversão cujo original esteja fora do recorte exige revisão; não é reconstruída por estimativa.

A pasta completa com `01` e `06` é suportada. Também é possível executar somente relatório e taxas. A evidência final de A7 está em `docs/ACEITE_A7.md` e `saida/alvo-a7-final/`. A6 permanece preservada em `docs/ACEITE_A6.md` e `saida/alvo-a6/`. A5 permanece preservada em `docs/ACEITE_A5.md` e `saida/alvo-a5/`. A evidência de A4 em `docs/ACEITE_A4.md` e `saida/alvo-a4/` permanece preservada. As evidências anteriores, incluindo `docs/ACEITE_A3.md`, `saida/alvo-a3/`, A2 corrigida em `saida/alvo-a2-rn64/`, A1 em `saida/alvo-a1/` e os aceites do mínimo, foram preservadas.

## Escopo financeiro

- Calcula `VENDA` de débito, crédito à vista e Pix com 0 ou 1 parcela, e crédito parcelado nas faixas 2–6 e 7–12. Valores não positivos, 13x, modalidade desconhecida ou quantidade inconsistente ficam pendentes.
- Resolve EC/CNPJ pela planilha ou por vínculo explícito de `regras.toml`. Não associa por nome. Vínculos conflitantes ficam pendentes, sem sobrescrever o cadastro da planilha.
- Seleciona uma única linha contratual válida: data isolada representa início; `até dd/mm/aaaa` representa término; `a partir de dd/mm/aaaa` representa início. Limites são inclusivos; o limite não informado é aberto. Sobreposição, lacuna ou vigência desconhecida gera pendência.
- Observações desconhecidas continuam pendentes. Apenas os textos explicitamente esclarecidos por CNPJ em `regras.toml` podem ser utilizados, com fonte e interpretação registradas.
- Taxas XLSX numéricas são frações; taxas textuais exigem `%`. Texto sem unidade, fórmula ou taxa ausente vira pendência.
- Usa a taxa contratada, nunca `valor_taxa` ou taxa aplicada da Orbe. Arredonda cada contribuição com `Decimal`/`ROUND_HALF_UP` antes de somar.
- `ESTORNO` tem bruto negativo, referência e data original obrigatórias. Usa a faixa da própria linha e o contrato/isenção na data da venda; a contribuição pertence ao mês do movimento. Venda anterior ao mês pode estar ausente do arquivo: a data e a referência declaradas no estorno sustentam a seleção contratual, sem inventar arquivo histórico nem reabrir o mês anterior.
- Se a venda original estiver no arquivo, conferem-se tipo, EC, data e total estornado. Relação incompatível, valor acumulado acima da venda, ou referência ausente para venda do próprio mês gera pendência, sem escolher uma linha arbitrariamente. Não se infere outra faixa a partir da venda original.
- `ANTECIPACAO` usa bruto positivo, taxa da coluna Antecipação e a data do evento como base contratual, pois o relatório não vincula uma venda individual. Não há constante de 2,10% no motor. Taxa ausente gera pendência. Referência temporal diferente da data do evento requer esclarecimento.
- `REVERSAO ANTECIPACAO` exige a antecipação original disponível e calculável, mesmo que apareça depois no arquivo. Confere tipo, EC, data e bruto integral oposto; o valor é o negativo exato da contribuição original, com sua taxa, contrato e regra. Não usa a taxa atual nem soma outra antecipação. Reversão parcial, original ausente ou múltiplas reversões da mesma antecipação ficam pendentes.
- As abas em `entrada.abas_identidade` fornecem apenas CNPJ/nome/origem, nunca taxas ou vigência. Ausência dessas abas não bloqueia os contratos vigentes; identidades que dependeriam delas permanecem pendentes.
- A Atlas é identificada pela aba antiga e vínculo documentado, mas o bloqueio comercial mantém seus eventos pendentes. Nenhuma taxa antiga é importada. D-07 foi decidida pelo time: Atlas fica fora das comissões; cada pendência preserva CNPJ, origem e `valor_taxa` efetivamente cobrado, separado do bruto. Não se estima a comissão nem se importa taxa antiga.
- A isenção confirmada da Casa usa a data da venda e o intervalo configurado. Contribuições isentas são zero com rastro. Antes/depois do intervalo, aplica-se o contrato vigente, sem estender a isenção. A devolução pelo cobrado foi confirmada na RN-64 (antiga D-08), e implementada em A2. Conforme esclarecimento da RN-64 pelo usuário em 17/10/2026, estornos de vendas isentas abatem a devolução, pelo vínculo e pela data original, mesmo que o movimento ocorra fora da vigência. Estornos de vendas não isentas ficam fora. Referência atual: R$ 15.405,85 em 117 vendas/antecipações menos R$ 9,08 do estorno elegível = R$ 15.396,77 líquidos em 118 linhas. A interpretação anterior de excluir todos os estornos foi corrigida. Nenhum total é constante no código.
- A isenção também vale para a antecipação no seu período. A reversão de antecipação isenta permanece zero, mesmo após o fim da isenção. Estornos anteriores à isenção usam a condição anterior, com saldo negativo permitido nas comissões.
- D-10 continua pendente de confirmação financeira. A3 usa a decisão documentada do time para o ajuste; A4 usa sua contribuição já calculada, sem aplicar 50% novamente. Propostas com ajuste mostram D-10 na discriminação e no manifesto, além da pendência de A3; exigem revisão antes da liberação.
- A2 compara taxas contratuais e aplicadas por evento; valores são bruto × diferença de taxas, com HALF_UP por linha. Estornos entram negativos; taxa menor também diverge; truncamento com mesma taxa não diverge. Casa é concessão separada, somente em pendência; Atlas não tem divergência calculável sem contrato. IA não é utilizada nesta entrega.
- RN-42 a RN-45: proposta por CNPJ/competência com saldo positivo no checkout; proposta única à contraparte Ponte configurada, pela soma líquida da participação no mês. Zero/negativo gera pendência financeira `SEM_NOTA:`, com rastro completo, sem nota nem transporte para outro mês. A4 não soma divergências, devoluções ou acompanhamento como receita. A nota depende somente da respectiva comissão validada e da configuração; uma comissão provisória gera proposta provisória, identificada no manifesto.

## Resultados e fechamento parcial

`saida/` recebe:

- `comissoes_por_lojista.csv`: somente contribuições calculadas, agrupadas por CNPJ e linha de negócio; layout obrigatório.
- `rastro.csv`: uma contribuição assinada por evento calculado e por pendência com valor conhecido; soma exata por `id_saida`, incluindo zero e negativos. Colunas adicionais registram contrato, taxa, faixa, regra, vínculo, tipo, data base contratual e referência original. Os IDs `CHECKOUT:...` e `PENDENCIA:...` separam os números reconciliados: valores cobrados da Atlas não entram na soma das comissões. O vínculo ao original é metadado, sem repetir seu valor e duplicar a soma. Arquivo histórico não disponível permanece vazio.
- `pendencias.csv`: no mínimo, uma linha por origem; em A2, também grupos de contestação/devolução com detalhe no rastro, com as seis colunas oficiais e `proximo_passo`, arquivo, linha, CNPJ, categoria e natureza do valor como extras. Para Atlas, `valor_brl` é o cobrado pela Orbe. Em pendências de dados, um bruto disponível é identificado como `BRUTO_REFERENCIA`, nunca como comissão ou cobrança a executar. Valor desconhecido fica vazio e explicitamente provisório, sem rastro monetário inventado.
- `divergencias_taxa.csv`: no escopo alvo, uma linha por diferença de taxa de checkout ou spread de remessa, com os sete campos oficiais. Contestação líquida por lojista em `pendencias.csv`, com detalhe assinado no rastro. Nas pendências agregadas, `ref_origem` mantém um `id_transacao` real (a primeira operação ordenada), com arquivo/linha correspondentes; o conjunto completo de origens e valores é ligado pelo `id_saida` no rastro. Casa tem pendência separada pelo líquido de cobranças e estornos elegíveis de vendas isentas. IDs `DIVERGENCIA:`, `CONTESTACAO_ORBE:` e `DEVOLUCAO_CHECKOUT:` distinguem as naturezas; não some esses valores como comissões. No escopo padrão, A2–A6 não são publicadas.
- `notas_a_emitir.csv`: no escopo alvo, propostas com os seis campos oficiais, serviço e competência na discriminação. IDs `NOTA:CHECKOUT:` e `NOTA:REMESSA:`; cada contribuição da comissão é copiada ao rastro, preservando valores, sinais e vínculos. Saldos não positivos ficam em `pendencias.csv`, com IDs `SEM_NOTA:` e natureza própria. No escopo padrão, somente cabeçalho.
- `lancamentos_classificados.csv`: no escopo alvo, movimentos Aurora e Meridiano classificados, com linha física ou FITID respectivamente, data ISO, descrição e valor preservados, conta analítica permitida, método REGRA e confiança 1. IDs `AURORA:`/`MERIDIANO:`. Histórico sem regra única ou conta permitida fica em pendência; crédito sem identificação e repasse devolvido também exigem revisão. O status agregado reflete os dois bancos. No escopo padrão, somente cabeçalho.
- `manifesto.json`: situação, competência, hashes de cada fonte e saída, cobertura física, duplicidades, avisos, limitações, decisões documentadas/pendentes e todas as pendências por referência, tipo, categoria, próximo passo e responsável. O valor bruto de uma pendência não representa comissão nem valor a cobrar.

O terminal exibe resumo, decisões, pendências e status de cada CSV; `proximo_passo` fica no manifesto e no CSV de pendências. O manifesto usa **versão 8**, etapa `ALVO_A6`, e registra os parâmetros de notas e classificação com fonte/aprovação. `situacao`, `escopo_situacao=CHECKOUT`, `rastro_validado` e `total_parcial_brl` conservam o significado legado, exclusivamente do checkout. O código de saída segue `situacao_comando`: agrega CHECKOUT e PENDENCIAS_CHECKOUT no escopo padrão, ou todas as partes no escopo alvo. Nos casos normais do mínimo os códigos e os seis CSVs permanecem iguais.

`partes` declara situação, motivos, dependências de fontes/resultados, validação e cobertura de cada parte. `fechamento` sempre resume **todo o alvo**, inclusive etapas não implementadas: completo somente com todas as partes completas; provisório com ao menos uma parte disponível e alguma incompleta; bloqueado quando todas estão bloqueadas. Pendência de negócio não impõe provisório ao módulo, conforme D-13.

`resultados` identifica por CSV os produtores, as partes bloqueadas, a situação no escopo escolhido e `situacao_alvo`. Comissões, divergências e notas estão disponíveis para checkout e remessa; Aurora e Meridiano estão disponíveis, sujeitos às próprias fontes e regras. A cobertura das partes NOTAS conta saldos de comissão de origem, não transações físicas nem quantidade de notas; vários saldos de remessa compõem uma única nota. Não confunda total do checkout com total das outras linhas de negócio. IDs e ordenação são estáveis; mesma entrada e regras geram os mesmos arquivos.

| Situação | Significado | Código de saída |
| --- | --- | --- |
| `COMPLETO` | Todas as partes exigidas pelo escopo disponíveis e validadas. Atlas continua pendente para o Comercial. Só significa alvo concluído se esse for o escopo e todas as partes estiverem completas. | `0` |
| `PROVISORIO` | Há partes exigidas provisórias ou bloqueadas, mas existe resultado válido. Publica somente as partes validadas, sem estimar valores. | `2` |
| `BLOQUEADO` | Todas as partes exigidas bloqueadas. Sem valores dessas partes; resultados independentes de outro escopo têm situação própria. Erros de uso/escrita também retornam 1. | `1` |

Ausência de fontes do alvo não bloqueia checkout. Orbe, taxas e regras são inspecionadas separadamente. Se todos os candidatos Orbe forem inválidos, bloqueia; se houver fontes válidas e outra identificada com layout inválido, fecha provisoriamente as válidas e registra o arquivo rejeitado, hash e motivo. A cobertura de linhas refere-se aos arquivos lidos com sucesso; linhas de fonte estruturalmente inválida não são contadas como processadas.

IDs idênticos entre arquivos são calculados uma vez, com ocorrência repetida em pendência e origem canônica pela ordenação dos arquivos. IDs com conteúdo conflitante deixam **todas** as ocorrências pendentes, assim como eventos que os referenciam. Não se escolhe um valor financeiro entre conflitos. ID ausente ou repetido dentro do mesmo arquivo continua sendo falha estrutural da fonte, para não tornar ambígua a referência oficial `arquivo + id_transacao`.

**Consulte sempre `manifesto.json` e verifique seus hashes antes de consumir CSVs.** Ele é publicado por último como marcador de validade. Se a publicação for interrompida, o marcador permanece bloqueado. Só os arquivos registrados em `arquivos` pertencem à execução atual.

Uma parte bloqueada publica diagnóstico e não contribui com valores nos CSVs. Arquivos compartilhados conservam apenas as partes validadas; se não houver produtor válido, ficam só com cabeçalho. Se checkout estiver bloqueado, seu total é `null`, nunca zero. Se todas as partes estiverem bloqueadas, os seis CSVs contêm só cabeçalhos. Na falha de escrita, o marcador de publicação permanece bloqueado para a execução inteira, pois não é seguro declarar um conjunto de arquivos parcialmente substituído como publicado. Arquivos externos ou modificados pelo usuário nunca são sobrescritos/removidos: o comando falha e pede outra pasta de saída. Não use a pasta das entradas como saída. Outros arquivos presentes em `saida/` não fazem parte desta entrega.

## Ponte (A3)

Coloque os e-mails `.eml` na pasta de entrada. O leitor encontra anexos XLSX e cabeçalhos por conteúdo, processa em memória e preserva a origem `email.eml::anexo.xlsx::aba`, Nº Operação e linha física. Não extrai anexos para o disco nem acessa e-mail/Slack externos. E-mail inválido é diagnosticado; arquivos válidos independentes continuam disponíveis de forma provisória.

- Comissão por operação = participação configurada × Spread R$ realizado, HALF_UP por linha. Competência normal pela contratação; liquidação em outro mês e APROVADO C/ RESSALVA não excluem operação.
- Nº repetido conta uma vez e gera pendência; conteúdo financeiro conflitante ou ocorrência ilegível com o mesmo número não autoriza escolher um valor.
- Diferença de spread usa o percentual, PTAX e valor ME pelo valor cheio. Tolerância inclusiva D-02 no TOML; não recalcular a participação pela diferença contratual. Spread contratual em branco/padrão usa 1,5% conforme RN-32; CNPJ novo preserva comissão realizada e exige cadastro comercial. A vigência de spread da Mundo Aberto fica restrita ao início confirmado de julho.
- Negativo irregular fica fora da comissão/divergências normais. D-11: `valor_brl` e `valor_solicitado_brl` contêm realizado − spread contratado × PTAX × valor ME; `valor_reportado_brl` conserva o negativo original. O rastro fecha com o principal, sem inverter o sinal. Pedido desconhecido permanece vazio e provisório.
- AJUSTE REF é reconhecido antes do negativo irregular e da duplicidade. A linha tem número próprio e contribuição negativa pela participação, uma única vez. A competência declarada no novo relatório (ou seleção explícita, se não declarada) determina o mês do ajuste; sem ambos, usa-se a contratação da nova linha, registrada como premissa. `ref_original` e o rastro preservam a operação anterior; arquivo histórico ausente permanece vazio.
- D-10 continua pendente: aplicar 50% é decisão documentada do time, não confirmação financeira. Cada ajuste gera pendência para revisão do Financeiro. A4 deriva a proposta do saldo validado, com ressalva do ajuste, sem aplicar novamente o percentual.
- Acompanhamento do TED usa a participação calculada para conferência futura; não cria recebimento nem supõe desconto da Ponte.

Os extras de D-11 e `ref_original`/linha física no rastro são publicados somente no escopo alvo, mantendo as colunas e os seis CSVs do mínimo. Fonte Orbe ausente não bloqueia Ponte. Sem planilha, a comissão realizada permanece disponível; comparação contratual fica bloqueada. Se houver negativo sem contrato, seu pedido fica desconhecido e REMESSAS provisório, conservando as comissões conhecidas.

## Dependências e isolamento de A1/A2/A3

- CHECKOUT e PENDENCIAS_CHECKOUT usam Orbe, taxas e regras, mas têm validações independentes. Uma falha no rastro de comissões pode preservar as pendências já identificadas e validadas, e vice-versa.
- DIVERGENCIAS_CHECKOUT e DEVOLUCAO_CASA usam as contribuições contratuais resolvidas, Orbe, taxas e regras. Cada parte tem validação e rastro próprios; não dependem da agregação válida de comissões. Campo aplicado inválido afeta divergências; cobrado inválido afeta devolução. Valor desconhecido permanece vazio e provisório.
- Remessas declara Ponte + regras; divergências de remessa também declaram `contratos_remessa` (leitura independente da mesma planilha). Notas declaram dependência da respectiva comissão. Cada banco declara seu extrato + plano de contas + regras, sem depender do outro banco.
- As partes futuras são **não implementadas**. Suas fontes não lidas aparecem como `NAO_AVALIADA`; a existência de um arquivo não é tratada como validação de seu conteúdo. Não foram adicionados leitores de Ponte ou bancos em A1.
- O validador comum confere esquema, IDs, cobertura e soma do rastro por saída; o checkout conserva suas verificações financeiras específicas. Dependência bloqueada ou conflito de IDs bloqueia os produtores/dependentes envolvidos, preservando partes independentes.
- Cobertura global do mínimo conta somente contribuições e pendências validadas; registros cujo destino ficou bloqueado aparecem em `bloqueadas`. Contagens por parte descrevem seu domínio e não devem ser somadas indiscriminadamente: um evento pode produzir comissão e outro resultado derivado.

## Verificação

Os testes usam `unittest` da biblioteca padrão, sem dependência de desenvolvimento adicional:

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src')
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

As amostras são sintéticas e criadas em diretório temporário: arredondamento positivo/negativo, rastro, faixas 2/6/7/12/13x, vigências, conflitos de identidade, histórico sem taxas antigas, estornos de mês anterior e anteriores à isenção, antecipação pela taxa própria, anulação exclusiva da antecipação, ordem das linhas, referências inconsistentes, reversões duplicadas, fontes faltantes, determinismo e proteção das saídas. Totais do case não são usados como regras.

## Configuração e decisões pendentes

`regras.toml` contém os três ECs complementares confirmados, vínculo da Atlas, bloqueio por falta de confirmação comercial, período de isenção da Casa e observações esclarecidas. Valores, datas e identificadores do caso ficam nessa configuração, nunca como constantes no código de cálculo. Cada regra exige `fonte`, `aprovacao`, `aprovador`, `aprovado_em` e `natureza`. Datas conhecidas ficam em ISO; `NAO_INFORMADO` explicita lacunas reais do registro, também listadas em `fontes.regras.metadados_incompletos`. Interpretações técnicas não recebem aprovação financeira fictícia.

D-07 e RN-64 constam como decisões documentadas. D-10 permanece com confirmação financeira pendente: o time escolheu 50% do Spread R$ negativo, mas remessas continuam fora do mínimo. Datas ausentes de decisões/interpretações precisam ser completadas com evidência, sem impedir a leitura dos contratos já confirmados. Não é preciso API nem nova dependência para a Entrega 4.

## Aceite independente e reprodução do zero

Em uma cópia nova do projeto, repita a instalação acima e coloque todos os CSVs Orbe e o XLSX de taxas em `data/raw/`. Execute sem chaves e sem configurar `PYTHONPATH`:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados data/raw --saida saida --regras regras.toml
$codigo = $LASTEXITCODE
```

Código `0` é esperado no escopo padrão para o case com as pendências comerciais da Atlas e fontes válidas. Código `2` indica que apenas parte do escopo foi validada, inclusive falha isolada de comissão ou pendência; com `--escopo alvo`, também indica etapas futuras ainda bloqueadas. Código `1` indica bloqueio ou erro. Não trate qualquer saída diferente de zero como fechamento concluído.

O verificador independente usa apenas a biblioteca padrão, sem importar o motor:

```powershell
.\.venv\Scripts\python.exe tests/validar_saida.py --dados data/raw --saida saida --regras regras.toml --esperar COMPLETO --esperar-fechamento PROVISORIO
```

O auditor conserva `--esperar` como expectativa do checkout e aceita `--esperar-fechamento` para o agregado do alvo. Ele confere cabeçalhos e domínios, hashes das fontes/saídas, IDs de todas as linhas Orbe, destino único em rastro ou pendência, contagens, datas/competência, soma exata por comissão e pendência com valor conhecido, seis cabeçalhos oficiais em ordem e preservação das decisões pendentes. Em A2, também confere fórmula das divergências pelas fontes, contestação líquida, recorte da devolução, valores efetivamente cobrados e reconciliação por natureza, sem importar o motor. A auditoria de A3 também lê MIME/XML do XLSX usando biblioteca padrão, verifica participação por operação, competência, spread, D-11, origens físicas e cobertura, sem importar o motor. Os testes de regras verificam a seleção contratual.

Para determinismo, rode o mesmo comando em duas pastas de saída novas (por exemplo, `saida-a` e `saida-b`) e compare os bytes dos seis CSVs e `manifesto.json`. O teste `test_execucao_instalada_fora_da_raiz_sem_chaves_e_repeticao` também verifica repetição sem depender do diretório do código. Os demais testes de aceite exercitam outro mês sintético, modalidade desconhecida, 13x, EC sem cadastro, fonte ausente, layout inválido, soma/referência adulterada e publicação interrompida.

Os testes de subprocesso exigem o pacote instalado pelo comando de instalação. Nenhum dado do `Context/`, do `.env` ou de serviços externos é necessário. O verificador retorna `0` quando o artefato tem a situação esperada e é coerente; `1` quando detecta inconsistência. Aceite técnico não confirma o contrato da Atlas, não responde à pergunta financeira de D-10 e não valida funcionalidades futuras do alvo. D-02 está aplicada: 0,01 p.p. = fração 0,0001, com diferenças no limite inclusive tratadas como arredondamento. D-04 está implementada: a referência é a linha física inicial do registro; L9 é o primeiro movimento do exemplo, sem constante no leitor. Meridiano e o aceite integrado A7 foram validados no ambiente Windows documentado.

## Estrutura

`src/tarvo/` separa execução, modelos, leitores, cadastro, cálculo, validação e exportação. `ResultadoParte` em `modelos.py` contém o contrato interno; `partes.py` declara dependências e isola validações; `contratos.py` reúne os layouts usados por coordenação, validação e exportação, sem duplicar definições. `regras.toml` contém a configuração desta fatia e decisões pendentes. `docs/FORMATO_SAIDA.md` conserva o contrato do desafio. `HIPOTESES.md` registra limites e decisões. `PROMPTS/` registra o uso de IA.

A4 acrescenta `notas.py` para a projeção das comissões validadas; a publicação revalida sua correspondência exata com valores e origens, bloqueando somente o dependente se houver adulteração. O auditor independente `tests/auditoria_a4.py` reconstrói saldos a partir dos CSVs auditados e confere tomadores, competência, ausência de transporte, sinais e metadados de cada origem.

A proposta de expansão está em [docs/EVOLUCAO_ALVO.md](docs/EVOLUCAO_ALVO.md), com A1–A6 implementadas e A7 validada tecnicamente no ambiente documentado; extras não iniciados. Nenhuma etapa futura é iniciada por executar o comando atual.

## Plano Fênix e Aurora (A5)

O plano é identificado pelo cabeçalho `COD_CONTA` e o extrato pelo cabeçalho bancário, sem nomes fixos. Aceitam UTF-8 e o encoding legado do pack. Mais de um candidato bloqueia a dependência, sem escolher pelo nome. Códigos repetidos ou estrutura inválida bloqueiam o plano; somente contas ANALITICA com ACEITA_LANCTO=S podem ser usadas. A contrapartida vem de `classificacao_aurora` no TOML, com fonte, critério, aprovador/papel e data; mapeamentos técnicos não recebem aprovação financeira fictícia.

O histórico é normalizado apenas para correspondência (minúsculas, sem acento, espaços normalizados); a saída preserva a descrição original. Uma única regra deve corresponder ao histórico e ao sinal. Os aliases de repasse confirmados ficam na configuração; não há identificação de lojista por nome semelhante nem associação obrigatória ao checkout. Novo destinatário/histórico sem regra vira pendência financeira, sem criar conta ou receita. A devolução da RN-53 usa a contraparte confirmada na regra; outra devolução exige revisão. Transferência própria exige o destino configurado; não confirma recebimento no outro banco.

Folha, INSS, FGTS, ISS e DARFs conhecidos baixam passivos; não são geradas provisões. Créditos Orbe baixam recebíveis, sem conciliação parcela a parcela. Saldo anterior/final e rodapé conhecidos não são movimentos; linhas desconhecidas posteriores ao cabeçalho recebem diagnóstico, sem descarte silencioso. Cada movimento do recorte tem um destino principal (classificado ou pendente); uma pendência adicional de revisão não duplica a cobertura. Cada saída monetária tem rastro próprio com valor assinado e linha física; a classificação também aponta para a regra e a linha da conta no plano.

A competência do Aurora é independente do checkout e vem das datas dos movimentos. Se houver vários meses, informe `--competencia AAAA-MM`; outros meses são contados em `fontes.aurora.fora_competencia`. Datas inválidas não podem ser descartadas pelo recorte. Não são exigidos dados Orbe, Ponte ou taxas para classificar o Aurora. Sem plano/extrato ou com layout inválido, somente Aurora fica bloqueado; o mínimo e A1–A4 continuam disponíveis conforme suas próprias fontes.

A publicação reconfere origens, contas, valores, regras e cobertura. `tests/auditoria_a5.py` relê o plano e o extrato com biblioteca padrão, sem importar o motor. O manifesto detalha EXTRATO_AURORA e EXTRATO_MERIDIANO; ausência/falha de um banco não impede o outro. A6 reutiliza os mesmos critérios de conta permitida, cobertura e validação de domínio.

## Meridiano (A6)

O leitor aceita o contrato OFX SGML com encoding declarado cp1252 ou UTF-8, preservando acentos, FITID e o dia local de DTPOSTED, sem conversão UTC. Campos-folha podem ter fechamento omitido; agregados precisam estar completos. Mais de um OFX, várias contas no mesmo arquivo, moeda diferente de BRL, status bancário de erro ou estrutura truncada bloqueiam somente Meridiano. Não há conversão cambial, reparo de encoding por adivinhação ou preenchimento de valor desconhecido por zero.

FITID repetido deixa todas as ocorrências pendentes, mesmo com valores iguais: não existe regra oficial autorizando escolher uma delas no banco. A verificação ocorre antes do recorte mensal; um conflito em outro mês não desaparece pelo filtro. FITID ausente usa referência física somente no diagnóstico, sem inventar FITID ou classificar o movimento. Pendências Meridiano incluem a linha física no ID para distinguir ocorrências, preservando o FITID original em ref_origem quando disponível.

`classificacao_meridiano` contém critérios documentados por histórico e sinal. Recursos recebidos de lojistas e sua liquidação à Ponte movimentam o passivo de remessas; não são receita. A Ponte Aérea é lojista, independente da Ponte Câmbio. Comissão recebida baixa o recebível; aplicações/resgates movimentam a conta de aplicação, sem inferir rendimento pela diferença; rendimento explicitamente informado, tarifas, seguro e IOF seguem suas contas. Novos históricos ou correspondências ambíguas exigem revisão. Não há conciliação entre bancos nem confirmação automática de transferências em trânsito.

`tests/auditoria_a6.py` relê OFX com HTMLParser da biblioteca padrão e reutiliza a conferência independente das contas/origens; não importa o motor. Os resultados computacionais do pacote completo podem ficar COMPLETO mesmo com pendências de negócio, conforme D-13. A7 acrescentou a auditoria global dos seis arquivos e a reprodução documentada; extras continuam fora do escopo.

## Aceite integrado e reprodução (A7)

Aceite técnico executado em Windows/Python 3.12.10, inclusive em uma cópia limpa com ambiente virtual novo e dependências instaladas conforme o projeto. A instalação inicial usa acesso ao índice de pacotes (inclusive backend de build); a execução não requer rede, chave de API, Context ou saídas prévias. macOS/Linux têm instruções, mas não foram executados/certificados nesta sessão.

Em ambientes Windows restritos, se a criação do ambiente falhar por acesso à pasta temporária do usuário, antes de `python -m venv .venv` use uma pasta gravável no projeto:

```powershell
New-Item -ItemType Directory -Force .tmp | Out-Null
$env:TEMP = (Join-Path $PWD '.tmp')
$env:TMP = $env:TEMP
```

Para repetir o aceite de um conjunto completo de fontes, depois da instalação, escolha duas pastas novas:

```powershell
.\.venv\Scripts\python.exe tests/aceite_integrado.py --dados Tarvo_Data_Pack_set2026 --regras regras.toml --saida saida/validacao-nova --evidencias .tmp/aceite-novo
```

O comando executa os seis resultados e o mínimo fora da raiz, audita fontes/formatos/valores/rastros, compara uma repetição em bytes, testa perda/layout inválido de cada fonte em cópias isoladas, bloqueio sem configuração, remoção de saídas antigas e outubro/2032 sintético com ajuste tardio e D-10. Falha de execução ou conferência reprova o aceite; configuração ausente permite apenas conferir o bloqueio estrutural, sem declarar cálculo financeiro validado. `resultado.json` só recebe aprovado=true após todas as verificações. Os originais são somente lidos.

Para comparar especificamente o mesmo pacote original com as evidências preservadas, acrescente `--referencia saida/alvo-a6 --minimo saida/alvo-a1`. Não use essas referências para julgar outro dataset: números conhecidos são regressão, não regra. Para fontes parciais, use o comando normal e confira os estados/motivos no manifesto; o aceite completo exige todas as dependências.

A auditoria integrada acrescenta IDs únicos entre relatórios, produtor validado, domínios, datas, precisão, destinos conhecidos e reconciliação global, além das auditorias específicas de cada fonte. O terminal informa contagem por método em cada banco. Publicação mantém o manifesto como marcador final; bloqueios transitórios de acesso do Windows têm até quatro tentativas de substituição atômica (pausas totais de até 350 ms). Falha persistente continua sendo erro; não é transformada em fechamento válido.

O manifesto mantém versão 8/etapa ALVO_A6 porque A7 valida a entrega existente, sem novo módulo financeiro ou alteração de layout. O registro de aceite e as evidências finais de A7 ficam separados. D-10, contrato da Atlas e datas de aprovação não comprovadas continuam explícitos; aceite técnico não equivale à aprovação dessas decisões. Nenhum extra, pagamento, emissão fiscal ou integração externa foi acrescentado.
