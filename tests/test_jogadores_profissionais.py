import csv

import pandas as pd

from src.analise.jogadores_profissionais import gerar_base_profissionais


def _escrever_csv(caminho, colunas, linhas):
	with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
		escritor = csv.DictWriter(arquivo, fieldnames=colunas)
		escritor.writeheader()
		escritor.writerows(linhas)


def test_base_profissionais_agrega_clube_e_nao_inventa_formacao_ou_indices(tmp_path):
	aparicoes = tmp_path / "appearances.csv"
	players = tmp_path / "players.csv"
	validos = tmp_path / "jogadores_validos.csv"
	indices = tmp_path / "indices_jogadores.csv"
	_escrever_csv(
		aparicoes,
		["player_id", "player_club_id", "game_id", "date", "player_name", "minutes_played"],
		[
			{"player_id": 1, "player_club_id": 131, "game_id": 10, "date": "2019-08-01", "player_name": "A", "minutes_played": 90},
			{"player_id": 1, "player_club_id": 131, "game_id": 11, "date": "2021-08-01", "player_name": "A", "minutes_played": 75},
			{"player_id": 2, "player_club_id": 31, "game_id": 12, "date": "2020-08-01", "player_name": "B", "minutes_played": 60},
			{"player_id": 3, "player_club_id": 999, "game_id": 13, "date": "2022-08-01", "player_name": "C", "minutes_played": 90},
		],
	)
	_escrever_csv(
		players,
		["player_id", "position", "sub_position", "date_of_birth", "url"],
		[
			{"player_id": 1, "position": "Midfield", "sub_position": "Central Midfield", "date_of_birth": "2000-01-01", "url": "https://example.test/1"},
			{"player_id": 2, "position": "Attack", "sub_position": "Centre-Forward", "date_of_birth": "2001-02-02", "url": "https://example.test/2"},
		],
	)
	_escrever_csv(
		validos,
		["clube", "player_id", "formado_confirmado"],
		[{"clube": "Barcelona", "player_id": 1, "formado_confirmado": "sim"}],
	)
	_escrever_csv(
		indices,
		["clube", "player_id", "indice_tecnico", "indice_explosivo"],
		[{"clube": "Barcelona", "player_id": 1, "indice_tecnico": 75, "indice_explosivo": 60}],
	)

	resultado = gerar_base_profissionais(aparicoes, players, validos, indices).set_index("player_id")

	assert len(resultado) == 2
	assert resultado.loc[1, "jogos_profissionais"] == 2
	assert resultado.loc[1, "minutos_profissionais"] == 165
	assert resultado.loc[1, "ano_primeira_aparicao"] == 2019
	assert resultado.loc[1, "ano_ultima_aparicao"] == 2021
	assert resultado.loc[1, "formacao_status"] == "confirmada"
	assert resultado.loc[1, "indice_tecnico"] == 75
	assert resultado.loc[2, "formacao_status"] == "nao_confirmada"
	assert pd.isna(resultado.loc[2, "indice_tecnico"])
