import pandas as pd

from src.analise.descritiva import descritiva_por_academia


def test_descritiva_calcula_quartis_e_medianas_por_academia():
    df = pd.DataFrame(
        {
            "clube": ["Barcelona", "Barcelona", "Liverpool", "Liverpool"],
            "position": ["Defender", "Midfield", "Defender", "Attack"],
            "player_id": [10, 11, 12, 13],
            "indice_tecnico": [40, 60, 70, 90],
            "indice_explosivo": [30, 50, 60, 80],
        }
    )

    resultado = descritiva_por_academia(df)
    resumo = resultado["metricas"]

    barcelona = resumo.query("academia == 'Barcelona' and metrica == 'indice_tecnico'").iloc[0]
    assert barcelona["n"] == 2
    assert barcelona["mediana"] == 50
    assert barcelona["q1"] == 45
    assert barcelona["q3"] == 55


def test_descritiva_calcula_contagens_e_proporcoes_posicionais():
    df = pd.DataFrame(
        {
            "academia": ["Barcelona", "Barcelona", "Barcelona", "Liverpool", "Liverpool"],
            "categoria": ["lateral", "lateral", "goleiro", "centroavante", None],
            "indice_tecnico": [40, 60, 50, 80, 90],
        }
    )

    posicoes = descritiva_por_academia(df)["posicoes"]
    barcelona_lateral = posicoes.query("academia == 'Barcelona' and posicao == 'lateral'").iloc[0]
    liverpool = posicoes.query("academia == 'Liverpool'").iloc[0]

    assert barcelona_lateral["n_posicao"] == 2
    assert barcelona_lateral["proporcao"] == 2 / 3
    assert liverpool["n_academia"] == 2
    assert liverpool["n_posicao_valida"] == 1
    assert liverpool["proporcao_total"] == 0.5


def test_descritiva_aceita_colunas_configuradas_e_nome_de_clube():
    df = pd.DataFrame(
        {
            "clube": ["Barcelona", "Liverpool"],
            "position": ["Defender", "Attack"],
            "score": [55, 75],
            "player_id": [101, 102],
        }
    )

    resultado = descritiva_por_academia(df, metricas=["score"])

    assert resultado["metricas"]["metrica"].unique().tolist() == ["score"]
    assert set(resultado["metricas"]["academia"]) == {"Barcelona", "Liverpool"}
