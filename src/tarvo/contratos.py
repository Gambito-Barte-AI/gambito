"""Layouts compartilhados pela coordenação, validação e exportação."""

ARQUIVOS = {
    "comissoes_por_lojista.csv": ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"],
    "divergencias_taxa.csv": ["id_saida", "cnpj", "linha_negocio", "ref_origem", "taxa_contratada_pct", "taxa_aplicada_pct", "diferenca_brl"],
    "notas_a_emitir.csv": ["id_saida", "tomador_cnpj", "tomador", "linha_negocio", "valor_brl", "discriminacao"],
    "lancamentos_classificados.csv": ["id_saida", "banco", "ref_origem", "data", "descricao", "valor", "conta_codigo", "metodo", "confianca"],
    "pendencias.csv": ["id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide",
                       "proximo_passo", "arquivo_origem", "linha_origem", "cnpj", "categoria", "natureza_valor"],
    "rastro.csv": ["id_saida", "arquivo_origem", "ref_origem", "valor",
                  "contrato_origem", "ref_contrato", "taxa_contratada_fracao",
                  "faixa", "regra", "vinculo_identidade", "tipo_lancamento", "data_base_taxa",
                  "ref_evento_original", "arquivo_evento_original", "natureza_valor"],
}
# Preserva os bytes/colunas do mínimo; extensões são publicadas apenas em --escopo alvo.
COLUNAS_MINIMO = {nome: list(colunas) for nome, colunas in ARQUIVOS.items()}
ARQUIVOS["pendencias.csv"] += ["valor_reportado_brl", "valor_solicitado_brl", "ref_original"]
ARQUIVOS["rastro.csv"] += ["ref_original", "linha_origem"]

RELATORIOS_ALVO = {"divergencias_taxa.csv", "notas_a_emitir.csv", "lancamentos_classificados.csv"}

CAMPOS_VALOR = {
    "comissoes_por_lojista.csv": "comissao_brl",
    "divergencias_taxa.csv": "diferenca_brl",
    "notas_a_emitir.csv": "valor_brl",
    "lancamentos_classificados.csv": "valor",
    "pendencias.csv": "valor_brl",
}
