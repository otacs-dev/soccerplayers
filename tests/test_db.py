import csv
import sqlite3

from config import settings
from src.db import inicializar_banco


def _escrever_csv(caminho, colunas, linhas):
	caminho.parent.mkdir(parents=True, exist_ok=True)
	with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
		escritor = csv.DictWriter(arquivo, fieldnames=colunas)
		escritor.writeheader()
		escritor.writerows(linhas)


def test_inicializar_banco_carrega_jogadores_e_resultados_analiticos(tmp_path, monkeypatch):
	processados = tmp_path / "processed"
	interim = tmp_path / "interim"
	monkeypatch.setattr(settings, "DIR_PROCESSED", processados)
	monkeypatch.setattr(settings, "DIR_INTERIM", interim)

	jogadores = [
		{
			"player_id": player_id,
			"clube": clube,
			"nome": nome,
			"formado_confirmado": "sim",
			"minutos": 900,
			"jogos": 10,
		}
		for player_id, clube, nome in [(1, "Barcelona", "A"), (2, "Liverpool", "B")]
	]
	_escrever_csv(
		processados / "jogadores_validos.csv",
		["player_id", "clube", "nome", "formado_confirmado", "minutos", "jogos"],
		jogadores,
	)
	_escrever_csv(
		processados / "indices_jogadores.csv",
		["player_id", "indice_tecnico", "indice_explosivo"],
		[
			{"player_id": 1, "indice_tecnico": 80, "indice_explosivo": 60},
			{"player_id": 2, "indice_tecnico": 70, "indice_explosivo": 75},
		],
	)
	_escrever_csv(
		processados / "percentis_metricas.csv",
		[
			"player_id", "position", "categoria", "indice", "metrica",
			"valor", "grupo_percentil", "percentil_0_100", "peso",
		],
		[
			{
				"player_id": player_id,
				"position": "Midfield",
				"categoria": "meio_campista_defensivo_central",
				"indice": "tecnico",
				"metrica": "accuratePasses",
				"valor": value,
				"grupo_percentil": "meia",
				"percentil_0_100": value,
				"peso": 1,
			}
			for player_id, value in [(1, 80), (2, 70)]
		],
	)
	_escrever_csv(
		processados / "cobertura_metricas.csv",
		["indice", "metrica", "n_jogadores", "peso", "n_amostra", "proporcao_coberta"],
		[{"indice": "tecnico", "metrica": "accuratePasses", "n_jogadores": 2, "peso": 1, "n_amostra": 2, "proporcao_coberta": 1}],
	)
	_escrever_csv(
		processados / "descritiva_academias.csv",
		["academia", "metrica", "n", "n_ausentes", "mediana", "q1", "q3", "minimo", "maximo"],
		[
			{"academia": "Barcelona", "metrica": "indice_tecnico", "n": 1, "n_ausentes": 0, "mediana": 80, "q1": 80, "q3": 80, "minimo": 80, "maximo": 80},
			{"academia": "Liverpool", "metrica": "indice_tecnico", "n": 1, "n_ausentes": 0, "mediana": 70, "q1": 70, "q3": 70, "minimo": 70, "maximo": 70},
		],
	)
	_escrever_csv(
		processados / "kruskal_wallis.csv",
		["metrica", "statistic", "p_value", "significativo", "alpha", "n_grupos"],
		[{"metrica": "indice_tecnico", "statistic": 1, "p_value": 0.3, "significativo": "False", "alpha": 0.05, "n_grupos": 2}],
	)
	_escrever_csv(
		processados / "mann_whitney_bonferroni.csv",
		["grupo_a", "grupo_b", "statistic", "p_value", "p_bonferroni", "significativo", "median_diff", "rank_biserial", "metrica"],
		[{"grupo_a": "Barcelona", "grupo_b": "Liverpool", "statistic": 1, "p_value": 0.5, "p_bonferroni": 0.5, "significativo": "False", "median_diff": 10, "rank_biserial": 0, "metrica": "indice_tecnico"}],
	)
	_escrever_csv(
		processados / "carreira_jogadores.csv",
		["player_id", "temporadas_com_aparicoes", "jogos_profissionais", "minutos_profissionais", "gols_profissionais", "assistencias_profissionais", "idade_estreia"],
		[
			{"player_id": player_id, "temporadas_com_aparicoes": 2, "jogos_profissionais": 10, "minutos_profissionais": 900, "gols_profissionais": 1, "assistencias_profissionais": 1, "idade_estreia": 18}
			for player_id in (1, 2)
		],
	)
	_escrever_csv(
		interim / "por90_appearances.csv",
		["player_id", "temporada", "torneio", "minutos", "gols", "assistencias", "amarelos", "vermelhos", "gols_por90", "assistencias_por90", "amarelos_por90", "vermelhos_por90", "amostra_suficiente"],
		[{"player_id": 1, "temporada": "2023/24", "torneio": "", "minutos": 900, "gols": 1, "assistencias": 1, "amarelos": 0, "vermelhos": 0, "gols_por90": 0.1, "assistencias_por90": 0.1, "amarelos_por90": 0, "vermelhos_por90": 0, "amostra_suficiente": "True"}],
	)
	_escrever_csv(
		interim / "por90_sofascore.csv",
		["id_tm", "temporada", "torneio", "metrica", "valor", "minutos", "valor_por90", "amostra_suficiente"],
		[{"id_tm": 2, "temporada": "2023/24", "torneio": "League", "metrica": "accuratePasses", "valor": 10, "minutos": 900, "valor_por90": 10, "amostra_suficiente": "True"}],
	)

	banco = tmp_path / "database.sqlite3"
	contagens = inicializar_banco(banco)

	assert contagens == {
		"academias": 4,
		"jogadores": 2,
		"indices": 2,
		"percentis": 2,
		"cobertura": 1,
		"descritivas": 2,
		"testes_kruskal": 1,
		"testes_mann_whitney": 1,
		"carreira": 2,
		"estatisticas": 5,
	}
	with sqlite3.connect(banco) as conexao:
		assert conexao.execute("SELECT COUNT(*) FROM vw_jogadores_com_indices").fetchone()[0] == 2
		assert conexao.execute("SELECT COUNT(*) FROM vw_metricas_jogador").fetchone()[0] == 2
		assert conexao.execute("SELECT COUNT(*) FROM vw_resultados_academia").fetchone()[0] == 2
		assert conexao.execute("PRAGMA foreign_key_check").fetchall() == []
