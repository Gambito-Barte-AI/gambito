# Aceite atualizado do mínimo — P0/P1 e ajustes tardios

**Resultado: aprovado tecnicamente com relatório e ajustes tardios, mantendo as pendências comerciais e a arquitetura existente.** Situação `COMPLETO` conforme D-13, sem confundir pendência de contrato da Atlas com erro de processamento. Nenhuma funcionalidade do alvo foi implementada.

## Reprodução do zero

Em 17/10/2026 foi criada `.tmp/aceite-multiorbe/` com fonte, testes, configuração e documentação atuais, sem `.git`, ambiente virtual anterior ou Context. O data pack foi copiado byte a byte, incluindo os dois CSVs Orbe. Os arquivos de remessas/bancos presentes na pasta não se tornam dependências do checkout.

Um venv novo foi criado com Python **3.12.10**, seguido de instalação editável do projeto. O temporário do sandbox foi direcionado ao workspace. A primeira tentativa de instalação não tinha acesso à rede; a repetição autorizada instalou somente as dependências já declaradas: **openpyxl 3.1.5** e **et-xmlfile 2.0.0**. `pip check` passou. Sem novas dependências de produto.

Os comandos foram executados a partir da cópia nova, sem `PYTHONPATH`, `PYTHONHOME`, site-packages do usuário ou chaves de API. O caminho importado do pacote aponta ao `src/` da cópia. **94 testes passaram** nesse ambiente. Os bytes do código, testes e regras foram comparados ao workspace; hashes em `aceite.json` identificam o que foi validado.

## Resultado conferido pelo auditor independente

| Verificação | Evidência |
| --- | --- |
| Competência derivada do movimento | 2026-09 |
| Cobertura física dos arquivos Orbe válidos | 1.957 linhas = 1.900 calculadas + 57 pendências comerciais; zero sem destino |
| Comissões de checkout | 21 lojistas; **R$ 203.735,34** |
| Ajustes tardios | 14 contribuições com origem no arquivo 06; 13 referências apontam ao arquivo 01 |
| Comparação com relatório original isolado | R$ 207.039,73 → R$ 203.735,34; 7 lojistas alterados; diferença −R$ 3.304,39 |
| Casa | Comissão −R$ 5,50, preservando estorno anterior à isenção; devolução não calculada |
| Atlas | Fora das comissões; 57 pendências com CNPJ, origem, próximo passo e cobrança efetiva Orbe somada em R$ 7.876,05, separada do bruto |
| Rastro | Uma contribuição assinada por evento calculado; reconciliação exata por `id_saida` |
| Formato | CSV UTF-8 com `;`, ponto decimal, datas ISO e colunas obrigatórias preservadas |
| Determinismo | Mesmos bytes dos dois CSVs e manifesto em duas pastas distintas |
| Tempos medidos | 0.8704 s e 1.3381 s, incluindo inicialização |
| Fontes | Hashes iguais aos originais antes/depois; nenhuma edição dos dados |

Os números acima são referências de conferência, não constantes do motor. Também foi auditado o recorte só com relatório original e taxas. `tests/validar_saida.py` usa apenas a biblioteca padrão, sem importar `tarvo`: verifica todos os candidatos Orbe, hashes, cobertura por arquivo/referência, linha física das pendências, contratos de saída, competência, vínculos, anulação de reversões e soma por comissão. Os testes financeiros continuam responsáveis pela seleção contratual e fórmulas.

## Casos de falha e regressão

- Arquivos com nomes livres, referência entre arquivos e reversão antes do original na ordem de leitura.
- Duplicata idêntica contada uma vez, com destino explícito para a ocorrência repetida; conflito de valores ou ocorrência inválida não libera comissão arbitrária nem referência dependente.
- Arquivo adicional com layout inválido deixa o subconjunto válido provisório, com aviso, hash e motivo. Mudança da coluna de ID também é detectada pelos demais campos da assinatura Orbe.
- Fonte necessária ausente, todas as fontes Orbe inválidas ou rastro quebrado: dois CSVs só com cabeçalhos, manifesto bloqueado e total `null`, sem transformar desconhecido em zero.
- Publicação interrompida mantém marcador inválido; arquivos externos/modificados continuam protegidos.
- Múltiplos meses exigem escolha; seleção por `--competencia` contabiliza separadamente os demais meses. Datas inválidas não são atribuídas silenciosamente a outro mês.
- Auditor rejeita CSV Orbe omitido, soma/referência adulterada e decisões omitidas; metadados de aprovação ausentes ou datas inválidas nas regras são rejeitados.

## Pendências e limites

**D-07** é decisão documentada do time: Atlas fora do arquivo de comissões. Seu contrato continua pendente para o Comercial. As 57 origens e valores cobrados ficam no manifesto; não se cria comissão fictícia no rastro dos valores calculados. **RN-64**, antiga D-08, confirmou a devolução da Casa pelo efetivamente cobrado, mas essa funcionalidade continua no alvo.

**D-10** permanece com resposta financeira pendente: o time decidiu usar 50% do Spread R$ negativo, porém ainda falta confirmar se a linha já vem como participação. Não há implementação de remessas. Datas de aprovação não documentadas das interpretações técnicas e decisões do time aparecem como `NAO_INFORMADO`, também no manifesto; não foram fabricadas.

A interpretação de RN-13 que permite estorno de mês anterior sem relatório histórico foi preservada e explicitada em `HIPOTESES.md`; referência do próprio mês ausente ou reversão sem original vira pendência. Duplicata dentro de um mesmo arquivo ainda invalida essa fonte, por ambiguidade de `arquivo + id_transacao`. Cobertura não inclui linhas de arquivo estruturalmente rejeitado, cujo motivo permanece explícito.

D-02 (tolerância de spread de 0,01 p.p. = 0,0001 em fração) e D-04 (Aurora com primeira transação física L9) permanecem requisitos para os módulos futuros. Não há remessas, divergências, notas, extratos, devoluções, IA, recuperação futura da Atlas ou `pendencias.csv` nesta etapa.

## Evidências e reprodução

`saida/aceite-multiorbe/` contém os CSVs, manifesto, `aceite.json`, log dos 94 testes, `pip-check.log`, logs das execuções e auditorias. A cópia nova mantém a repetição em `saida-b/` e o recorte original em `saida-original/`. Evidências anteriores não foram sobrescritas.

Siga o README para instalar e executar com a pasta completa. Para o case atual, o motor retorna `0` (`COMPLETO` com pendências comerciais); o auditor com `--esperar COMPLETO` também retorna `0`. As pastas de saída, dados, Context e PROMPTS continuam sob as escolhas existentes de `.gitignore`; presença local não implica versionamento. Nenhum commit, push ou alteração de branch.

---

# Registro histórico da Entrega 4, anterior aos ajustes P0/P1

O registro abaixo foi preservado para rastrear a entrega anterior. Seus critérios de um único Orbe, bloqueio sem CSVs e D-07/D-08 abertas foram substituídos pelo aceite acima.

# Aceite técnico do mínimo — Entrega 4

**Resultado: aprovado no recorte das duas entradas originais, com pendências financeiras explícitas.** Não é aprovação das decisões financeiras, dos ajustes tardios ou do alvo.

## Ambiente e execução do zero

Em 17/10/2026 foi criada uma cópia dos arquivos atuais do workspace em `.tmp/aceite-minimo/`, sem `.git`, ambiente virtual anterior, Context, dados pré-processados ou serviços externos. A cópia incluiu as alterações ainda não commitadas das Entregas 3 e 4; não foi um clone do último commit.

Foi criado um venv novo com `python -m venv .venv`, seguido de `pip install -e .`, conforme README. O acesso à rede foi usado somente para instalar as dependências declaradas. O temporário do sandbox foi direcionado ao workspace, sem reutilizar pacotes instalados no ambiente antigo.

| Item | Evidência |
| --- | --- |
| Plataforma executada | Windows, Python 3.12.10 |
| Dependências de execução | openpyxl 3.1.5 e et-xmlfile 2.0.0 |
| Pacote | tarvo-gambito 0.1.0, importado do `src/` da cópia limpa |
| Isolamento | Sem PYTHONPATH/PYTHONHOME, sem site-packages do usuário, sem chaves de API |
| Instalação | Venv novo e instalação editável concluídos; `pip check` sem inconsistências |
| Testes na cópia limpa | 81 testes passaram; log preservado |
| Tempo do comando | 1,1469 s e 1,1248 s, incluindo inicialização do processo |

Não foram executados Python 3.11, outras versões das bibliotecas ou outros sistemas operacionais. As versões efetivamente usadas estão registradas; o manifesto do projeto continua declarando os intervalos suportados, não um lockfile de todas as plataformas.

## Entradas e resultado auditado

O relatório Orbe original e o XLSX de taxas foram copiados byte a byte para `data/raw/` da cópia limpa. Os hashes das entradas foram conferidos contra os arquivos originais antes/depois das execuções. Nenhuma limpeza manual, fusão ou alteração das fontes foi feita.

| Verificação | Resultado |
| --- | --- |
| Competência | Derivada dos dados: 2026-09 |
| Linhas de entrada | 1.943 IDs únicos |
| Calculadas | 1.886 contribuições |
| Pendentes | 57 eventos da Atlas, com motivo e responsável |
| Cobertura | 100% das referências em exatamente um destino principal: rastro ou pendência |
| Comissões | 21 linhas CHECKOUT, com CNPJs normalizados |
| Rastro | Soma exata por id_saida, incluindo zeros e negativos |
| Subtotal provisório | R$ 207.039,73; referência de conferência, sem constante no código |
| Determinismo | Dois CSVs e manifesto idênticos em bytes em duas pastas distintas |
| Proveniência | Hashes de fontes, configuração e saídas conferidos por verificador independente |

O verificador `tests/validar_saida.py` não importa o motor: audita layout, domínios, cobertura real por referência, datas/competência, valores publicados e vínculos de reversão. Os testes de cálculo continuam responsáveis pelas fórmulas e pela seleção contratual.

## Casos adicionais exercitados

- Outro mês sintético, sem alterar o código; modalidade nova, parcelamento inconsistente e EC sem cadastro geram pendências com cobertura mantida.
- Arquivo ausente e cabeçalho incompatível bloqueiam o resultado dependente. Arquivos anteriores gerados pelo produtor são invalidados, sem reapresentar um fechamento antigo como atual.
- Soma interna corrompida impede publicação dos CSVs; adulteração externa de comissão/referência é rejeitada pelo auditor mesmo após recalcular o hash do arquivo.
- Omissão de decisão financeira no manifesto é detectada.
- Falha simulada durante a publicação mantém o manifesto bloqueado; CSVs eventualmente presentes não são declarados válidos.
- Execução do pacote instalado a partir de um diretório externo, sem depender da raiz do código e sem chave de API.

## Limites e decisões pendentes

**D-07:** Atlas sem comissão estimada; forma final fora/zerada continua pendente. **D-08:** não há cálculo de devolução da Casa; a isenção confirmada e os estornos permanecem separados dessa decisão. **D-10:** ajuste da Ponte fora do escopo, sem aplicação antecipada de 50%.

A pasta completa contém dois candidatos Orbe, incluindo `06_orbe_ajustes_tardios_set2026.csv`. A execução nessa pasta foi verificada como `BLOQUEADO`, com lista de candidatos e nenhum arquivo declarado válido. Esse é um tratamento técnico seguro da ambiguidade, **não o processamento ou aceite do arquivo adicional**. A cobertura de 100% acima refere-se somente ao Orbe original selecionado no recorte.

Não foram implementados remessas, divergências, notas, extratos, devoluções, IA, recuperação futura da Atlas ou integrações. Os textos de hipóteses e regras registram as aprovações conhecidas e os tratamentos conservadores, sem atribuir aprovação financeira à autorização técnica desta etapa.

## Evidências locais e reprodução

`saida/entrega4/` contém os dois CSVs, manifesto, `aceite.json` com hashes/tempos/versões e `testes.log`. A cópia limpa mantém as execuções em `saida-a/` e `saida-b/`. Os artefatos anteriores não foram sobrescritos.

Para repetir em outra cópia nova, siga instalação, seleção explícita das duas entradas e comandos de auditoria da seção “Aceite independente e reprodução do zero” do README. Código `2` do motor é esperado para o case com pendências; código `0` do auditor confirma coerência do artefato provisório, sem aprovar a pendência financeira.

`saida/` e parte de `PROMPTS/` estão ignoradas pela configuração atual do repositório. Essa configuração do usuário foi preservada; a presença local das evidências não implica que estejam no último commit. Nenhum commit, push ou mudança de branch foi realizado pelo agente.
