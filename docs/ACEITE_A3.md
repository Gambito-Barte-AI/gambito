# Aceite A3 — Ponte de ponta a ponta

A3 implementada por autorização do usuário em 17/10/2026. Preservados o mínimo, o isolamento de A1 e a RN-64 corrigida. A4/notas e etapas seguintes não iniciadas; nenhuma dependência instalada, integração externa, commit ou alteração de branch feita pelo agente.

## Implementação e regras

- `leitores/ponte.py`: lê e-mails locais e anexos XLSX em memória, identifica cabeçalho por conteúdo, preserva Nº Operação, arquivo/anexo/aba e linha física. Não depende do nome mensal nem grava anexos fornecidos pelo e-mail. Rodapés conhecidos são reconhecidos; linhas inválidas têm diagnóstico e destino, com valor desconhecido vazio. Arquivo rejeitado não é apresentado como processado.
- `leitores/taxas.py`: leitura de contratos de remessa independente do cadastro de checkout. Blank/padrão usa spread padrão configurado; vigências e taxas inválidas não são estimadas. Mundo Aberto tem início de spread confirmado desde julho, registrado com fonte no TOML; não aplicar retroativamente sem contrato.
- `remessas.py`: participação pelo Spread R$ realizado, arredondada HALF_UP por operação. Liquidação em outro mês e ressalva aprovada não excluem participação. A comparação usa Spread % − contratado, PTAX e valor ME pelo valor cheio, sem descontar a participação. D-02: tolerância inclusiva de 0,01 p.p. = fração 0,0001. D-05 mantém o critério percentual da Mundo Aberto.
- RN-34: mesma operação calcula uma vez, preservando diagnóstico da ocorrência repetida. Conteúdo financeiro conflitante, status incompatível ou ocorrência ilegível com o mesmo número deixa as ocorrências pendentes; não escolher valor silenciosamente.
- RN-35/D-11: negativo irregular fica fora da comissão e das divergências normais. Principal e rastro = Spread R$ reportado − spread contratado × PTAX × ME. Extras `valor_reportado_brl` e `valor_solicitado_brl` distinguem os valores, com o sinal preservado. Sem dados suficientes, pedido vazio, sem zero ou reconstrução por Spread %.
- RN-37/D-10: ajuste com número próprio é reconhecido antes das regras de negativo irregular e repetição. Contribuição = participação × Spread R$ negativo, uma vez. `ref_original` e `ref_evento_original` apontam à operação anterior; arquivo histórico ausente fica vazio. Competência pelo novo relatório, ou seleção explícita quando não declarada; sem ambos, contratação da nova linha conforme premissa registrada em HIPOTESES. A operação original não é relançada.
- **D-10 continua pendente de confirmação financeira:** os 50% são decisão existente do time, explicitada na configuração, no manifesto e em uma pendência por ajuste. O exemplo real não tem ajuste; os testes sintéticos verificam inclusive o mês posterior e o arredondamento negativo. Nenhuma nota é calculada nesta etapa.
- RN-39/RN-40: acompanhamento do TED usa a participação calculada para conferência, sem prever recebimento/desconto; CNPJ novo preserva a participação realizada e gera pendência comercial. Planilha indisponível não significa cadastro inexistente para todos.

## Arquitetura, contratos e isolamento

Mantidos monólito modular, Decimal, CLI, TOML e processamento em memória. Acrescentados os modelos OperacaoPonte/ContratoRemessa, o leitor e o módulo financeiro; nenhuma infraestrutura ou camada genérica nova.

REMESSAS depende de Ponte + regras. DIVERGENCIAS_REMESSA depende também da fonte `contratos_remessa`, lida do mesmo XLSX com estado independente do checkout. Validadores e rastros das partes permanecem separados. Falha do rastro da comissão não bloqueia divergência válida nem checkout. Sem planilha, a comissão regular continua disponível; havendo negativo sem contrato, seu pedido fica desconhecido e REMESSAS provisório, preservando a comissão conhecida. A comparação contratual fica bloqueada.

Manifesto versão 5, etapa ALVO_A3. Campos legados e cobertura global continuam exclusivos do checkout; o fechamento do alvo agrega todas as partes. As seis saídas oficiais continuam obrigatórias. Extras de A3 entram somente em `--escopo alvo`; o escopo padrão conserva as colunas e bytes dos seis CSVs do mínimo. Notas e classificados continuam apenas com cabeçalho e status bloqueado.

## Resultados conferidos nas fontes

| Verificação | Resultado |
| --- | --- |
| Ponte física | 233 linhas = 228 contribuições + 4 negativos irregulares + 1 ocorrência duplicada; 232 números únicos |
| Comissão Ponte | 14 lojistas; **R$ 39.543,45**; 50% de R$ 262,01 = R$ 131,01 por linha |
| Divergências Ponte | 23 operações da Mundo Aberto; **R$ 1.418,85**, pelo percentual e valor cheio |
| Negativos irregulares | Quatro pedidos com valores reportado/solicitado identificados; nenhum entra como comissão |
| Duplicata | PC-0926-0162 uma vez na comissão; ocorrência adicional rastreada em pendência de correção |
| Acompanhamento | 14 pendências por lojista para conferir repasse efetivo; não são recebimentos estimados |
| Checkout | 1.957 = 1.900 contribuições + 57 pendências Atlas; 21 lojistas, **R$ 203.735,34** |
| RN-64 | **R$ 15.396,77** líquidos em 118 origens; estorno isento de R$ 9,08 abatido; estorno de agosto preservado somente na comissão pela taxa original |
| CSVs no escopo alvo | 35 comissões, 115 divergências, 80 pendências e 2.766 rastros; notas/classificados com zero linhas |
| Mínimo | Retorno 0; seis CSVs idênticos em bytes a `saida/alvo-a1/` |
| A2 corrigida | Todas as linhas/valores de checkout, divergências, pendências e rastro preservados contra `saida/alvo-a2-rn64/`, projetando as colunas anteriores |
| Alvo | Retorno 2, PROVISORIO: A1/A2/A3 disponíveis, quatro partes futuras bloqueadas (notas e bancos) |
| Repetição | Seis CSVs e manifesto idênticos em duas pastas; hashes das fontes antes/depois iguais |

Os valores do exemplo foram usados para conferência, nunca como constantes no motor. Totais de comissão, diferenças, devolução e acompanhamento são naturezas distintas: não somar todos os valores de pendências/rastro como receita.

| Nº Operação | Reportado (R$) | Principal/solicitado (R$) |
| --- | ---: | ---: |
| PC-0926-0210 | −687,52 | −1.351,87 |
| PC-0926-0326 | −509,22 | −1.001,29 |
| PC-0926-0491 | −292,28 | −574,91 |
| PC-0926-0545 | −345,03 | −637,91 |

## Testes e reprodução

**159 testes passaram**, incluindo os 132 anteriores e 27 de A3. Cobrem MIME/XLSX, nomes livres, meia unidade de centavo positiva/negativa, tolerância abaixo/igual/acima, realizado versus percentual, duplicatas iguais/conflitantes/ilegíveis, negativo com dois valores, ajustes e D-10, competência do novo relatório, ressalva, CNPJ novo, ausência de fontes, planilha corrompida, campos opcionais inválidos, bloqueio isolado de rastro e adulteração/omissão detectadas pelo auditor. Não exigem o data pack ignorado pelo Git.

O auditor A3 é independente do motor e usa somente biblioteca padrão para MIME e XML/ZIP do XLSX. Verifica hashes dos e-mails/anexos/contratos, linhas físicas, competência, participação por operação, pedido do negativo, referência de contrato, percentuais/tolerância, somas por destino e cobertura das 233 linhas. Não depende de totais declarados em rodapés. Testes do motor cobrem também resolução e rejeição das relações inválidas.

Matriz executada com cópias locais, sem alterar as fontes:

| Fonte removida | Checkout | Remessas | Divergências remessa |
| --- | --- | --- | --- |
| Ponte | COMPLETO | BLOQUEADO | BLOQUEADO |
| Planilha | BLOQUEADO | PROVISORIO, comissão disponível e pedidos negativos desconhecidos | BLOQUEADO |
| Orbe | BLOQUEADO | COMPLETO | COMPLETO |

Executar na raiz, com o ambiente já instalado:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida/alvo-a3 --regras regras.toml --escopo alvo
.\.venv\Scripts\python.exe tests/validar_saida.py --dados Tarvo_Data_Pack_set2026 --saida saida/alvo-a3 --regras regras.toml --esperar COMPLETO --esperar-fechamento PROVISORIO
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Primeiro comando retorna 2 enquanto o alvo tiver etapas futuras; auditor retorna 0 ao confirmar esse estado esperado. Em macOS/Linux, usar `.venv/bin/python`. Nesta sessão foi executado Windows/Python 3.12.10, com ambiente existente, fora da raiz, sem PYTHONPATH/PYTHONHOME, chaves ou site-packages do usuário. macOS/Linux não foram executados.

Evidências atuais: `saida/alvo-a3/manifesto.json` e seis CSVs; `.tmp/aceite-a3/resultado.json`, logs, auditorias, repetição e matriz; `.tmp/testes-a3.log`. Evidências A1/A2 e fontes originais preservadas. `git diff --check` sem erros.

## Pendências e limite

D-10 e o contrato da Atlas continuam explícitos. Datas sem evidência continuam NAO_INFORMADO. A4 fará notas e tratamento fiscal dos saldos; nenhuma nota, repasse, pagamento ou contestação externa foi executada. Bancos e extras permanecem futuros. Aceite de A3 não é aceite integral do alvo.
