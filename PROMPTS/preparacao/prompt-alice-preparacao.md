# Preparação · Alice (antes da liberação do case)

Transcript da sessão de Claude Code (app desktop) usada por **Alice Carvalho** no Desafio Barte AI, exportado do arquivo `.jsonl` do próprio Claude Code, em ordem cronológica e sem edição do texto.

- **Período:** 16/10 15:58 a 16/10 19:12 (horário de Brasília).
- **Mensagens:** 1 da Alice e 4 blocos de resposta do Claude.
- **O que foi removido:** e-mails e padrões de chaves ou tokens (substituídos por `[e-mail removido]` e `[removido]`).
- **O que não entra:** as saídas das ferramentas (leitura de arquivos, Slack, Canva, terminal), pelo volume e por conterem dados de terceiros. Cada chamada de ferramenta aparece como `🔧 nome · entrada resumida`. Imagens aparecem como `[imagem anexada]`.
- **Resumos de contexto:** quando a conversa ficou longa, o Claude Code gerou resumos automáticos; eles aparecem marcados como "Sistema".

---

> 🔧 `ToolSearch` · {"query": "select:WebSearch,WebFetch", "max_results": 2}

> 🔧 `mcp__ccd_turn__update_plan` · {"items": [{"content": "Pesquisar Barte: produto, rodadas, notícias", "status": "in_progress"}, {"content": "Pesquisar AI Services e pessoas", "status": "pending"}, {"content": "Pesquisar Junior Fellows e o hackathon", "status": "pending"}, {"content": "Levantar temas técnicos e regulatórios", "status": "pending"}, {"content": "Montar o dossiê final com fontes", "status": "pending"}], "scope": "fi …

> 🔧 `WebFetch` · {"url": "https://www.barte.com/", "prompt": "Descreva em detalhe: o que a Barte faz, produtos, clientes citados, números, posicionamento AI-native, AI Services, links para páginas de produtos/carreiras/blog/fellows/hackathon."}

> 🔧 `WebSearch` · {"query": "Barte fintech rodada investimento Raphael Dyxklay", "mode": "extended"}

> 🔧 `WebSearch` · {"query": "\"Barte\" \"AI Services\" forward deployed engineers finanças", "mode": "extended"}

> 🔧 `WebSearch` · {"query": "\"Desafio Barte AI\" OR \"Junior Fellows\" Barte hackathon", "mode": "extended"}

> 🔧 `WebFetch` · {"url": "https://www.barte.com/blog-posts/fde-para-financas", "prompt": "Resuma em detalhe: como funciona o modelo de squads/FDE da Barte, composição do squad, fases, casos de uso, resultados, métricas, clientes, referências a Anthropic/OpenAI/Ramp/Palantir, autor e data."}

> 🔧 `WebFetch` · {"url": "https://www.barte.com/ai-services", "prompt": "Resuma em detalhe a oferta de AI Services/automação agêntica: como funciona, etapas, casos de uso, resultados, clientes, preço, equipe, tecnologias, segurança."}

> 🔧 `WebSearch` · {"query": "Barte receita R$ 300 milhões 2026 agentes IA CFO", "mode": "extended"}

> 🔧 `WebFetch` · {"url": "https://cgn.inf.br/noticia/1900711/fintech-barte-triplica-receita-para-r-150-mi-e-pode-ser-avaliada-em-mais-de-r-1-bi", "prompt": "Extraia todos os fatos: receita, valuation, investidores, número de clientes, TPV, produtos, fundadores, planos, data da matéria e fonte original."}

> 🔧 `WebFetch` · {"url": "https://exame.com/negocios/proximo-unicornio-esta-empresa-brasileira-dobrou-a-receita-em-sete-meses/", "prompt": "Extraia todos os fatos e citações de Raphael Dyxklay: receita, clientes, IA, AI Services, squads, agentes, metas, investidores, concorrentes, data."}

> 🔧 `WebFetch` · {"url": "https://economiasp.com/2026/02/06/barte-fecha-ano-com-r-250-milhoes-de-receita-e-aposta-de-r-100-milhoes-em-ia/", "prompt": "Extraia todos os fatos: receita, aposta em IA, produtos de IA, squads, clientes, citações dos executivos, nomes de pessoas."}

> 🔧 `WebFetch` · {"url": "https://braziljournal.com/barte-vale-r-400-milhoes-em-rodada-para-crescer-em-pagamentos/", "prompt": "Extraia fatos: rodada, investidores, valuation, história dos fundadores, modelo de negócio, clientes, data."}

> 🔧 `WebFetch` · {"url": "https://tiinside.com.br/01/10/2026/barte-cria-diretoria-de-estrategia-e-contrata-rodolfo-bizinoto-net/", "prompt": "Extraia todos os fatos e nomes de executivos, números e citações."}

> 🔧 `mcp__ccd_turn__update_plan` · {"advance": true}

> 🔧 `WebSearch` · {"query": "Raphael Dyxklay Barte entrevista podcast IA", "mode": "extended"}

> 🔧 `WebSearch` · {"query": "\"Beny Braun\" Barte", "mode": "extended"}

> 🔧 `WebSearch` · {"query": "\"Túlio Lancaster\" OR \"Tulio Lancaster\" Barte", "mode": "extended"}

> 🔧 `WebSearch` · {"query": "\"Daniel Dias\" Barte fintech", "mode": "extended"}

### Claude · 16/10 15:58

Ainda pesquisando. Já tenho o panorama da Barte (rodadas, receita, AI Services) e agora estou levantando as pessoas e o programa Junior Fellows.

> 🔧 `WebFetch` · {"url": "https://startups.com.br/5-minutos-com/5-minutos-com-raphael-dyxklay-presidente-e-co-founder-da-barte/", "prompt": "Extraia tudo: citações de Raphael Dyxklay, visão de IA, laboratório de IA, AI services, squads, prioridades 12-18 meses, cultura, contratação, data."}

> 🔧 `WebFetch` · {"url": "https://www.astella.com.br/matrix/raphael-dyxklay-podcast-astella-playbook", "prompt": "Extraia tudo: temas, citações, visão de contratação, time de elite, AI services, engenheiros embarcados, cultura, data."}

> 🔧 `WebSearch` · {"query": "Barte \"Junior Fellows\" programa", "mode": "extended"}

> 🔧 `WebFetch` · {"url": "https://www.barte.com/cultura", "prompt": "Resuma valores, cultura, perfil de pessoas que contratam, programas de estágio/fellows/trainee, processo seletivo."}

> 🔧 `WebFetch` · {"url": "https://vagas.barte.io", "prompt": "Liste vagas abertas, especialmente Junior Fellows, AI Services, FDE, estágio; descreva perfil, requisitos, processo seletivo e qualquer menção a hackathon ou Desafio Barte AI."}

> 🔧 `WebSearch` · {"query": "Barte fellows hackathon Casa Barte outubro 2026 inteligência artificial finanças", "mode": "extended"}

> 🔧 `WebFetch` · {"url": "https://www.barte.com/blog/inicio", "prompt": "Liste os títulos e datas dos posts mais recentes (especialmente 2026) sobre IA, agentes, FDE, AI services, fellows, hackathon, conciliação, cobrança; inclua URLs."}

> 🔧 `WebFetch` · {"url": "https://barte.com/blog-posts/niveis-de-maturidade-em-ai", "prompt": "Liste os 5 níveis de maturidade em AI para times financeiros com descrição de cada um, e principais argumentos. Autor e data se houver."}

> 🔧 `WebFetch` · {"url": "https://barte.com/blog-posts/estudo-de-caso-comp", "prompt": "Detalhe o case da Comp: problema, o que foi construído, agentes, tempo, resultados, números, pessoas citadas."}

> 🔧 `WebFetch` · {"url": "https://barte.com/blog-posts/ia-no-financeiro", "prompt": "Resuma argumentos principais, números, arquitetura de dados, recomendações. Autor e data."}

> 🔧 `WebFetch` · {"url": "https://barte.com/blog-posts/pagamentos-agenticos", "prompt": "Resuma argumentos principais, números, protocolos citados (AP2, ACP, Visa, Mastercard, Pix), riscos, recomendações. Autor e data."}

> 🔧 `mcp__ccd_turn__update_plan` · {"advance": true}

> 🔧 `WebSearch` · {"query": "Beny Braun AI Services for Finance linkedin", "mode": "extended"}

> 🔧 `WebSearch` · {"query": "Túlio Lancaster Santos Andrade", "mode": "extended"}

> 🔧 `WebSearch` · {"query": "Barte Endeavor Outliers 2026 lista", "mode": "standard"}

> 🔧 `WebSearch` · {"query": "Banco Central Pix novidades 2026 Pix parcelado MED 2.0 Pix automático Open Finance", "mode": "extended"}

> 🔧 `WebFetch` · {"url": "https://br.linkedin.com/in/beny-braun-83b457284", "prompt": "Extraia cargo, experiência, formação, posts e sobre."}

> 🔧 `WebFetch` · {"url": "https://www.linkedin.com/in/rapha-dyxklay", "prompt": "Extraia cargo, experiência, formação, sobre e posts recentes."}

> 🔧 `WebFetch` · {"url": "https://barte.com/blog-posts/brasil-lidera-lista-outliers-endeavor", "prompt": "Extraia fatos: data, o que é a lista, por que a Barte entrou, números citados."}

> 🔧 `WebSearch` · {"query": "Banco Central regras segurança instituições de pagamento após ataque C&M Sinqia autorização prazo 2026 PSTI", "mode": "extended"}

> 🔧 `WebSearch` · {"query": "Pagar.me Asaas Iugu Stripe Brasil 2026 agentes IA pagamentos B2B notícias", "mode": "extended"}

> 🔧 `WebFetch` · {"url": "https://br.linkedin.com/in/rapha-dyxklay", "prompt": "Extraia cargo, experiência, formação, sobre e posts recentes."}

### Claude · 16/10 16:00

Fechando as últimas buscas (a turma de formação em FDE da Barte, que deve ter a ver com o Junior Fellows). Depois disso, monto o dossiê.

> 🔧 `WebSearch` · {"query": "Barte formação FDE turma \"Forward Deployed\" inscrição", "mode": "extended"}

> 🔧 `WebFetch` · {"url": "https://abreu.substack.com/p/insights-semi-controversos-sobre-2d4", "prompt": "Liste as principais opiniões/insights de Raphael Dyxklay e a data."}

> 🔧 `mcp__ccd_turn__update_plan` · {"done": [3, 4], "start": 5}

> 🔧 `Write` · {"file_path": "C:\\Users\\alice\\AppData\\Roaming\\Claude\\scratch-workspaces\\340037dd-c58e-4941-b475-7403124136ac\\01e8a2fb-844a-4f13-97e0-b49352a2e591\\scratch-2026-10-16-94f64a\\dossie-desafio-barte-ai.md", "content": "# Dossiê: Desafio Barte AI (sáb 17/10/2026, Casa Barte, SP, 8h–22h)\n\nLegenda: ✅ confirmado em fonte · ⚠️ incerto, conflitante ou inferido · 📚 conhecimento geral (não verifique …

> 🔧 `mcp__ccd_turn__wrap_up` · {"recap": "O dossiê do Desafio Barte AI está pronto, com fontes e incertezas marcadas. Não achei nada público sobre o Junior Fellows nem sobre Beny, Túlio e Daniel, então vale olhar o LinkedIn deles hoje à noite."}

### Claude · 16/10 16:03

Terminei a pesquisa. O dossiê completo, com fontes e o que é incerto marcado com ⚠️, está em [dossie-desafio-barte-ai.md](dossie-desafio-barte-ai.md). Ele tem o resumo de uma página, as 10 perguntas, o glossário (cerca de 60 termos) e o plano de escopo para o dia.

**O essencial para chegar sabendo:**
- **Barte:** infraestrutura financeira para médias e grandes empresas, com pagamentos, tesouraria, multiadquirência white-label e agentes de IA.
  - Receita anualizada saiu de R$ 150 mi (ago/25) para cerca de R$ 300 mi (mar/26), com meta de R$ 500 mi em 2026.
  - Movimenta cerca de R$ 10 bi por ano (TPV), atende mais de 10 mil empresas e é lucrativa.
  - Promete investir R$ 100 mi em IA até 2027.
  - A última rodada pública foi a Série A de out/24, liderada pela AlleyCorp, com valuation de R$ 400 mi. Hoje a imprensa estima cerca de R$ 1 bi ⚠️.
  - Entrou na lista Endeavor Outliers 2026.
- **AI Services (o modelo FDE da Barte):** um squad formado por especialista financeiro, engenheiro de IA e agentes entra na operação do cliente. Custa de R$ 20 a 35 mil por mês, segundo o blog deles.
  - A tese central é "a IA é 5% do trabalho, o dado é 95%". Antes do agente, banco e ERP precisam bater.
  - Cada exceção resolvida por um humano vira uma regra nova.
  - Eles usam um modelo de maturidade de 5 níveis. Leia esse post: é provável que usem esse vocabulário no painel.
  - Cases que eles mesmos divulgam: Comp ("pipeline de 1 ano em 2 meses"), Buser (R$ 402 mil) e Sallve (fechamento em 5 dias).
- **Raphael Dyxklay:** formado em Letras, passou por Creditas, Loft e Olist.
  - Valoriza pensamento independente (primeiros princípios, "mentalidade de pesquisador") e intensidade.
  - Gosta de contratar no começo de carreira e usa uma semana de trabalho remunerada no processo seletivo.
  - Se der tempo, ouça o episódio dele no Astella Playbook (jul/26).

**O que não consegui confirmar:**
- **Junior Fellows e Desafio Barte AI:** não há nada público. Pela minha inferência ⚠️, o programa deve estar ligado à "turma de formação em FDE" que a Barte vem divulgando no LinkedIn.
- **Beny Braun, Túlio Lancaster e Daniel Dias:** não há rastro público que os ligue à Barte, e o LinkedIn bloqueia leitura automática. Abra os perfis deles hoje à noite e anote cargo, trajetória e um ou dois posts de cada.
- Uma fonte fala em "Série D de R$ 2,7 bi". Parece falso, então não cite.

**Dica para o hackathon:** escolha um único processo, como conciliação, cobrança ou o gap entre DRE e caixa. Rode o agente sobre dados sujos e realistas e mostre fila de exceções para humano, trilha de auditoria, uma métrica de acurácia medida e quanto em reais o cliente economiza. É exatamente a língua deles.

Se quiser, transformo o dossiê numa página fácil de ler no celular amanhã de manhã.

If you want to keep this work, I can move this session to a folder you choose.

### Alice · 16/10 19:11

[imagem anexada]

como vai funcionar amanha:

> 🔧 `mcp__ccd_turn__update_plan` · {"items": [{"content": "Adaptar o plano do dossiê à agenda oficial", "status": "in_progress"}], "scope": "continuation"}

> 🔧 `Edit` · {"replace_all": false, "file_path": "C:\\Users\\alice\\AppData\\Roaming\\Claude\\scratch-workspaces\\340037dd-c58e-4941-b475-7403124136ac\\01e8a2fb-844a-4f13-97e0-b49352a2e591\\scratch-2026-10-16-94f64a\\dossie-desafio-barte-ai.md", "old_string": "### 5.7 Como priorizar escopo e pitchar\nO evento vai das 8h às 22h. Se o build for de cerca de 9h, a agenda abaixo funciona:\n\n| Bloco | Tempo | O que …

> 🔧 `mcp__ccd_turn__wrap_up` · {"recap": "Atualizei a seção 5.7 do dossiê com a agenda oficial: perguntas para o cliente hoje à noite, o plano de sábado por bloco e o roteiro do pitch de 10 minutos."}

### Claude · 16/10 19:12

Pela agenda que você mandou, o jogo começa **hoje**: o case sai até as 20h30 e o financeiro do cliente responde das 20h30 às 22h30. Atualizei a seção 5.7 do [dossiê](dossie-desafio-barte-ai.md) com isso.

**Hoje à noite (o que mais vale o seu tempo):**
1. Pergunte ao cliente:
   - qual é a dor nº 1 em horas ou R$;
   - como é o processo passo a passo e quais sistemas e arquivos entram;
   - quais são as exceções comuns e como um analista experiente resolve cada uma;
   - o que seria "pronto" para ele e qual métrica faria ele usar na segunda;
   - quanto custa um erro e onde ele exige aprovação humana;
   - que dados ainda vão chegar amanhã.
2. Escreva em uma frase o problema e a métrica de sucesso.
3. Deixe pronto o repositório, o script que carrega os dados do case e o esqueleto do eval (o conjunto de casos para medir acurácia). Depois, durma.

**Sábado:**
- **8h credenciamento:** a pontualidade é avaliada **por pessoa**. Chegue antes.
- **9h painel:** é a hora das suas perguntas (seção 6 do dossiê).
- **9h30–11h:** explore os dados e monte uns 30 a 50 casos rotulados para o eval.
  - Para o **checkpoint 1 (11h)**, leve hipóteses, escopo e **o que fica de fora, com o motivo**. Eles pedem isso explicitamente, e o Rapha valoriza coerência de premissas.
- **11h–15h30:** construa uma fatia de ponta a ponta: ingestão, regras, LLM só no que sobrar, fila de exceções com justificativa e KPIs. Deixe a ingestão tolerante a dado novo, porque podem chegar dados durante o dia.
- **15h30, checkpoint 2:** mostre o que roda, o número do eval e **o que mudou de hipótese e por quê**.
- **Até 17h30:** última validação com o cliente, que só responde até esse horário.
- **18h30:** commit depois disso não conta. Faça commit e push a cada marco, nunca deixe para o último minuto.
- **18h30–19h:** grave um vídeo de backup da demo e feche o deck. Todos enviam o pitch às 19h.
- **Finalistas (19h30):** são 10 minutos de apresentação e 5 de perguntas. Uma divisão que funciona:

| Tempo | Conteúdo |
|---|---|
| 1 min | Dor do cliente, nas palavras dele |
| 4 min | Demo com uma exceção indo para um humano |
| 2 min | Confiabilidade: eval e trilha de auditoria |
| 1,5 min | Impacto e o que mudou desde o checkpoint 1 |
| 1,5 min | O que ficou de fora e o próximo passo |

Quando o case sair, me manda que eu te ajudo a escolher o recorte e a preparar as perguntas para o cliente.
