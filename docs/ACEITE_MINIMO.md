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
