# Frente 2 — E1: rascunhos de contestação

E1 autorizada pelo usuário e implementada conforme [E0](EXTRA_E0.md). **E4/assistência por IA não foi iniciada.** Nenhuma nova regra financeira, dependência, branch, commit ou integração externa. Alterações preexistentes de E0 preservadas. Histórico integral de IA continua adiado pelo usuário; este documento descreve o produto e os testes, não substitui o histórico das sessões.

## Interface entregue

```python
from tarvo.extras.contestacoes import construir_contestacoes

pacote = construir_contestacoes(visao, {})
```

Função sem I/O, chamada de rede ou mutação das entradas. Recebe a projeção versão 1 definida em E0: competência, fontes/hashes, estados de partes e linhas publicáveis dos seis relatórios. Cada estado deve ter `situacao`, `validado` e `motivos`; ao projetar um manifesto, `validado` corresponde a `rastro_validado`. Os relatórios devem vir de uma base previamente auditada, nunca de CSVs arbitrários sem verificação de hashes/validade. A função faz reconciliação adicional dos grupos utilizados, sem substituir o auditor financeiro do alvo.

**Configuração E1: `{}`.** Não há taxa, texto livre obrigatório ou parâmetro financeiro adicional. Configuração desconhecida é rejeitada explicitamente; não foi acrescentada seção ao TOML central.

Retorna `versao`, `recurso=contestacoes`, `situacao`, `motivos`, `registros`. Estados: COMPLETO, PARCIAL ou BLOQUEADO. Sem casos elegíveis e com fontes válidas, COMPLETO com registros vazios. Estado do extra não altera estado/retorno do alvo.

Cada registro tem ID estável `CONTESTACAO:<contraparte>:<competencia>`, contraparte, origens, IDs das pendências/divergências e texto Markdown. Campo adicional `grupos` preserva natureza, valores e operações de cada pendência para conferência. No máximo um registro por contraparte/competência. Todos os valores serializados usam ponto decimal e duas casas; percentuais preservam a precisão original. Ordenação determinística; caracteres de estrutura Markdown e quebras de linha em identificadores são escapados no texto.

## Conteúdo e integridade

- **Orbe:** somente `CONTESTACAO_TAXA_ORBE` de DIVERGENCIAS_CHECKOUT validada. Diferença líquida por CNPJ, operações de venda/estorno assinadas, taxas e IDs de divergência. O total soma as pendências agregadas uma vez; não soma seus detalhes outra vez.
- **Ponte / contrato:** `CONTESTACAO_SPREAD_CONTRATUAL` de DIVERGENCIAS_REMESSA validada, pelo valor cheio já calculado no alvo, sem recalcular spread ou participação.
- **Ponte / negativo:** `CONTESTACAO_SPREAD_NEGATIVO` de REMESSAS validada. Seção própria RN-35/D-11, com valor reportado e solicitado identificados e sinais preservados. Não é divergência de taxa nem receita e não é compensada com o total da seção contratual.
- **Pedido desconhecido:** conserva o reportado conhecido e a operação, informa pedido NÃO INFORMADO e marca PARCIAL; sem inventar zero ou rastro monetário. Se houver outros pedidos conhecidos, o texto os identifica como subtotal conhecido.
- **Exclusões:** Casa/concessões, Atlas sem contrato, cadastro, acompanhamento de TED e ajuste D-10 não viram cobrança contratual. D-10 continua explicitamente pendente no rodapé; não há aplicação de participação dentro do gerador.
- Diferenças negativas e saldo zero continuam assinados e exigem decisão caso a caso; não há liberação automática de cobrança, pagamento ou envio.

Para cada grupo monetário, soma do rastro deve ser igual ao valor principal. Nas divergências contratuais, exige correspondência única por negócio/arquivo/referência, mesmo CNPJ, mesmo valor da divergência e de seu próprio rastro. D-11 confere principal versus solicitado. Rejeita duplicidade de ID, origem repetida ou operação usada por mais de uma pendência da contraparte. Valores inválidos, natureza incompatível e percentuais inválidos não são recalculados nem corrigidos.

Parte bloqueada/não validada não fornece valores. Parte provisória ou pedido desconhecido gera texto limitado, sem aparentar contestação definitiva. Uma inconsistência em uma contraparte rejeita seu rascunho, preservando a outra; erros de versão/esquema/IDs globais/hashes da projeção rejeitam o pacote. Motivos ficam explícitos.

Origens preservam arquivo, referência e linha física quando disponível. Se o rastro Orbe não informa linha física para uma operação, `linha=null` e o texto usa o identificador oficial, sem inventar linha nem reler o original. Quando disponível, inclui SHA-256 e `arquivo_hash`; em origem `email::anexo::aba`, o hash do e-mail é identificado como tal, não atribuído falsamente à aba. O vínculo ao rastro e aos IDs oficiais permanece íntegro.

## Limite de integração

Conforme a divisão de E0, E1 entrega **o módulo puro e seu aceite**, não altera CLI, exportador, contratos CSV, configuração ou auditores centrais. A ligação única e o manifesto/publicação de extras pertencem à frente 1. `--extras` ainda não está disponível. Nenhum `__init__.py` compartilhado, coordenador vazio ou código de E2/E3/E4 foi criado.

Na integração futura, a frente 1 monta a projeção validada e grava o `texto` retornado nos caminhos contratados `extras/contestacao_orbe.md` e `extras/contestacao_ponte.md`, com o manifesto próprio de extras. Não recalcular o fechamento dentro do módulo nem publicar rascunhos em uma base inválida. A API exige os dois estados independentes da Ponte: REMESSAS e DIVERGENCIAS_REMESSA.

## Validação e reprodução

Testes permanentes em `tests/test_extra_contestacoes.py`, com dados sintéticos e fechamento de outubro/2032. Exercitam sinais/estornos, separação de naturezas, D-11 desconhecido, exclusões/D-10, parcial/bloqueado por fonte, IDs/hash/esquema inválidos, rastros adulterados, duplicação de cobrança, ordenação/determinismo, valores inválidos, projeção somente leitura e preservação dos arquivos de origem/saída. Não dependem do pack oficial.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_extra_contestacoes.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Em macOS/Linux, usar `.venv/bin/python`. Em Windows restrito, usar TEMP/TMP graváveis conforme README. A verificação ponta a ponta existente do alvo continua sendo o auditor `tests/validar_saida.py`; testes de E1 não equivalem ao aceite da futura CLI de extras.

Revisão local do pack já validado: dois registros, **Orbe com 92 operações em dois grupos**, **Ponte com 27 operações em cinco grupos** (23 divergências contratuais e quatro negativos). Esses números são evidências, nunca condições do motor. Rascunhos em `.tmp/extra-e1/contestacao_orbe.md`, `.tmp/extra-e1/contestacao_ponte.md`, com `pacote.json` para inspeção e `testes.log` da suíte. Nenhuma saída oficial foi sobrescrita.

Validação final em Windows/Python 3.12.10: **254 testes aprovados em 62,230 s**, sendo 233 anteriores e 21 de E1. Auditor independente do alvo permaneceu COMPLETO, com fontes/rastros/hashes e decisões preservados. SHA-256 dos 156 arquivos preexistentes conferidos (motor, configurações, documentos oficiais, fontes e saídas) inalterado; somente o novo módulo foi acrescentado nessa área. Nenhuma alteração financeira ou nova dependência.
