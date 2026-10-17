# Gambito — Entrega 4: aceite do mínimo

Checkout Tarvo com vendas, estornos, antecipações e reversões: lê Orbe e taxas, calcula **eventos com contrato e referências verificáveis**, valida o rastro e publica dois CSVs. Os eventos sem contrato confirmado, como a Atlas, ficam pendentes; não são estimados. Nenhuma funcionalidade do alvo foi implementada.

## Instalação

Python 3.11 ou superior. Na raiz do repositório, em PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

A única dependência de execução é `openpyxl` (XLSX). Não há servidor, banco, acesso a API ou chave obrigatória. `.env.example` fica reservado à eventual IA, fora desta entrega. Nenhuma variável desse arquivo é consumida agora.

## Executar

Coloque os arquivos originais do mês em uma pasta. Não os edite antes de executar:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados data/raw --saida saida --regras regras.toml
```

Para o data pack local, se disponível:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida --regras regras.toml
```

O data pack e `Context/` não estão versionados. A banca fornece os arquivos originais. O leitor reconhece **todos os CSVs Orbe pelo cabeçalho**, sem nomes fixos, e um único XLSX de taxas. Relatório e ajustes são reunidos antes das referências. A aba vigente é configurada em `regras.toml`; várias planilhas candidatas continuam bloqueando essa dependência.

A competência vem de `data_movimento`, nunca da data da venda original. Com vários meses, escolha explicitamente, por exemplo `--competencia 2026-09`. Linhas válidas de outros meses ficam fora do cálculo e são contadas em `ingestao.fora_competencia`. Linhas com data inválida permanecem pendentes, pois não é seguro atribuir um mês. Uma reversão cujo original esteja fora do recorte exige revisão; não é reconstruída por estimativa.

A pasta completa com `01` e `06` é suportada. Também é possível executar somente relatório e taxas. As evidências antigas em `saida/entrega2/`, `entrega3/` e `entrega4/` foram preservadas; representam a versão anterior. O aceite atualizado está em `docs/ACEITE_MINIMO.md` e `saida/aceite-multiorbe/`.

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
- A isenção confirmada da Casa usa a data da venda e o intervalo configurado. Contribuições isentas são zero com rastro. Antes/depois do intervalo, aplica-se o contrato vigente, sem estender a isenção. A devolução pelo cobrado foi confirmada na RN-64 (antiga D-08), mas seu cálculo pertence ao alvo e continua não implementado. R$ 15.396,77 é referência de conferência, nunca constante no código.
- A isenção também vale para a antecipação no seu período. A reversão de antecipação isenta permanece zero, mesmo após o fim da isenção. Estornos anteriores à isenção usam a condição anterior, com saldo negativo permitido nas comissões.
- D-10 continua fora do escopo. Saldos zero/negativos são preservados nas comissões; nenhuma nota, transferência de saldo ou devolução é gerada.
- Remessas, divergências, notas, extratos, devoluções, IA e `pendencias.csv` não são implementados.

## Resultados e fechamento parcial

`saida/` recebe:

- `comissoes_por_lojista.csv`: somente contribuições calculadas, agrupadas por CNPJ; layout obrigatório.
- `rastro.csv`: uma contribuição assinada por evento calculado; soma exata por `id_saida`, incluindo zero e negativos. Colunas adicionais registram contrato, taxa, faixa, regra, vínculo, tipo, data base contratual e referência original. O vínculo ao original é metadado, sem repetir seu valor e duplicar a soma. Arquivo histórico não disponível permanece vazio.
- `manifesto.json`: situação, competência, hashes de cada fonte e saída, cobertura física, duplicidades, avisos, limitações, decisões documentadas/pendentes e todas as pendências por referência, tipo, categoria, próximo passo e responsável. O valor bruto de uma pendência não representa comissão nem valor a cobrar.

O terminal exibe resumo, decisões e pendências com motivo e responsável; `proximo_passo` fica no manifesto. O CSV de pendências permanece reservado ao alvo, preservando o contrato oficial. IDs e ordenação são estáveis; mesma entrada e regras geram os mesmos arquivos.

| Situação | Significado | Código de saída |
| --- | --- | --- |
| `COMPLETO` | Fontes válidas e rastro reconciliado. Pendências de negócio, como Atlas, continuam explícitas. Não significa alvo concluído. | `0` |
| `PROVISORIO` | Há pendências de dados ou aviso de fonte adicional inválida; fecha somente o subconjunto validado. | `2` |
| `BLOQUEADO` | Dependência inválida/ausente, competência ambígua ou rastro quebrado; CSVs apenas com cabeçalhos, total indisponível. | `1` |

Ausência de fontes do alvo não bloqueia checkout. Orbe, taxas e regras são inspecionadas separadamente. Se todos os candidatos Orbe forem inválidos, bloqueia; se houver fontes válidas e outra identificada com layout inválido, fecha provisoriamente as válidas e registra o arquivo rejeitado, hash e motivo. A cobertura de linhas refere-se aos arquivos lidos com sucesso; linhas de fonte estruturalmente inválida não são contadas como processadas.

IDs idênticos entre arquivos são calculados uma vez, com ocorrência repetida em pendência e origem canônica pela ordenação dos arquivos. IDs com conteúdo conflitante deixam **todas** as ocorrências pendentes, assim como eventos que os referenciam. Não se escolhe um valor financeiro entre conflitos. ID ausente ou repetido dentro do mesmo arquivo continua sendo falha estrutural da fonte, para não tornar ambígua a referência oficial `arquivo + id_transacao`.

**Consulte sempre `manifesto.json` e verifique seus hashes antes de consumir CSVs.** Ele é publicado por último como marcador de validade. Se a publicação for interrompida, o marcador permanece bloqueado. Só os arquivos registrados em `arquivos` pertencem à execução atual.

Uma execução bloqueada publica diagnóstico e substitui os dois CSVs próprios, com hash intacto, por arquivos apenas com cabeçalhos. O manifesto marca `BLOQUEADO`, `rastro_validado=false` e total `null`; isso não é comissão zero. Arquivos externos ou modificados pelo usuário nunca são sobrescritos/removidos: o comando falha e pede outra pasta de saída. Não use a pasta das entradas como saída. Outros arquivos presentes em `saida/` não fazem parte desta entrega.

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

Código `0` é esperado para o case com as pendências comerciais da Atlas e fontes válidas. Código `2` indica dados não reconhecidos ou aviso de fonte rejeitada, com subconjunto validado. Código `1` indica bloqueio ou erro. Não trate qualquer saída diferente de zero como fechamento concluído.

O verificador independente usa apenas a biblioteca padrão, sem importar o motor:

```powershell
.\.venv\Scripts\python.exe tests/validar_saida.py --dados data/raw --saida saida --regras regras.toml --esperar COMPLETO
```

Ele confere cabeçalhos e domínios, hashes das fontes/saídas, IDs de todas as linhas Orbe, destino único em rastro ou pendência, contagens, datas/competência, soma exata por comissão e preservação das decisões pendentes. Ele audita os artefatos; os testes de regras verificam as fórmulas e a seleção contratual.

Para determinismo, rode o mesmo comando em duas pastas de saída novas (por exemplo, `saida-a` e `saida-b`) e compare os bytes dos dois CSVs e `manifesto.json`. O teste `test_execucao_instalada_fora_da_raiz_sem_chaves_e_repeticao` também verifica repetição sem depender do diretório do código. Os demais testes de aceite exercitam outro mês sintético, modalidade desconhecida, 13x, EC sem cadastro, fonte ausente, layout inválido, soma/referência adulterada e publicação interrompida.

Os testes de subprocesso exigem o pacote instalado pelo comando de instalação. Nenhum dado do `Context/`, do `.env` ou de serviços externos é necessário. O verificador retorna `0` quando o artefato tem a situação esperada e é coerente; `1` quando detecta inconsistência. Aceite técnico não confirma o contrato da Atlas, não responde à pergunta financeira de D-10 e não valida funcionalidades do alvo. D-02 (spread 0,01 p.p. = fração 0,0001) e D-04 (Aurora L9 físico) continuam documentadas para a implementação futura, sem leitor ou motor de remessas/extratos nesta entrega.

## Estrutura

`src/tarvo/` separa execução, modelos, leitores, cadastro, cálculo, validação e exportação. `regras.toml` contém a configuração desta fatia e decisões pendentes. `docs/FORMATO_SAIDA.md` conserva o contrato do desafio. `HIPOTESES.md` registra limites e decisões. `PROMPTS/` registra o uso de IA.
