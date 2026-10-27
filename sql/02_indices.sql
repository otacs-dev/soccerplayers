CREATE INDEX IF NOT EXISTS idx_passagem_base_clube
    ON passagem_base (clube_id, formado_confirmado);

CREATE INDEX IF NOT EXISTS idx_estatistica_jogador_temporada
    ON estatistica_temporada (player_id, temporada);

CREATE INDEX IF NOT EXISTS idx_estatistica_metrica_fonte
    ON estatistica_temporada (metrica, fonte);

CREATE INDEX IF NOT EXISTS idx_jogador_estreia
    ON jogador (estreia);

CREATE INDEX IF NOT EXISTS idx_percentil_indice_metrica
    ON percentil_metrica (indice, metrica);

CREATE INDEX IF NOT EXISTS idx_mann_whitney_grupos
    ON teste_mann_whitney (grupo_a, grupo_b);
