# Momentos

> De 2 a 4 momentos que importaram. Para cada um: o que foi pedido, o que a IA devolveu e o que foi feito com isso.
> Pelo menos um momento em que a IA errou ou levou para o lugar errado.

## Momento 1 — Recorte antes do código

- **Pedido:** analisar a arquitetura sem implementar e depois consolidar novas regras de fechamento parcial.
- **Resposta da IA:** propôs monólito modular e ajustou a publicação por resultado, mantendo decisões financeiras pendentes.
- **O que fiz:** o usuário aprovou explicitamente a arquitetura e apenas a Entrega 1 antes de autorizar alterações.

## Momento 2 — Suposição incorreta sobre o ambiente

- **Pedido:** implementar e validar a Entrega 1.
- **Resposta da IA:** tentou criar o ambiente virtual com o diretório temporário padrão, mas o sandbox negou a gravação; a tentativa de instalar dependências pela rede também falhou.
- **O que fiz:** o agente ajustou o temporário para o workspace, validou inicialmente com o runtime disponível e depois concluiu a instalação no venv com acesso à rede autorizado pela revisão automática.

## Momento 3 — Identidade não autoriza contrato

- **Pedido:** implementar identidade, faixas e vigências, mantendo decisões financeiras pendentes.
- **Resposta da IA:** separou identidade histórica e contrato vigente, com vínculos explícitos e rastro de faixa/regra.
- **O que fiz:** o agente acrescentou testes que comprovam que a identificação de CNPJ na aba antiga não permite usar suas taxas, e que isenção confirmada não resolve D-08 sobre devolução.
