"""
Configurações centrais do projeto.

Tudo que muda de uma rodada para outra (clubes, critérios, caminhos) fica aqui,
para os outros arquivos não terem nomes ou números fixos no código.

"""
from pathlib import Path

# --------------------------------------------------------------------------
# Caminhos (a raiz do projeto é a pasta acima de config/)
# --------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]

DIR_RAW = RAIZ / "data" / "raw"
DIR_INTERIM = RAIZ / "data" / "interim"
DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_MANUAL = RAIZ / "data" / "manual"

# Entradas do Kaggle (colocar em data/raw/)
ARQ_PLAYERS = DIR_RAW / "players.csv"
ARQ_APPEARANCES = DIR_RAW / "appearances.csv"
ARQ_TRANSFERS = DIR_RAW / "transfers.csv"

# Saídas
ARQ_CANDIDATOS = DIR_INTERIM / "candidatos_formados.csv"
ARQ_VALIDOS_MANUAL = DIR_MANUAL / "jogadores_validos.csv"
ARQ_VALIDOS_FINAL = DIR_PROCESSED / "jogadores_validos.csv"

# --------------------------------------------------------------------------
# Clubes (IDs do Transfermarkt, conferidos no players.csv)
# --------------------------------------------------------------------------
CLUBES = {
    131: "Barcelona",
    418: "Real Madrid",
    281: "Manchester City",
    31: "Liverpool",
}

# Como a base do próprio clube aparece em transfers.csv (coluna from_club_name).
# Um jogador que chegou ao time principal vindo de um desses nomes foi
# "promovido da base". Expressões regulares, com diferença entre maiúsculas.
PADROES_BASE = {
    131: r"Barcelona B|Barça|Juvenil|Barcelona U",
    418: r"Castilla|Real Madrid|RM ",
    281: r"Man City",
    31: r"Liverpool",
}

# --------------------------------------------------------------------------
# Critérios
# --------------------------------------------------------------------------
# 1) Lista AMPLA para conferência manual. Fica larga de propósito, porque a
#    conferência humana vai eliminar falsos positivos (ex.: quem veio da base
#    de outro clube). Assim, mudar o corte final depois não obriga a conferir
#    tudo de novo.
CAND_ESTREIA_DESDE = "2013-01-01"
CAND_MIN_MINUTOS = 500

# 2) Critério FINAL, aplicado só aos jogadores confirmados como formados.
#    Ajustes aqui afetam apenas a amostra final; a conferência manual continua
#    válida e não precisa ser refeita.
#
# Regras finais da amostra:
# - estreia no profissional a partir de 2016
# - 900 minutos ou mais no time principal
# - até 15 jogadores por academia, ordenados por minutos no time principal
# - se um clube cair abaixo de 6 jogadores, o script avisa e o estudo passa a
#   tratar essa comparação como pequena e com efeito mais relevante do que p-valor
ESTREIA_DESDE = "2016-01-01"
MIN_MINUTOS = 900
MAX_POR_CLUBE = 15  # os de mais minutos

# Abaixo disso o script avisa que o grupo ficou pequeno demais para testes
# Este valor é um limite de "alerta" e não um corte rígido do estudo.
MIN_RECOMENDADO_POR_CLUBE = 6

# O appearances.csv começa em julho de 2012: quem estreou antes aparece com
# estreia em 2012. Por isso cortes de estreia anteriores a 2013 não são confiáveis.
# O conjunto final validado do projeto tem 35 jogadores e a distribuição por academia
# não é perfeitamente equilibrada: Barcelona 15, Liverpool 8, Manchester City 7,
# Real Madrid 5. Por isso o limite de 6 jogadores é usado como alerta de viés de
# tamanho amostral e não como corte duro do estudo.
INICIO_COBERTURA = "2013-01-01"




