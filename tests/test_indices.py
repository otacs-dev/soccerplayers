import pandas as pd

from src.features.indices import calcular_indices_jogador, agregador_media_percentis


def test_agregador_media_percentis_usa_media_ponderada():
    s = pd.Series([10, 30, 50], name="score")
    out = agregador_media_percentis(s, pesos=[1, 2, 3])
    assert out == 36.666666666666664


def test_calcular_indices_jogador_retorna_tecnico_explosivo():
    df = pd.DataFrame(
        {
            "player_id": [1, 1, 1, 1, 2, 2, 2, 2],
            "nome": ["A", "A", "A", "A", "B", "B", "B", "B"],
            "clube": ["Barcelona"] * 4 + ["Liverpool"] * 4,
            "position": ["Defender"] * 4 + ["Midfield"] * 4,
            "sub_position": ["Left-Back"] * 4 + ["Central Midfield"] * 4,
            "categoria": ["lateral"] * 4 + ["meio_campista_defensivo_central"] * 4,
            "percentil_0_100": [20, 60, 40, 80, 70, 90, 30, 50],
            "indice": ["tecnico", "tecnico", "explosivo", "explosivo", "tecnico", "tecnico", "explosivo", "explosivo"],
        }
    )

    out = calcular_indices_jogador(df)

    assert {"player_id", "nome", "clube", "indice_tecnico", "indice_explosivo"}.issubset(out.columns)
    assert out["indice_tecnico"].between(0, 100).all()
    assert out["indice_explosivo"].between(0, 100).all()
    assert len(out) == 2
