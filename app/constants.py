"""Listas fixas usadas pelos formularios.

Mantenha aqui os valores que aparecem nos selects da tela de candidatos.
Se quiser tornar editavel, mover para a tabela list_options e ler do banco.
"""

INTERVIEWERS = ["Gabriela", "Erica", "Nayara"]

SCREENED_BY = [
    "Gabriela", "Erica", "Nayara", "Sarah",
    "Laryssa", "Sabrina", "D+1",
]

STAGES = [
    "Msg de Aprovacao",
    "Sem Retorno",
    "Desistiu",
    "Treinamento loja",
    "Corte/Processo",
    "Admissao",
    "Stand Caixa",
    "Stand Vendas",
    "Aguardando inauguracao",
    "Desistiu Treina.",
    "Dispensado",
    "Stand",
    "Enviado Fabricio",
    "Reprovado pelo Lucas",
    "Nao iniciou",
]

YES_NO = ["Sim", "Nao"]

POSITIVE_POINTS = [
    "Ambicao",
    "Comunicativo",
    "Treinabilidade",
    "Boa postura",
    "Objetivos Alinhados",
    "Historico",
]

NEGATIVE_POINTS = [
    "SD", "TX", "Instab. Emocional", "Postura ruim", "Questionador",
    "Objetivos nao alinhados", "Vendedor Mediano", "Baixa comunicacao",
    "Imaturo", "Politico", "Assistencialista", "Estrelinha",
    "Alta RT", "Historico Ruim", "Vitimista",
]

SCORE_OPTIONS = ["Sem nota", 1, 2, 3, 4, 5]

# Etapas que contam como perda nos relatorios
LOSS_STAGES = {
    "Sem Retorno", "Desistiu", "Corte/Processo", "Desistiu Treina.",
    "Dispensado", "Reprovado pelo Lucas", "Nao iniciou",
}

ADMISSION_STAGES = {"Admissao"}
