# AGENTS.md — Diretrizes de desenvolvimento

## 1. Contexto do projeto

Este repositório contém o projeto do hackathon Gambito para a Tarvo Pagamentos, uma subadquirente fictícia. A solução automatiza o fechamento mensal de comissões de checkout (Orbe), comissões de remessas (Ponte Câmbio), divergências de taxas, notas a emitir, classificação de extratos, pendências e trilha de auditoria.

O case usa seis fontes heterogêneas e exige seis CSVs de saída. A solução deve aceitar novos arquivos mensais no mesmo formato, sem regras ou caminhos fixos para setembro de 2026.

Antes de propor ou implementar mudanças, consulte a documentação relevante. Use como referências principais:

- `Context/context.md`: contexto do case, decisões, níveis de entrega e regras confirmadas.
- `Context/regrasdenegocio.md`: regras operacionais e respectivas fontes/aprovações.
- `Context/arquitetura.md`: arquitetura e decisões técnicas do time.
- `Context/01_instrucoes_participantes.docx`: instruções originais do desafio.
- `Tarvo_Data_Pack_set2026/00_LEIA-ME.md`: descrição das entradas de exemplo.
- `docs/FORMATO_SAIDA.md`: layout e domínios exigidos nas saídas.
- `HIPOTESES.md`: hipóteses e decisões ainda não confirmadas.
- `README.md`: configuração e execução destinadas à banca.

O contexto define **o que** o produto deve fazer; este arquivo define **como** desenvolver. Não invente regras de negócio, contratos, integrações ou requisitos. Os dados do data pack são sintéticos e servem como exemplo do formato.

## 2. Princípios

1. **Correção financeira e rastreabilidade:** cada valor deve ser explicável e ligado às fontes de origem.
2. **Simplicidade:** escolha a solução mais simples que atenda ao case e seja fácil de revisar.
3. **Entrega incremental:** priorize fluxos pequenos, completos e demonstráveis.
4. **Consistência:** respeite a arquitetura, dependências e convenções já adotadas.
5. **Controle de escopo:** não implemente extras ou refatorações sem relação com a tarefa.
6. **Reprodutibilidade:** mesmas entradas e regras devem produzir as mesmas saídas.
7. **Supervisão humana:** incertezas de negócio devem aparecer como pendências, com motivo e responsável pela decisão.

Evite ML, serviços externos, infraestrutura ou abstrações sem necessidade demonstrada. A prioridade é uma solução funcional para o nível mínimo e, em seguida, para o alvo descrito no contexto. Extras só entram depois do alvo ou por pedido explícito.

## Data-Agnostic Processing and Official Data Preservation

- O motor deve ser independente dos datasets exploratórios. Novos datasets compatíveis com os contratos documentados devem funcionar sem alterações na lógica central.
- Valores, IDs, estabelecimentos, datas e nomes de arquivos específicos não podem determinar comportamentos do motor, salvo exigência explícita de regra oficial com fonte e aprovação documentadas. Condições comerciais específicas devem permanecer na configuração apropriada, sem exceções artificiais por nome ou resultado esperado.
- Regras financeiras devem expressar critérios de negócio generalizáveis, documentados e configuráveis quando apropriado, respeitando a hierarquia de decisão da seção 3.
- Exemplos oficiais e resultados conhecidos servem para compreender contratos, validar e testar regressões; nunca como valores fixos, atalhos ou condições para reproduzir gabaritos no processamento. Isso inclui a RN-64: o líquido deve resultar das cobranças e dos estornos elegíveis pela origem e vigência da venda, sem fixar totais conhecidos.
- Todos os arquivos oficiais do parceiro são imutáveis e devem ser tratados exclusivamente como fontes de leitura, incluindo documentos, CSVs, anexos, gabaritos e resultados de referência. Não modificar, sobrescrever, renomear, mover ou excluir esses materiais, nem alterar seu conteúdo, estrutura, nome ou localização para adequá-los ao código. Saídas geradas devem ficar em destinos próprios, separados dos materiais oficiais.
- Inconsistências dos originais devem ser registradas e tratadas pela lógica ou como pendências, conforme as regras aprovadas; nunca corrigidas manualmente nos arquivos oficiais.
- Testes que modifiquem entradas devem usar cópias isoladas ou dados sintéticos, preservando integralmente os originais e as referências de validação.
- Precisão financeira, rastreabilidade e integridade dos dados são obrigatórias, conforme os critérios de cálculo, reconciliação e publicação das seções 2, 5 e 7.

## 3. Hierarquia de decisão

Ao tomar decisões, siga esta ordem:

1. Instruções explícitas da tarefa atual.
2. Regras confirmadas do case e instruções dos participantes.
3. Decisões de arquitetura aprovadas pelo time.
4. Convenções existentes no repositório.
5. Boas práticas gerais.

Se houver conflito entre fontes, explicite-o e não transforme silenciosamente uma hipótese em regra. Registre decisões não confirmadas em `HIPOTESES.md`, com justificativa e impacto. Taxas, condições comerciais e regras financeiras só podem ser alteradas com fonte ou aprovação documentada.

## 4. Regras específicas do case

- O fluxo principal deve ingerir os seis formatos/fontes descritos no contexto: CSV da Orbe, XLSX de taxas, e-mail `.eml` com anexo da Ponte, plano de contas CSV, extrato CSV Aurora e extrato OFX Meridiano.
- Comissão de checkout usa a taxa contratada aplicável, e não `valor_taxa` informado pela Orbe. A taxa aplicada serve para identificar divergência.
- Comissão de remessa segue a participação da Tarvo e o arredondamento documentados nas regras de negócio. Não trate spread negativo, duplicidade ou exceções como receita normal.
- Não confunda divergência contratual com devolução ao lojista ou outra pendência operacional; respeite a natureza definida no contexto.
- A IA pode sugerir correspondências ou classificações nos pontos autorizados, mas não calcula valores, cria/aprova regras, aprova lançamentos ou substitui decisão humana. Sugestões incertas devem ser revisáveis e sinalizadas.
- Não envie e-mail, conteste transações, transfira valores, emita notas nem integre sistemas externos sem pedido explícito. O escopo do case é gerar informações e arquivos para revisão/ação humana.
- Não exponha credenciais nem dados financeiros fora do necessário. Use `.env.example` para documentar configuração sem segredos.

## 5. Saídas e integridade

As seis saídas obrigatórias ficam em `saida/` e devem respeitar o contrato em `docs/FORMATO_SAIDA.md`:

1. `comissoes_por_lojista.csv`
2. `divergencias_taxa.csv`
3. `notas_a_emitir.csv`
4. `lancamentos_classificados.csv`
5. `pendencias.csv`
6. `rastro.csv`

Preserve os domínios e convenções definidos no formato de saída: separador `;`, decimal com ponto, data `AAAA-MM-DD`, CNPJ numérico com 14 dígitos e valores permitidos para linha de negócio, banco, método e confiança.

O rastro é requisito funcional, não um relatório opcional. Cada `id_saida` deve apontar às referências de origem e a soma dos valores do rastro deve reconciliar com o valor reportado, conforme a regra aplicável. Se a reconciliação falhar, não apresente a saída como fechamento válido; sinalize o erro de forma clara.

## 6. Antes de implementar

1. Identifique o nível da entrega (mínimo, alvo ou extra) e o resultado pedido.
2. Leia as regras e hipóteses relacionadas à alteração.
3. Inspecione os arquivos e padrões relevantes do repositório.
4. Defina a menor alteração que atende aos critérios de aceite.
5. Para mudanças complexas ou arquiteturais, exponha um plano curto antes de editar; para mudanças pequenas e autorizadas, prossiga diretamente.
6. Se o pedido for apenas análise ou planejamento, não altere arquivos.

## 7. Implementação

- Siga linguagem, estrutura e estilo já estabelecidos; mantenha cada módulo com responsabilidade clara.
- Evite duplicar regras de negócio e mantenha-as legíveis e, quando a arquitetura permitir, separadas da lógica de leitura e apresentação.
- Use aritmética decimal apropriada para dinheiro; não use ponto flutuante binário para cálculos financeiros sem uma justificativa explícita.
- Preserve identificadores e referências de origem ao normalizar dados. Não faça correspondência ambígua de lojistas como se fosse confirmada.
- Trate encoding, cabeçalhos deslocados, formatos de data e separadores conforme as fontes. Erros de leitura devem indicar arquivo e causa, sem produzir fechamento parcial enganoso.
- Trate duplicidades, ausências e exceções conforme as regras documentadas; não descarte linhas silenciosamente.
- Não adicione dependências, altere interfaces públicas ou faça refatorações amplas sem necessidade.
- Preserve trabalho existente. Não sobrescreva saídas, arquivos ou alterações do usuário sem verificar o conteúdo e o impacto.

## 8. Validação

Valide de forma proporcional à alteração e conforme o pedido do usuário. Para mudanças no pipeline, considere conferir os seis arquivos, esquemas/domínios, determinismo, casos de erro e reconciliação do rastro. Para alterações pontuais, prefira verificações focadas.

Não afirme que testes, lint, compilação ou execução passaram sem tê-los realizado. Se uma validação necessária não puder ser feita, informe claramente o que ficou sem verificar e por quê.

## 9. Repositório e comunicação

- Mantenha `README.md` suficiente para configurar e executar a solução do zero, inclusive indicando como configurar eventual chave de API.
- Registre sessões e momentos relevantes de uso de IA em `PROMPTS/`, conforme solicitado pelo desafio, sem inventar interações.
- Evite alterar arquivos não relacionados, instalar pacotes sem motivo claro ou modificar lockfiles sem mudança correspondente de dependência.
- Não crie commits, faça push ou altere branches sem solicitação.
- Comunique progresso e conclusão de forma breve, objetiva e em português, destacando arquivos alterados, validação realizada e limitações relevantes.

## 10. Definição de concluído

Uma alteração está concluída quando atende ao pedido e aos critérios de aceite, respeita as regras documentadas e a arquitetura, preserva a rastreabilidade financeira, não modifica escopo alheio e foi validada na medida adequada (ou tem suas limitações explicitadas).

**Regra final:** priorize um fechamento funcional, determinístico, revisável e rastreável; mantenha decisões financeiras sob aprovação humana.
