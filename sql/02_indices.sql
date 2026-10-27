-- 1. Índice em passagem_base
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_passagem_base_clube')
BEGIN
    CREATE INDEX idx_passagem_base_clube 
        ON passagem_base (clube_id, formado_confirmado);
END;
GO

-- 2. Índice em estatistica_temporada (player_id, temporada)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_estatistica_jogador_temporada')
BEGIN
    CREATE INDEX idx_estatistica_jogador_temporada 
        ON estatistica_temporada (player_id, temporada);
END;
GO

-- 3. Índice em estatistica_temporada (metrica, fonte)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_estatistica_metrica')
BEGIN
    CREATE INDEX idx_estatistica_metrica 
        ON estatistica_temporada (metrica, fonte);
END;
GO

-- 4. Índice em jogador
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_jogador_estreia')
BEGIN
    CREATE INDEX idx_jogador_estreia 
        ON jogador (estreia);
END;
GO