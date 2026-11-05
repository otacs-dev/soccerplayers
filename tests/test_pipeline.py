import warnings

import pandas as pd
import pytest
from scipy import stats

from run_pipeline import construir_indices


def test_construir_indices_agrega_por_minutos_e_registra_cobertura():
    jogadores = pd.DataFrame(
        {
            "player_id": [1, 2, 3],
            "nome": ["A", "B", "C"],
            "clube": ["Barcelona", "Liverpool", "Real Madrid"],
            "position": ["Defender"] * 3,
            "sub_position": ["Centre-Back"] * 3,
            "height_in_cm": [180, 190, 170],
        }
    )
    appearances = pd.DataFrame(
        {
            "player_id": [1, 1, 2, 3],
            "minutos": [900, 1800, 900, 900],
            "gols": [10, 20, 10, 5],
            "amostra_suficiente": [True] * 4,
        }
    )
    sofascore = pd.DataFrame(
        {
            "id_tm": [1, 2],
            "metrica": ["accuratePasses", "accuratePasses"],
            "valor": [10, 30],
            "minutos": [900, 900],
            "amostra_suficiente": [True, True],
        }
    )
    definicoes = {
        "indices": {
            "tecnico": {
                "variaveis": [
                    {"nome": "accuratePasses", "fonte": "sofascore", "peso": 2.0, "tipo": "por_90"},
                    {"nome": "goals", "fonte": "appearances", "peso": 1.0, "tipo": "por_90"},
                ]
            },
            "explosivo": {
                "variaveis": [
                    {"nome": "height_in_cm", "fonte": "players", "peso": 1.0, "tipo": "perfil"}
                ]
            },
        }
    }

    resultado = construir_indices(jogadores, appearances, sofascore, definicoes)
    indices = resultado["indices"].set_index("player_id")
    cobertura = resultado["cobertura"]

    gols_jogador_1 = resultado["percentis"].query("player_id == 1 and metrica == 'goals'")["valor"].iat[0]
    assert gols_jogador_1 == 1.0
    assert indices.loc[2, "indice_tecnico"] > indices.loc[1, "indice_tecnico"]
    assert indices.loc[3, "cobertura_tecnico"] == 0.5
    assert indices["indice_explosivo"].between(0, 100).all()
    assert cobertura.query("metrica == 'accuratePasses'")["n_jogadores"].iat[0] == 2


def _dados_com_metrica_compartilhada():
    ids = list(range(1, 9))
    jogadores = pd.DataFrame(
        {
            "player_id": ids,
            "nome": [f"Jogador {player_id}" for player_id in ids],
            "clube": ["Barcelona", "Liverpool", "Real Madrid", "Manchester City"] * 2,
            "position": ["Goalkeeper"] * 3 + ["Midfield"] * 5,
            "sub_position": ["Goalkeeper"] * 3
            + ["Defensive Midfield"] * 3
            + ["Attacking Midfield"] * 2,
            "height_in_cm": [185, 190, 188, 175, 180, 178, 172, 174],
        }
    )
    appearances = pd.DataFrame(
        {
            "player_id": ids,
            "minutos": [900] * len(ids),
            "gols": [0, 1, 2, 1, 3, 0, 2, 4],
            "amostra_suficiente": [True] * len(ids),
        }
    )
    sofascore = pd.DataFrame(
        {
            "id_tm": ids,
            "metrica": ["successfulDribbles"] * len(ids),
            "valor": [1, 2, 3, 4, 5, 6, 7, 8],
            "minutos": [900] * len(ids),
            "amostra_suficiente": [True] * len(ids),
        }
    )
    definicoes = {
        "indices": {
            "tecnico": {
                "variaveis": [
                    {"nome": "successfulDribbles", "fonte": "sofascore", "peso": 1.0},
                    {"nome": "goals", "fonte": "appearances", "peso": 1.0},
                ]
            },
            "explosivo": {
                "variaveis": [
                    {"nome": "successfulDribbles", "fonte": "sofascore", "peso": 1.0},
                    {"nome": "height_in_cm", "fonte": "players", "peso": 1.0},
                ]
            },
        }
    }
    return jogadores, appearances, sofascore, definicoes


def test_construir_indices_calcula_dribles_uma_vez_e_fallback_por_jogador():
    jogadores, appearances, sofascore, definicoes = _dados_com_metrica_compartilhada()

    with pytest.warns(RuntimeWarning, match="abaixo do mínimo recomendado"):
        resultado = construir_indices(jogadores, appearances, sofascore, definicoes)

    dribles = resultado["percentis"].query("metrica == 'successfulDribbles'")
    assert len(dribles) == 16
    assert dribles["player_id"].nunique() == 8
    assert dribles.groupby("player_id")["percentil_0_100"].nunique().eq(1).all()
    assert dribles["percentil_0_100"].max() == 100
    assert set(dribles.loc[dribles["position"] == "Goalkeeper", "grupo_percentil"]) == {
        "amplo:Goalkeeper"
    }
    assert set(dribles.loc[dribles["position"] == "Midfield", "grupo_percentil"]) == {
        "amplo:Midfield"
    }


def test_construir_indices_e_resultado_kruskal_independentes_da_ordem_das_linhas():
    jogadores, appearances, sofascore, definicoes = _dados_com_metrica_compartilhada()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        original = construir_indices(jogadores, appearances, sofascore, definicoes)
        embaralhado = construir_indices(
            jogadores.sample(frac=1, random_state=21),
            appearances.sample(frac=1, random_state=22),
            sofascore.sample(frac=1, random_state=23),
            definicoes,
        )

    colunas_indices = ["player_id", "indice_tecnico", "indice_explosivo"]
    original_indices = original["indices"][colunas_indices].sort_values("player_id").reset_index(drop=True)
    embaralhado_indices = embaralhado["indices"][colunas_indices].sort_values("player_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(original_indices, embaralhado_indices)

    for coluna in ("indice_tecnico", "indice_explosivo"):
        grupos_original = [
            grupo[coluna].dropna().to_numpy()
            for _, grupo in original["indices"].groupby("clube")
        ]
        grupos_embaralhados = [
            grupo[coluna].dropna().to_numpy()
            for _, grupo in embaralhado["indices"].groupby("clube")
        ]
        assert stats.kruskal(*grupos_original).statistic == stats.kruskal(*grupos_embaralhados).statistic
