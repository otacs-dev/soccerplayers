CREATE TABLE IF NOT EXISTS clube (
    clube_id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE,
    pais TEXT NOT NULL DEFAULT 'Desconhecido'
);

CREATE TABLE IF NOT EXISTS jogador (
    player_id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    position TEXT,
    sub_position TEXT,
    date_of_birth TEXT,
    height_in_cm REAL CHECK (height_in_cm IS NULL OR height_in_cm > 0),
    estreia TEXT,
    minutos_profissionais INTEGER CHECK (minutos_profissionais IS NULL OR minutos_profissionais >= 0),
    jogos_profissionais INTEGER CHECK (jogos_profissionais IS NULL OR jogos_profissionais >= 0),
    url_perfil TEXT
);

CREATE TABLE IF NOT EXISTS passagem_base (
    passagem_id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES jogador(player_id) ON DELETE CASCADE,
    clube_id INTEGER NOT NULL REFERENCES clube(clube_id),
    inicio TEXT,
    fim TEXT,
    formado_confirmado INTEGER NOT NULL DEFAULT 0 CHECK (formado_confirmado IN (0, 1)),
    fonte_conferencia TEXT,
    UNIQUE (player_id, clube_id)
);

CREATE TABLE IF NOT EXISTS estatistica_temporada (
    estatistica_id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES jogador(player_id) ON DELETE CASCADE,
    temporada TEXT NOT NULL,
    torneio TEXT NOT NULL DEFAULT '',
    metrica TEXT NOT NULL,
    valor REAL,
    minutos REAL,
    valor_por90 REAL,
    amostra_suficiente INTEGER CHECK (amostra_suficiente IS NULL OR amostra_suficiente IN (0, 1)),
    fonte TEXT NOT NULL,
    UNIQUE (player_id, temporada, torneio, metrica, fonte)
);

CREATE TABLE IF NOT EXISTS indice_jogador (
    player_id INTEGER PRIMARY KEY REFERENCES jogador(player_id) ON DELETE CASCADE,
    indice_tecnico REAL CHECK (indice_tecnico IS NULL OR indice_tecnico BETWEEN 0 AND 100),
    indice_explosivo REAL CHECK (indice_explosivo IS NULL OR indice_explosivo BETWEEN 0 AND 100),
    cobertura_tecnico REAL CHECK (cobertura_tecnico IS NULL OR cobertura_tecnico BETWEEN 0 AND 1),
    cobertura_explosivo REAL CHECK (cobertura_explosivo IS NULL OR cobertura_explosivo BETWEEN 0 AND 1),
    n_metricas_tecnico INTEGER CHECK (n_metricas_tecnico IS NULL OR n_metricas_tecnico >= 0),
    n_metricas_explosivo INTEGER CHECK (n_metricas_explosivo IS NULL OR n_metricas_explosivo >= 0)
);

CREATE TABLE IF NOT EXISTS percentil_metrica (
    percentil_id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES jogador(player_id) ON DELETE CASCADE,
    position TEXT,
    categoria TEXT,
    indice TEXT NOT NULL,
    metrica TEXT NOT NULL,
    valor REAL,
    grupo_percentil TEXT,
    percentil_0_100 REAL CHECK (percentil_0_100 IS NULL OR percentil_0_100 BETWEEN 0 AND 100),
    peso REAL NOT NULL,
    UNIQUE (player_id, indice, metrica)
);

CREATE TABLE IF NOT EXISTS cobertura_metrica (
    indice TEXT NOT NULL,
    metrica TEXT NOT NULL,
    n_jogadores INTEGER NOT NULL CHECK (n_jogadores >= 0),
    peso REAL,
    n_amostra INTEGER NOT NULL CHECK (n_amostra >= 0),
    proporcao_coberta REAL CHECK (proporcao_coberta IS NULL OR proporcao_coberta BETWEEN 0 AND 1),
    PRIMARY KEY (indice, metrica)
);

CREATE TABLE IF NOT EXISTS descritiva_academia (
    academia TEXT NOT NULL REFERENCES clube(nome),
    metrica TEXT NOT NULL,
    n INTEGER NOT NULL CHECK (n >= 0),
    n_ausentes INTEGER NOT NULL CHECK (n_ausentes >= 0),
    mediana REAL,
    q1 REAL,
    q3 REAL,
    minimo REAL,
    maximo REAL,
    PRIMARY KEY (academia, metrica)
);

CREATE TABLE IF NOT EXISTS teste_kruskal_wallis (
    metrica TEXT PRIMARY KEY,
    statistic REAL,
    p_value REAL CHECK (p_value IS NULL OR p_value BETWEEN 0 AND 1),
    significativo INTEGER CHECK (significativo IS NULL OR significativo IN (0, 1)),
    alpha REAL CHECK (alpha IS NULL OR alpha BETWEEN 0 AND 1),
    n_grupos INTEGER CHECK (n_grupos IS NULL OR n_grupos >= 0)
);

CREATE TABLE IF NOT EXISTS teste_mann_whitney (
    metrica TEXT NOT NULL,
    grupo_a TEXT NOT NULL REFERENCES clube(nome),
    grupo_b TEXT NOT NULL REFERENCES clube(nome),
    statistic REAL,
    p_value REAL CHECK (p_value IS NULL OR p_value BETWEEN 0 AND 1),
    p_bonferroni REAL CHECK (p_bonferroni IS NULL OR p_bonferroni BETWEEN 0 AND 1),
    significativo INTEGER CHECK (significativo IS NULL OR significativo IN (0, 1)),
    median_diff REAL,
    rank_biserial REAL CHECK (rank_biserial IS NULL OR rank_biserial BETWEEN -1 AND 1),
    PRIMARY KEY (metrica, grupo_a, grupo_b)
);

CREATE TABLE IF NOT EXISTS carreira_jogador (
    player_id INTEGER PRIMARY KEY REFERENCES jogador(player_id) ON DELETE CASCADE,
    temporadas_com_aparicoes INTEGER CHECK (temporadas_com_aparicoes IS NULL OR temporadas_com_aparicoes >= 0),
    jogos_profissionais INTEGER CHECK (jogos_profissionais IS NULL OR jogos_profissionais >= 0),
    minutos_profissionais REAL CHECK (minutos_profissionais IS NULL OR minutos_profissionais >= 0),
    gols_profissionais REAL CHECK (gols_profissionais IS NULL OR gols_profissionais >= 0),
    assistencias_profissionais REAL CHECK (assistencias_profissionais IS NULL OR assistencias_profissionais >= 0),
    idade_estreia REAL CHECK (idade_estreia IS NULL OR idade_estreia >= 0)
);
