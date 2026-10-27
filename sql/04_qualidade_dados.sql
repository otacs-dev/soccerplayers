-- Cada consulta de inconsistência deve retornar zero linhas.

-- Jogadores sem academia confirmada.
SELECT j.player_id, j.nome
FROM jogador AS j
LEFT JOIN passagem_base AS pb
    ON pb.player_id = j.player_id AND pb.formado_confirmado = 1
WHERE pb.passagem_id IS NULL;

-- Formações duplicadas.
SELECT player_id, clube_id, COUNT(*) AS repeticoes
FROM passagem_base
GROUP BY player_id, clube_id
HAVING COUNT(*) > 1;

-- Índices fora das faixas permitidas.
SELECT player_id, indice_tecnico, indice_explosivo
FROM indice_jogador
WHERE (indice_tecnico IS NOT NULL AND indice_tecnico NOT BETWEEN 0 AND 100)
   OR (indice_explosivo IS NOT NULL AND indice_explosivo NOT BETWEEN 0 AND 100);

-- Percentis fora da faixa permitida.
SELECT percentil_id, player_id, indice, metrica, percentil_0_100
FROM percentil_metrica
WHERE percentil_0_100 IS NOT NULL AND percentil_0_100 NOT BETWEEN 0 AND 100;

-- Estatísticas sem jogador ou campos obrigatórios.
SELECT e.estatistica_id, e.player_id
FROM estatistica_temporada AS e
LEFT JOIN jogador AS j ON j.player_id = e.player_id
WHERE j.player_id IS NULL
   OR e.temporada = ''
   OR e.metrica = ''
   OR e.fonte = '';

-- Contagem geral das tabelas analíticas carregadas.
SELECT
    (SELECT COUNT(*) FROM clube) AS academias,
    (SELECT COUNT(*) FROM jogador) AS jogadores,
    (SELECT COUNT(*) FROM passagem_base WHERE formado_confirmado = 1) AS formacoes_confirmadas,
    (SELECT COUNT(*) FROM indice_jogador) AS jogadores_com_indices,
    (SELECT COUNT(*) FROM percentil_metrica) AS percentis,
    (SELECT COUNT(*) FROM estatistica_temporada) AS estatisticas_por_temporada;
