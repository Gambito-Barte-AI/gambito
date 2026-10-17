# Giorgia Scherer — Momentos relevantes de uso de IA

**Projeto:** Gambito — Hackathon Barte AI | Case Tarvo  
**Participante:** Giorgia Scherer  
**Ferramentas utilizadas:** **Claude** (análise exploratória, hipóteses, leitura do repositório e apoio técnico) e **ChatGPT** (entendimento do case, estruturação do raciocínio de negócio, planejamento e construção do pitch).

## Momento 1 — Da automação à causa raiz do fechamento

Solicitei apoio para organizar o diagnóstico da Tarvo a partir das fontes financeiras e das análises exploratórias; a IA estruturou um canvas com o fluxo das duas linhas de negócio, chaves de conciliação, hipóteses H1–H10 e questões para validação. Usei essa estrutura para aprofundar a tese central do case: o problema não era simplesmente a falta de automação, mas a combinação de identificação inconsistente dos lojistas, regras comerciais pouco formalizadas e decisões que não chegavam de maneira confiável ao fechamento.

## Momento 2 — Divergências de taxa como risco econômico e contratual

Pedi orientação para avançar na análise de divergências entre as taxas previstas em contrato e as aplicadas pela Orbe; a IA propôs comparar as taxas por transação, levando em conta a vigência contratual, os estornos e os arredondamentos. A partir disso, direcionei o foco para o significado de negócio das diferenças: separar erros efetivamente cobráveis de exceções contratuais, como a isenção da Casa do Estudante, evitando transformar toda diferença matemática em uma cobrança indevida.

## Momento 3 — Ajustes tardios alteram o fechamento financeiro

Questionei quais achados das minhas análises realmente poderiam mudar a rota do projeto; a IA identificou que a regra RN-65 exigia incorporar os ajustes tardios do arquivo 06 da Orbe, enquanto o motor ainda bloqueava a execução conjunta dos arquivos 01 e 06. A análise demonstrou o impacto material no resultado de referência do checkout: de **R$ 207.039,73** para **R$ 203.735,34**, uma diferença de **R$ 3.304,39** que não poderia ser ignorada na conciliação nem na apresentação à banca.

## Momento 4 — Revisão crítica das entregas e confiabilidade do resultado

Depois de novos commits, solicitei à IA outra leitura do repositório para confrontar o avanço técnico com os requisitos do case; ela apontou progresso no tratamento de estornos e reversões, mas também o bloqueio persistente do arquivo 06, diferenças no valor de devolução da Casa do Estudante e riscos de omissão dos arquivos de saída e de histórico de prompts. Usei os apontamentos para priorizar a consistência entre regras de negócio, números do fechamento, rastreabilidade e entregáveis, em vez de avaliar o projeto apenas pela quantidade de funcionalidades ou testes.

---

## Momento de pensamento crítico — Questionei a direção da análise da IA

Quando a IA sugeriu seguir diretamente para a implementação das divergências, questionei se aquela era realmente a prioridade e pedi que explicasse **quais achados das minhas análises mudavam a rota do negócio**. Ao reformular a resposta, ela identificou impactos que precisavam vir antes da implementação isolada: a inclusão dos ajustes tardios no fechamento, a mudança do total de comissões e a divergência entre os valores de devolução da Casa do Estudante (**R$ 15.396,77** e **R$ 15.397,42**); o questionamento deslocou a discussão de execução de código para precisão financeira, governança das regras e confiabilidade da decisão.
