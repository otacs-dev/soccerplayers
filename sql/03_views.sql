-- 1. View: vw_jogadores_com_indices
DROP VIEW IF EXISTS vw_jogadores_com_indices;
GO

CREATE VIEW vw_jogadores_com_indices AS
SELECT
    j.player_id,
    j.nome,
    c.nome AS academia,
    j.position,
    j.sub_position,
    j.date_of_birth,
    j.estreia,
    j.minutos_profissionais,
    pb.formado_confirmado,
    ij.indice_tecnico,
    ij.indice_explosivo,
    ij.cobertura_tecnico,
    ij.cobertura_explosivo
FROM jogador AS j
LEFT JOIN passagem_base AS pb
    ON pb.player_id = j.player_id AND pb.formado_confirmado = 1
LEFT JOIN clube AS c ON c.clube_id = pb.clube_id
LEFT JOIN indice_jogador AS ij ON ij.player_id = j.player_id;
GO

-- 2. View: vw_resumo_academia
DROP VIEW IF EXISTS vw_resumo_academia;
GO

CREATE VIEW vw_resumo_academia AS
SELECT
    c.nome AS academia,
    COUNT(DISTINCT j.player_id) AS n_jogadores,
    ROUND(AVG(CAST(ij.indice_tecnico AS FLOAT)), 2) AS media_indice_tecnico,
    ROUND(AVG(CAST(ij.indice_explosivo AS FLOAT)), 2) AS media_indice_explosivo,
    ROUND(AVG(CAST(j.minutos_profissionais AS FLOAT)), 0) AS media_minutos_profissionais
FROM clube AS c
LEFT JOIN passagem_base AS pb
    ON pb.clube_id = c.clube_id AND pb.formado_confirmado = 1
LEFT JOIN jogador AS j ON j.player_id = pb.player_id
LEFT JOIN indice_jogador AS ij ON ij.player_id = j.player_id
GROUP BY c.clube_id, c.nome;
GO

-- 3. View: vw_estatisticas_por_temporada
DROP VIEW IF EXISTS vw_estatisticas_por_temporada;
GO

CREATE VIEW vw_estatisticas_por_temporada AS
SELECT
    j.nome AS jogador,
    c.nome AS academia,
    e.temporada,
    e.torneio,
    e.metrica,
    e.valor,
    e.minutos,
    e.valor_por90,
    e.amostra_suficiente,
    e.fonte
FROM estatistica_temporada AS e
JOIN jogador AS j ON j.player_id = e.player_id
LEFT JOIN passagem_base AS pb
    ON pb.player_id = j.player_id AND pb.formado_confirmado = 1
LEFT JOIN clube AS c ON c.clube_id = pb.clube_id;
GO