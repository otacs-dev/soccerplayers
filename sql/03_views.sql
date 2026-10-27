DROP VIEW IF EXISTS vw_jogadores_com_indices;
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
    j.jogos_profissionais,
    pb.formado_confirmado,
    pb.fonte_conferencia,
    ij.indice_tecnico,
    ij.indice_explosivo,
    ij.cobertura_tecnico,
    ij.cobertura_explosivo,
    ij.n_metricas_tecnico,
    ij.n_metricas_explosivo
FROM jogador AS j
LEFT JOIN passagem_base AS pb
    ON pb.player_id = j.player_id AND pb.formado_confirmado = 1
LEFT JOIN clube AS c ON c.clube_id = pb.clube_id
LEFT JOIN indice_jogador AS ij ON ij.player_id = j.player_id;

DROP VIEW IF EXISTS vw_resumo_academia;
CREATE VIEW vw_resumo_academia AS
SELECT
    c.nome AS academia,
    COUNT(DISTINCT j.player_id) AS n_jogadores,
    ROUND(AVG(ij.indice_tecnico), 2) AS media_indice_tecnico,
    ROUND(AVG(ij.indice_explosivo), 2) AS media_indice_explosivo,
    ROUND(AVG(j.minutos_profissionais), 0) AS media_minutos_profissionais
FROM clube AS c
LEFT JOIN passagem_base AS pb
    ON pb.clube_id = c.clube_id AND pb.formado_confirmado = 1
LEFT JOIN jogador AS j ON j.player_id = pb.player_id
LEFT JOIN indice_jogador AS ij ON ij.player_id = j.player_id
GROUP BY c.clube_id, c.nome;

DROP VIEW IF EXISTS vw_estatisticas_por_temporada;
CREATE VIEW vw_estatisticas_por_temporada AS
SELECT
    e.player_id,
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

DROP VIEW IF EXISTS vw_resultados_academia;
CREATE VIEW vw_resultados_academia AS
SELECT
    d.academia,
    d.metrica,
    d.n,
    d.n_ausentes,
    d.mediana,
    d.q1,
    d.q3,
    k.statistic AS kruskal_statistic,
    k.p_value AS kruskal_p_value,
    k.significativo AS kruskal_significativo
FROM descritiva_academia AS d
LEFT JOIN teste_kruskal_wallis AS k ON k.metrica = d.metrica;

DROP VIEW IF EXISTS vw_metricas_jogador;
CREATE VIEW vw_metricas_jogador AS
SELECT
    p.player_id,
    j.nome AS jogador,
    c.nome AS academia,
    p.position,
    p.categoria,
    p.indice,
    p.metrica,
    p.valor,
    p.grupo_percentil,
    p.percentil_0_100,
    p.peso
FROM percentil_metrica AS p
JOIN jogador AS j ON j.player_id = p.player_id
LEFT JOIN passagem_base AS pb
    ON pb.player_id = j.player_id AND pb.formado_confirmado = 1
LEFT JOIN clube AS c ON c.clube_id = pb.clube_id;
