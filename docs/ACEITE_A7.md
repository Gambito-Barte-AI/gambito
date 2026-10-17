# Aceite A7 — integrado e reprodução final

A7 autorizada pelo usuário em 17/10/2026. **Aceite técnico aprovado em Windows/Python 3.12.10**, preservando o mínimo, A1–A6 e a RN-64 corrigida. D-10 e o contrato da Atlas continuam pendentes; resultados computacionais COMPLETO não representam aprovação financeira, emissão fiscal ou autorização de pagamento. Extras não iniciados. Sem commits ou alteração de branch.

## Escopo e ajustes necessários

- Auditoria global independente do motor complementa os auditores de cada fonte: unicidade de IDs entre relatórios, produtor validado, domínios, datas ISO, precisão decimal, destinos existentes e soma exata dos rastros. Corrupções e registros extras indevidos são rejeitados mesmo quando os hashes de saída são recalculados.
- Rotina reproduzível `tests/aceite_integrado.py`: execução instalada fora da raiz, seis contratos, fechamento parcial, determinismo, regressão opcional e dados sintéticos de outra competência. Fontes oficiais somente para leitura; falhas de entrada são produzidas em cópias isoladas.
- Terminal passou a informar quantidades por método em cada banco, sem apresentar um banco bloqueado como zero movimentos.
- A falha intermitente de substituição do manifesto observada em A6 reapareceu em A7. Publicação agora repete somente PermissionError de acesso/compartilhamento do Windows (códigos 5/32/33), até quatro tentativas e pausas totais de 350 ms. Falha persistente continua impedindo a conclusão; outros erros não são repetidos. Testes verificam sucesso transitório e marcador incompleto na falha persistente.
- Nenhuma fórmula financeira, taxa, elegibilidade, layout de saída ou dependência declarada foi alterada. O manifesto conserva versão 8/etapa ALVO_A6: A7 é aceite da entrega existente, sem nova parte financeira. A descrição e o comentário de escopo do TOML apontam para este registro.

## Reprodução do zero

Criada cópia limpa do projeto em `.tmp/aceite-a7/projeto-limpo`, sem ambiente anterior, Context, entradas oficiais ou saídas antigas. Criado ambiente virtual novo e instalado o projeto com `pip install -e` nessa cópia. Verificados Python 3.12.10, openpyxl 3.1.5 e et_xmlfile 2.0.0; importação de tarvo da cópia e bibliotecas do novo ambiente.

O acesso inicial à pasta temporária exigiu TEMP/TMP graváveis dentro do projeto. A instalação restrita também encontrou indisponibilidade de DNS; a instalação com acesso de rede autorizado concluiu. A instalação depende do índice de pacotes/backend de build, sem novas dependências declaradas. A execução instalada foi realizada por subprocesso fora da raiz, sem PYTHONPATH/PYTHONHOME, site-packages do usuário ou credenciais de API. Não requer Context nem resultados prévios em tempo de execução.

**233 testes passaram** na reprodução final (97,984 s): 220 anteriores e 13 novos de A7. O primeiro ensaio revelou o bloqueio transitório do Windows e duas expectativas de mensagem que passaram a ser detectadas antes pelo auditor global. Corrigidos a publicação e os testes de mensagem; logs inicial e finais preservados.

Com ambiente instalado, o aceite pode ser repetido escolhendo destinos novos:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests/aceite_integrado.py --dados Tarvo_Data_Pack_set2026 --regras regras.toml --saida saida/reproducao-nova --evidencias .tmp/reproducao-nova --referencia saida/alvo-a6 --minimo saida/alvo-a1
```

As duas referências opcionais são regressões do mesmo pacote, não critérios financeiros para outros datasets. Em macOS/Linux, substituir o executável por `.venv/bin/python`; essas plataformas **não foram executadas/certificadas**. A tentativa de consultar WSL retornou acesso negado.

## Matriz integrada

21 cenários nomeados e uma execução adicional do mínimo, com conferência independente:

| Grupo | Verificação e resultado |
| --- | --- |
| Completo e repetição | Dez partes COMPLETO, retorno 0; seis CSVs e manifesto idênticos em bytes na repetição |
| Regressão | Seis CSVs do alvo idênticos a A6; seis CSVs do mínimo idênticos a A1 |
| Seis famílias de fonte | Ausência e layout inválido em cópias: somente partes dependentes afetadas; resultados independentes preservados |
| Taxas ausentes/inválidas | Checkout bloqueado; comissões/notas Ponte provisórias e divergências Ponte bloqueadas; bancos independentes |
| Nenhuma fonte | Bloqueio explícito, sem inventar resultados financeiros |
| Configuração ausente | Bloqueio e saídas vazias; conferência apenas estrutural, sem declarar cálculo financeiro auditado |
| Reuso de destino de teste | Remoção da Ponte elimina os resultados anteriores dessa família, sem reaproveitamento indevido |
| Outro mês e ajuste tardio | Outubro/2032 sintético com novos nomes, CNPJs, IDs e valores; fechamento e chegada posterior de estorno/reversão atualizam corretamente os resultados |

Os 13 novos testes cobrem também IDs duplicados, produtor desconhecido, origem duplicada/órfã, domínios/precisão/datas, faixa não suportada, adulteração de rastro em oito partes e dependências, RN-64 sintética e falhas de publicação. São dados de teste, sem constantes financeiras novas no motor.

## Resultados nas fontes recebidas

| Resultado | Evidência |
| --- | --- |
| Checkout | 1.957 linhas: 1.900 calculadas e 57 pendentes; 21 comissões, **R$ 203.735,34** |
| Ponte | 233 linhas físicas; 228 contribuições, quatro spreads negativos irregulares e uma duplicata; 14 comissões, **R$ 39.543,45** |
| RN-64 | **R$ 15.396,77** = R$ 15.405,85 cobrados − R$ 9,08 de estorno elegível; 118 origens. Estorno de agosto fora da devolução e preservado no checkout |
| Propostas de notas | 21: vinte de checkout e uma da Ponte; **R$ 243.284,29**. Casa sem nota devido ao saldo de comissão negativo, com pendência explícita |
| Bancos | 184 classificados: 84 Aurora e 100 Meridiano; duas pendências bancárias de revisão preservadas |
| Seis CSVs | 35 comissões, 115 divergências, 21 propostas, 184 classificados, 83 pendências e 5.080 rastros |
| Integridade | 108 arquivos oficiais/referências com SHA-256 idêntico antes/depois; documentos, Context, data pack, data/raw e saídas anteriores preservados |

As 83 pendências do alvo incluem as 57 do mínimo. Pendências de negócio não tornam automaticamente uma parte PROVISORIO, conforme D-13; ausência/layout inválido e inconsistência de rastro mantêm estados e motivos próprios.

## Evidências e limites

- Saída final: `saida/alvo-a7-final/`, em destino novo; primeira reprodução em `saida/alvo-a7/` também preservada.
- Matriz final: `.tmp/aceite-a7/cenarios-final/resultado.json` e logs por cenário; nova reprodução após atualização exclusivamente descritiva do TOML.
- Testes: `.tmp/aceite-a7/testes-reproducao-final.log`; ensaios anteriores mantidos em logs separados.
- Instalação/ambiente: `.tmp/aceite-a7/instalacao.log`, `ensurepip.log`, `ambiente.json` e `copia-fontes.json`.
- Integridade: `.tmp/aceite-a7/integridade.json`, com hashes iniciais e comparação final.

Evidências locais em `.tmp/` e `saida/` seguem as regras de exclusão do repositório; este documento e os scripts permitem reproduzi-las. A7 certifica os contratos suportados e os cenários executados, sem prometer suporte a layouts arbitrários.

Continuam explícitas: confirmação financeira de D-10 (participação atual do time mantida sem nova decisão), contrato da Atlas e datas/aprovações sem evidência. Classificação nova ou ambígua exige revisão; não houve IA, integração externa, extras ou alteração dos materiais oficiais.
