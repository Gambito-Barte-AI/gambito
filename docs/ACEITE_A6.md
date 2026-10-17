# Aceite A6 — Meridiano

A6 autorizada pelo usuário e implementada em 17/10/2026, seguindo AGENTS.md. Preservados o mínimo, A1–A5, RN-64 corrigida, D-10 pendente e arquivos oficiais. **A7 não foi iniciada**; este documento registra a validação de A6 e suas regressões, sem substituir o aceite formal integrado do alvo. Nenhuma instalação, integração externa, commit ou alteração de branch realizada pelo agente.

## Implementação e contratos

- `leitores/meridiano.py`: um OFX por pasta, sem nome mensal fixo. Aceita o contrato SGML com encoding declarado cp1252/UTF-8 e campos-folha com fechamento opcional. Valida os agregados, conta, moeda BRL, status do banco e lista completa de movimentos. Moeda incompatível, estrutura truncada, campos ambíguos ou múltiplas contas/arquivos bloqueiam somente Meridiano. Não converte moeda ou repara encoding por suposição.
- RN-57: FITID preservado; DTPOSTED usa o dia local informado, sem deslocamento UTC. Decimal, sinais e descrições preservados. Campos inválidos têm diagnóstico e valor conhecido assinado; valor desconhecido fica vazio, sem zero nem arredondamento inventado.
- FITID repetido: todas as ocorrências ficam pendentes, mesmo se iguais, sem escolha arbitrária. É uma política técnica conservadora: não há regra financeira aprovada autorizando escolher uma ocorrência no banco. A verificação ocorre antes do recorte de competência. FITID ausente usa a linha física apenas como localização diagnóstica e nunca produz classificado com ID inventado.
- `classificacao.py` e a coordenação de A5 passaram a receber o banco explícito. Mesmas regras de conta existente/analítica/permitida, sinal, correspondência única, cobertura, pendências e rastro; não houve alteração das fórmulas ou registros financeiros anteriores. Contextos separados permitem revalidar e bloquear somente o banco afetado por adulteração.
- RN-46/RN-49/RN-55: recursos recebidos de lojistas e liquidação das remessas movimentam o passivo; recebimento de comissão baixa o recebível. Ponte Aérea é lojista, sem relação com Ponte Câmbio. Aplicação/resgate usa a conta da aplicação, sem inferir rendimento pela diferença. Rendimento explícito, tarifas, seguro e IOF seguem contas analíticas próprias. Não há geração de provisões, conciliação entre bancos ou confirmação automática do trânsito.
- RN-61: regras por histórico/sinal/conta no TOML, com fonte, aprovação/critério, aprovador/papel e data. Mapeamentos técnicos não recebem aprovação financeira individual fictícia; datas sem evidência continuam NAO_INFORMADO. Nenhuma data, valor, FITID ou quantidade do exemplo foi fixada no motor.

Os seis contratos CSV e os bytes do mínimo foram preservados. Manifesto versão 8, etapa ALVO_A6. EXTRATO_AURORA e EXTRATO_MERIDIANO são independentes, compartilhando somente plano e regras. A fonte do plano continua necessária aos dois; checkout/Ponte não são pré-requisitos da classificação.

## Resultados confrontados com as fontes

| Verificação | Resultado |
| --- | --- |
| OFX Meridiano | **100 movimentos**, 100 FITIDs únicos, nenhum ID ausente/repetido no pacote fornecido |
| Classificação Meridiano | **100 classificados**, todos com conta permitida, data, método REGRA, confiança e rastro |
| Valor assinado Meridiano | **R$ 1.116.335,23**, preservado exatamente |
| Aurora preservado | **84 classificados**, valor assinado −R$ 2.532.423,41; duas pendências anteriores mantidas |
| Total bancário | **184 classificados**, quantidade derivada das fontes, sem constante no motor |
| RN-49 | Recebimento de R$ 61.884,12 pela comissão anterior em 1.1.03.002; sem reconhecer receita outra vez |
| RN-55 | R$ 18.240,00 da Ponte Aérea em 2.1.02.001, como recursos de lojista para remessas |
| Saídas A6 | 35 comissões, 115 divergências, 21 propostas, 184 classificados, 83 pendências, 5.080 rastros |
| RN-64 | **R$ 15.396,77**, 118 origens; estorno elegível abatido, agosto fora da devolução |
| Mínimo | Retorno 0; seis CSVs idênticos em bytes aos de `saida/alvo-a1/` |
| A1–A5 | Todos os registros idênticos aos de `saida/alvo-a5/`, excluindo somente os novos IDs MERIDIANO:/PENDENCIA_MERIDIANO: |
| Determinismo | Seis CSVs e manifesto idênticos em duas pastas novas |
| Integridade | **101 arquivos oficiais/referências** com SHA-256 idêntico antes/depois, incluindo documentos, Context, data pack, data/raw e saídas anteriores |

O pacote completo agora produz resultados computacionais COMPLETO e retorno 0 no escopo alvo, conforme o agregado já aprovado em A1/D-13. Pendências de negócio continuam explícitas, inclusive D-10; esse status não equivale a ratificação financeira, liberação de pagamentos/notas nem conclusão de A7. Não foi acrescentada uma parte artificial para representar o aceite de projeto.

## Testes e validação de A6

**220 testes passaram**, sendo os 197 anteriores e 23 novos de A6. A suíte direcionada de A6 também passou. Casos: cp1252/UTF-8 com BOM, acentos, folhas SGML com/sem fechamento, FITID estável com outra ordem, FITID ausente/repetido/financeiramente conflitante, conflito entre meses, datas locais com horário/fração/fuso, sinal incompatível, valor inválido, precisão decimal, NAME como histórico, origem sem valor, conta proibida, metadados/regex inválidos, regras ambíguas, múltiplos OFX, arquivo truncado, status/moeda incompatível, fontes ausentes, adulteração de valor/FITID, rastro quebrado de cada banco preservando o outro, determinismo e preservação das fontes sintéticas.

O auditor `tests/auditoria_a6.py` usa HTMLParser da biblioteca padrão, sem importar tarvo. Relê os movimentos e FITIDs, confere encoding, identificação da conta, período, recorte, valores, sinais, regras, contas, datas, origens e cobertura. A conferência de classificação/origens de A5 foi reutilizada por banco; a leitura independente dos formatos permanece separada. Adulteração é rejeitada mesmo com hash da saída atualizado.

Na primeira execução completa houve um PermissionError/WinError 5 ao substituir o manifesto em um teste de repetição no Windows. O teste direcionado passou na repetição, e a suíte completa final passou sem publicação paralela de evidências. Não foi determinada a causa do bloqueio de arquivo nem alterado o mecanismo de publicação para ocultar a falha. Logs inicial e final foram mantidos.

| Cenário A6 com cópias isoladas | Aurora | Meridiano | Demais resultados | Auditor |
| --- | --- | --- | --- | --- |
| Pacote completo | COMPLETO | COMPLETO | Preservados | 0 |
| Sem Meridiano | COMPLETO | BLOQUEADO | Preservados | 0 |
| Sem Aurora | BLOQUEADO | COMPLETO | Preservados | 0 |
| Sem plano | BLOQUEADO | BLOQUEADO | A1–A4 preservados | 0 |
| Somente plano + Meridiano | BLOQUEADO | COMPLETO | Bloqueados pelas próprias fontes ausentes | 0 |
| OFX truncado | COMPLETO | BLOQUEADO | Preservados | 0 |

Casos parciais retornaram 2; auditor retorna 0 para confirmar o estado parcial esperado. Original algum foi editado: OFX truncado e remoções ocorreram exclusivamente em cópias próprias.

## Reprodução e evidências

Com o ambiente já instalado, usar um destino novo para preservar referências:

```powershell
.\.venv\Scripts\python.exe -m tarvo --dados Tarvo_Data_Pack_set2026 --saida saida/alvo-a6 --regras regras.toml --escopo alvo
.\.venv\Scripts\python.exe tests/validar_saida.py --dados Tarvo_Data_Pack_set2026 --saida saida/alvo-a6 --regras regras.toml --esperar COMPLETO --esperar-fechamento COMPLETO
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Ambos os primeiros comandos retornaram 0 com o pacote completo. Windows/Python 3.12.10, ambiente existente, execução instalada fora da raiz, sem PYTHONPATH/PYTHONHOME, chaves ou site-packages do usuário. Nenhuma dependência instalada. macOS/Linux não executados; usar `.venv/bin/python` nas instruções dessas plataformas.

Evidências: `saida/alvo-a6/` com os seis CSVs e manifesto; `.tmp/aceite-a6/resultado.json`, execução/repetição, auditorias, matriz e `integridade.json`; `.tmp/testes-a6-final.log` (220 aprovados), `.tmp/testes-a6-direcionados.log` e log inicial `.tmp/testes-a6.log`. Execução do pacote alvo observada em 1,768 segundo, sem garantia para outros volumes/ambientes. `git diff --check` sem erros de whitespace.

## Pendências e limite

D-10 continua aguardando confirmação financeira da natureza do ajuste; a decisão documentada do time de usar 50% não foi modificada. Atlas aguarda contrato; RN-64 permanece corrigida. A7 e extras não foram iniciados. Não houve ação em bancos, pagamento, contestação enviada, lançamento externo, emissão fiscal ou commit. Este aceite de etapa não encerra o aceite integrado do alvo.
