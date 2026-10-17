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

O data pack e `Context/` não estão versionados. A banca precisa fornecer os arquivos originais. O comando não depende desses nomes: descobre um CSV com `id_transacao` e um único XLSX; a aba vigente é configurada em `regras.toml`. Mais de um candidato bloqueia a fonte, sem escolher arbitrariamente. A competência é obtida de `data_movimento`; arquivos vazios ou com múltiplos meses ficam bloqueados nesta entrega.

Na validação da Entrega 2, a pasta local recebeu também `06_orbe_ajustes_tardios_set2026.csv`. Com dois relatórios Orbe, o comando acima gera corretamente `BLOQUEADO`; não há fusão ou seleção automática. Para reproduzir o recorte aprovado, coloque em `data/raw/` somente o relatório Orbe original e a planilha de taxas, copiados sem alteração, e use o primeiro comando. O relatório adicional permanece intacto e seu processamento não foi incorporado. As evidências anteriores foram preservadas em `saida/entrega2/` e `saida/entrega3/`. A Entrega 4 valida explicitamente o recorte de duas entradas; não significa aceite dos ajustes tardios ou do alvo.

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
- A Atlas é identificada pela aba antiga e vínculo documentado, mas o bloqueio comercial mantém seus eventos pendentes. Nenhuma taxa antiga é importada. D-07 não foi ratificada: a ausência de comissão calculada não decide a representação final fora/zerada.
- A isenção confirmada da Casa usa a data da venda e o intervalo configurado. Contribuições isentas são zero com rastro. Antes/depois do intervalo, aplica-se o contrato vigente, sem estender a isenção. Devolução ao lojista não é calculada e D-08 permanece pendente.
- A isenção também vale para a antecipação no seu período. A reversão de antecipação isenta permanece zero, mesmo após o fim da isenção. Estornos anteriores à isenção usam a condição anterior, com saldo negativo permitido nas comissões.
- D-10 continua fora do escopo. Saldos zero/negativos são preservados nas comissões; nenhuma nota, transferência de saldo ou devolução é gerada.
- Remessas, divergências, notas, extratos, devoluções, IA e `pendencias.csv` não são implementados.

## Resultados e fechamento parcial

`saida/` recebe:

- `comissoes_por_lojista.csv`: somente contribuições calculadas, agrupadas por CNPJ; layout obrigatório.
- `rastro.csv`: uma contribuição assinada por evento calculado; soma exata por `id_saida`, incluindo zero e negativos. Colunas adicionais registram contrato, taxa, faixa, regra, vínculo, tipo, data base contratual e referência original. O vínculo ao original é metadado, sem repetir seu valor e duplicar a soma. Arquivo histórico não disponível permanece vazio.
- `manifesto.json`: situação, competência, hashes das fontes e saídas, cobertura, limitações, decisões pendentes e todas as pendências por referência. O valor bruto de uma pendência não representa comissão nem valor a cobrar.

O terminal exibe resumo e pendências com motivo e responsável. IDs e ordenação são estáveis; mesma entrada e regras geram os mesmos arquivos.

| Situação | Significado | Código de saída |
| --- | --- | --- |
| `COMPLETO` | Todas as linhas de checkout calculadas, sem pendências. Não significa alvo concluído. | `0` |
| `PROVISORIO` | CSVs válidos somente para contribuições calculadas; demais linhas identificadas como pendências. | `2` |
| `BLOQUEADO` | Dependência inválida/ausente, competência ambígua ou falha de validação; sem CSVs atuais. | `1` |

Ausência de fontes do alvo não bloqueia checkout. As duas fontes desta entrega são inspecionadas independentemente, mas checkout precisa de ambas e das regras. Linha com dado inválido e ID conhecido pode ficar pendente; ID ausente/duplicado ou erro estrutural bloqueia a fonte. Não se infere como deduplicar Orbe.

**Consulte sempre `manifesto.json` e verifique seus hashes antes de consumir CSVs.** Ele é publicado por último como marcador de validade. Se a publicação for interrompida, o marcador permanece bloqueado. Só os arquivos registrados em `arquivos` pertencem à execução atual.

Uma execução bloqueada publica diagnóstico e remove apenas os dois CSVs anteriores gerados por este produtor e cujo hash permanece intacto. Arquivos externos ou modificados pelo usuário nunca são sobrescritos/removidos: o comando falha e pede outra pasta de saída. Não use a pasta das entradas como saída. Outros arquivos presentes em `saida/` não fazem parte desta entrega.

## Verificação

Os testes usam `unittest` da biblioteca padrão, sem dependência de desenvolvimento adicional:

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src')
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

As amostras são sintéticas e criadas em diretório temporário: arredondamento positivo/negativo, rastro, faixas 2/6/7/12/13x, vigências, conflitos de identidade, histórico sem taxas antigas, estornos de mês anterior e anteriores à isenção, antecipação pela taxa própria, anulação exclusiva da antecipação, ordem das linhas, referências inconsistentes, reversões duplicadas, fontes faltantes, determinismo e proteção das saídas. Totais do case não são usados como regras.

## Configuração e decisões pendentes

`regras.toml` contém os três ECs complementares confirmados, vínculo da Atlas, bloqueio por falta de confirmação comercial, período de isenção da Casa e observações esclarecidas. Valores, datas e identificadores do caso ficam nessa configuração, nunca como constantes no código de cálculo. Cada registro tem fonte e descrição da aprovação conhecida ou da interpretação técnica; datas/pessoas não informadas não são inventadas.

D-07 (representação da Atlas), D-08 (devolução da Casa) e D-10 (semântica do ajuste Ponte) continuam no manifesto e em `HIPOTESES.md`. Aprovar esta entrega não ratifica essas decisões financeiras. Não é preciso API nem nova dependência para a Entrega 4.

## Aceite independente e reprodução do zero

Em uma cópia nova do projeto, repita a instalação acima e coloque somente Orbe original e taxas em `data/raw/`. Execute sem chaves e sem configurar `PYTHONPATH`:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados data/raw --saida saida --regras regras.toml
$codigo = $LASTEXITCODE
```

Código `2` é esperado quando há pendências documentadas (como Atlas). O processo gerou resultados provisórios, não falhou na validação financeira. Código `1` indica bloqueio ou erro. Não trate qualquer saída diferente de zero como fechamento concluído.

O verificador independente usa apenas a biblioteca padrão, sem importar o motor:

```powershell
.\.venv\Scripts\python.exe tests/validar_saida.py --dados data/raw --saida saida --regras regras.toml --esperar PROVISORIO
```

Ele confere cabeçalhos e domínios, hashes das fontes/saídas, IDs de todas as linhas Orbe, destino único em rastro ou pendência, contagens, datas/competência, soma exata por comissão e preservação das decisões pendentes. Ele audita os artefatos; os testes de regras verificam as fórmulas e a seleção contratual.

Para determinismo, rode o mesmo comando em duas pastas de saída novas (por exemplo, `saida-a` e `saida-b`) e compare os bytes dos dois CSVs e `manifesto.json`. O teste `test_execucao_instalada_fora_da_raiz_sem_chaves_e_repeticao` também verifica repetição sem depender do diretório do código. Os demais testes de aceite exercitam outro mês sintético, modalidade desconhecida, 13x, EC sem cadastro, fonte ausente, layout inválido, soma/referência adulterada e publicação interrompida.

Os testes de subprocesso exigem o pacote instalado pelo comando de instalação. Nenhum dado do `Context/`, do `.env` ou de serviços externos é necessário. O verificador retorna `0` quando o artefato tem a situação esperada e é coerente; `1` quando detecta inconsistência. Aceite técnico do mínimo não encerra D-07/D-08/D-10 nem valida relatórios não processados.

## Estrutura

`src/tarvo/` separa execução, modelos, leitores, cadastro, cálculo, validação e exportação. `regras.toml` contém a configuração desta fatia e decisões pendentes. `docs/FORMATO_SAIDA.md` conserva o contrato do desafio. `HIPOTESES.md` registra limites e decisões. `PROMPTS/` registra o uso de IA.
