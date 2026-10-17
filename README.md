# Gambito — A2: divergências de checkout e devolução da Casa

Checkout Tarvo com vendas, estornos, antecipações e reversões, preservando o mínimo validado e o isolamento de A1. A2 calcula divergências contratuais de checkout e a pendência de devolução da Casa; publica esses resultados com `--escopo alvo`. Os seis CSVs oficiais continuam obrigatórios. Notas, remessas e classificação bancária ainda não foram implementadas; o fechamento do alvo permanece provisório. Atlas continua com contrato pendente, sem estimar comissão ou divergência.

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

Em macOS/Linux, use `.venv/bin/python` com os mesmos argumentos. Nesta A2, com checkout válido, `--escopo alvo` retorna `2` (`PROVISORIO`), pois remessas, divergências de remessa, notas e bancos continuam não implementados. O comando padrão preserva o resultado do mínimo: no case atual retorna `0`. O escopo muda o critério de conclusão e a agregação dos relatórios; não executa leitores ou fórmulas inexistentes.

Para o data pack local, se disponível:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida --regras regras.toml
```

Execução, testes e auditoria em **macOS/Linux**:

```bash
.venv/bin/python -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida --regras regras.toml
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tests/validar_saida.py --dados Tarvo_Data_Pack_set2026 --saida saida --regras regras.toml --esperar COMPLETO --esperar-fechamento PROVISORIO
```

Substitua `Tarvo_Data_Pack_set2026` por `data/raw` ou pela pasta recebida. Para escolher um mês, acrescente `--competencia AAAA-MM` ao comando de execução. Os mesmos códigos de saída documentados abaixo valem nas três plataformas.

O data pack e `Context/` não estão versionados. A banca fornece os arquivos originais. O leitor reconhece **todos os CSVs Orbe pelo cabeçalho**, sem nomes fixos, e um único XLSX de taxas. Relatório e ajustes são reunidos antes das referências. A aba vigente é configurada em `regras.toml`; várias planilhas candidatas continuam bloqueando essa dependência.

A competência vem de `data_movimento`, nunca da data da venda original. Com vários meses, escolha explicitamente, por exemplo `--competencia 2026-09`. Linhas válidas de outros meses ficam fora do cálculo e são contadas em `ingestao.fora_competencia`. Linhas com data inválida permanecem pendentes, pois não é seguro atribuir um mês. Uma reversão cujo original esteja fora do recorte exige revisão; não é reconstruída por estimativa.

A pasta completa com `01` e `06` é suportada. Também é possível executar somente relatório e taxas. As evidências antigas em `saida/entrega2/`, `entrega3/` e `entrega4/` foram preservadas; representam a versão anterior. O aceite atual de A2 está em `docs/ACEITE_A2.md` e `saida/alvo-a2-rn64/`. A evidência de A1 em `docs/ACEITE_A1.md` e `saida/alvo-a1/` permanece preservada. O mínimo anterior em `docs/ACEITE_MINIMO.md`, `saida/revisao-pre-alvo/` e `saida/aceite-multiorbe/` foi preservado.

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
- D-10 continua fora do escopo. Saldos zero/negativos são preservados nas comissões; nenhuma nota, transferência de saldo ou devolução é gerada.
- A2 compara taxas contratuais e aplicadas por evento; valores são bruto × diferença de taxas, com HALF_UP por linha. Estornos entram negativos; taxa menor também diverge; truncamento com mesma taxa não diverge. Casa é concessão separada, somente em pendência; Atlas não tem divergência calculável sem contrato. Remessas, notas, extratos e IA não são calculados.

## Resultados e fechamento parcial

`saida/` recebe:

- `comissoes_por_lojista.csv`: somente contribuições calculadas, agrupadas por CNPJ; layout obrigatório.
- `rastro.csv`: uma contribuição assinada por evento calculado e por pendência com valor conhecido; soma exata por `id_saida`, incluindo zero e negativos. Colunas adicionais registram contrato, taxa, faixa, regra, vínculo, tipo, data base contratual e referência original. Os IDs `CHECKOUT:...` e `PENDENCIA:...` separam os números reconciliados: valores cobrados da Atlas não entram na soma das comissões. O vínculo ao original é metadado, sem repetir seu valor e duplicar a soma. Arquivo histórico não disponível permanece vazio.
- `pendencias.csv`: no mínimo, uma linha por origem; em A2, também grupos de contestação/devolução com detalhe no rastro, com as seis colunas oficiais e `proximo_passo`, arquivo, linha, CNPJ, categoria e natureza do valor como extras. Para Atlas, `valor_brl` é o cobrado pela Orbe. Em pendências de dados, um bruto disponível é identificado como `BRUTO_REFERENCIA`, nunca como comissão ou cobrança a executar. Valor desconhecido fica vazio e explicitamente provisório, sem rastro monetário inventado.
- `divergencias_taxa.csv`: no escopo alvo, uma linha por diferença de taxa de checkout, com os sete campos oficiais. Contestação líquida por lojista em `pendencias.csv`, com detalhe assinado no rastro. Nas pendências agregadas, `ref_origem` mantém um `id_transacao` real (a primeira operação ordenada), com arquivo/linha correspondentes; o conjunto completo de origens e valores é ligado pelo `id_saida` no rastro. Casa tem pendência separada pelo cobrado nas vendas/antecipações isentas. IDs `DIVERGENCIA:`, `CONTESTACAO_ORBE:` e `DEVOLUCAO_CHECKOUT:` distinguem as naturezas; não some esses valores como comissões. No escopo padrão, A2 não é publicada.
- `notas_a_emitir.csv`, `lancamentos_classificados.csv`: somente cabeçalhos, explicitamente bloqueados como etapas futuras.
- `manifesto.json`: situação, competência, hashes de cada fonte e saída, cobertura física, duplicidades, avisos, limitações, decisões documentadas/pendentes e todas as pendências por referência, tipo, categoria, próximo passo e responsável. O valor bruto de uma pendência não representa comissão nem valor a cobrar.

O terminal exibe resumo, decisões, pendências e status de cada CSV; `proximo_passo` fica no manifesto e no CSV de pendências. O manifesto usa **versão 4**. `situacao`, `escopo_situacao=CHECKOUT`, `rastro_validado` e `total_parcial_brl` conservam o significado legado, exclusivamente do checkout. O código de saída agora segue `situacao_comando`: agrega CHECKOUT e PENDENCIAS_CHECKOUT no escopo padrão, ou todas as partes no escopo alvo. Nos casos normais do mínimo os códigos e os seis CSVs permanecem iguais.

`partes` declara situação, motivos, dependências de fontes/resultados, validação e cobertura de cada parte. `fechamento` sempre resume **todo o alvo**, inclusive etapas não implementadas: completo somente com todas as partes completas; provisório com ao menos uma parte disponível e alguma incompleta; bloqueado quando todas estão bloqueadas. Pendência de negócio não impõe provisório ao módulo, conforme D-13.

`resultados` identifica por CSV os produtores, as partes bloqueadas, a situação no escopo escolhido e `situacao_alvo`. Assim, comissões podem estar completas no escopo checkout e parciais no alvo, pois remessas ainda faltam. Não confunda total do checkout com total das outras linhas de negócio. IDs e ordenação são estáveis; mesma entrada e regras geram os mesmos arquivos.

| Situação | Significado | Código de saída |
| --- | --- | --- |
| `COMPLETO` | Todas as partes exigidas pelo escopo disponíveis e validadas. Atlas continua pendente para o Comercial. Só significa alvo concluído se esse for o escopo e todas as partes estiverem completas. | `0` |
| `PROVISORIO` | Há partes exigidas provisórias ou bloqueadas, mas existe resultado válido. Publica somente as partes validadas, sem estimar valores. | `2` |
| `BLOQUEADO` | Todas as partes exigidas bloqueadas. Sem valores dessas partes; resultados independentes de outro escopo têm situação própria. Erros de uso/escrita também retornam 1. | `1` |

Ausência de fontes do alvo não bloqueia checkout. Orbe, taxas e regras são inspecionadas separadamente. Se todos os candidatos Orbe forem inválidos, bloqueia; se houver fontes válidas e outra identificada com layout inválido, fecha provisoriamente as válidas e registra o arquivo rejeitado, hash e motivo. A cobertura de linhas refere-se aos arquivos lidos com sucesso; linhas de fonte estruturalmente inválida não são contadas como processadas.

IDs idênticos entre arquivos são calculados uma vez, com ocorrência repetida em pendência e origem canônica pela ordenação dos arquivos. IDs com conteúdo conflitante deixam **todas** as ocorrências pendentes, assim como eventos que os referenciam. Não se escolhe um valor financeiro entre conflitos. ID ausente ou repetido dentro do mesmo arquivo continua sendo falha estrutural da fonte, para não tornar ambígua a referência oficial `arquivo + id_transacao`.

**Consulte sempre `manifesto.json` e verifique seus hashes antes de consumir CSVs.** Ele é publicado por último como marcador de validade. Se a publicação for interrompida, o marcador permanece bloqueado. Só os arquivos registrados em `arquivos` pertencem à execução atual.

Uma parte bloqueada publica diagnóstico e não contribui com valores nos CSVs. Arquivos compartilhados conservam apenas as partes validadas; se não houver produtor válido, ficam só com cabeçalho. Se checkout estiver bloqueado, seu total é `null`, nunca zero. Se todas as partes estiverem bloqueadas, os seis CSVs contêm só cabeçalhos. Na falha de escrita, o marcador de publicação permanece bloqueado para a execução inteira, pois não é seguro declarar um conjunto de arquivos parcialmente substituído como publicado. Arquivos externos ou modificados pelo usuário nunca são sobrescritos/removidos: o comando falha e pede outra pasta de saída. Não use a pasta das entradas como saída. Outros arquivos presentes em `saida/` não fazem parte desta entrega.

## Dependências e isolamento de A1/A2

- CHECKOUT e PENDENCIAS_CHECKOUT usam Orbe, taxas e regras, mas têm validações independentes. Uma falha no rastro de comissões pode preservar as pendências já identificadas e validadas, e vice-versa.
- DIVERGENCIAS_CHECKOUT e DEVOLUCAO_CASA usam as contribuições contratuais resolvidas, Orbe, taxas e regras. Cada parte tem validação e rastro próprios; não dependem da agregação válida de comissões. Campo aplicado inválido afeta divergências; cobrado inválido afeta devolução. Valor desconhecido permanece vazio e provisório.
- Remessas declara Ponte + regras; divergências de remessa também declara taxas. Notas declaram dependência da respectiva comissão. Cada banco declara seu extrato + plano de contas + regras, sem depender do outro banco.
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

O auditor conserva `--esperar` como expectativa do checkout e aceita `--esperar-fechamento` para o agregado do alvo. Ele confere cabeçalhos e domínios, hashes das fontes/saídas, IDs de todas as linhas Orbe, destino único em rastro ou pendência, contagens, datas/competência, soma exata por comissão e pendência com valor conhecido, seis cabeçalhos oficiais em ordem e preservação das decisões pendentes. Em A2, também confere fórmula das divergências pelas fontes, contestação líquida, recorte da devolução, valores efetivamente cobrados e reconciliação por natureza, sem importar o motor. Os testes de regras verificam a seleção contratual.

Para determinismo, rode o mesmo comando em duas pastas de saída novas (por exemplo, `saida-a` e `saida-b`) e compare os bytes dos seis CSVs e `manifesto.json`. O teste `test_execucao_instalada_fora_da_raiz_sem_chaves_e_repeticao` também verifica repetição sem depender do diretório do código. Os demais testes de aceite exercitam outro mês sintético, modalidade desconhecida, 13x, EC sem cadastro, fonte ausente, layout inválido, soma/referência adulterada e publicação interrompida.

Os testes de subprocesso exigem o pacote instalado pelo comando de instalação. Nenhum dado do `Context/`, do `.env` ou de serviços externos é necessário. O verificador retorna `0` quando o artefato tem a situação esperada e é coerente; `1` quando detecta inconsistência. Aceite técnico não confirma o contrato da Atlas, não responde à pergunta financeira de D-10 e não valida funcionalidades futuras do alvo. D-02 (spread 0,01 p.p. = fração 0,0001) e D-04 (Aurora L9 físico) continuam documentadas para a implementação futura, sem leitor ou motor de remessas/extratos nesta entrega.

## Estrutura

`src/tarvo/` separa execução, modelos, leitores, cadastro, cálculo, validação e exportação. `ResultadoParte` em `modelos.py` contém o contrato interno; `partes.py` declara dependências e isola validações; `contratos.py` reúne os layouts usados por coordenação, validação e exportação, sem duplicar definições. `regras.toml` contém a configuração desta fatia e decisões pendentes. `docs/FORMATO_SAIDA.md` conserva o contrato do desafio. `HIPOTESES.md` registra limites e decisões. `PROMPTS/` registra o uso de IA.

A proposta de expansão está em [docs/EVOLUCAO_ALVO.md](docs/EVOLUCAO_ALVO.md), com A1/A2 implementadas e A3–A7 exclusivamente como planejamento. Nenhuma etapa futura é iniciada por executar o comando atual.
