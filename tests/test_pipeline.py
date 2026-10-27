import pandas as pd

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
