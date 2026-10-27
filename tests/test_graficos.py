import pandas as pd

from src.visual.graficos import (
    grafico_boxplots_indices,
    grafico_dispersao_indices,
    grafico_idade_estreia,
    grafico_revelados,
    preparar_dados_visualizacao,
)


def test_preparar_dados_junta_indice_posicao_e_idade_de_estreia():
    indices = pd.DataFrame(
        {
            "player_id": [1, 2],
            "nome": ["Jogador A", "Jogador B"],
            "clube": ["Barcelona", "Liverpool"],
            "indice_tecnico": [75, 60],
            "indice_explosivo": [65, 80],
        }
    )
    jogadores = pd.DataFrame(
        {
            "player_id": [1, 2],
            "position": ["Midfield", "Attack"],
            "date_of_birth": ["2000-01-01", "2000-01-01"],
            "estreia": ["2020-01-01", "2022-01-01"],
        }
    )

    out = preparar_dados_visualizacao(indices, jogadores)

    assert out["position"].tolist() == ["Midfield", "Attack"]
    assert out["idade_estreia"].iloc[0] < out["idade_estreia"].iloc[1]
    assert out["academia"].tolist() == ["Barcelona", "Liverpool"]


def test_graficos_representam_todos_os_indices_e_academias():
    df = pd.DataFrame(
        {
            "academia": ["Barcelona", "Barcelona", "Liverpool", "Liverpool"],
            "nome": ["A", "B", "C", "D"],
            "indice_tecnico": [70, 80, 60, 65],
            "indice_explosivo": [55, 75, 80, 85],
            "idade_estreia": [18, 19, 20, 21],
        }
    )

    dispersao = grafico_dispersao_indices(df)
    boxplots = grafico_boxplots_indices(df)
    revelados = grafico_revelados(df)
    idade = grafico_idade_estreia(df)

    assert len(dispersao.data) == 2
    assert list(dispersao.layout.xaxis.range) == [0, 100]
    assert list(dispersao.layout.yaxis.range) == [0, 100]
    assert len(boxplots.data) == 4
    assert sum(sum(trace.y) for trace in revelados.data) == 4
    assert len(idade.data) == 2
