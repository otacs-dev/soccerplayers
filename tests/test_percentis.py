import pandas as pd

from src.tratamento.percentis import categoria_posicao, calcular_percentis_por_posicao


def test_categoria_posicao_resolve_sub_posicao():
    assert categoria_posicao("Defender", "Left-Back") == "lateral"
    assert categoria_posicao("Midfield", "Defensive Midfield") == "meio_campista_defensivo_central"
    assert categoria_posicao("Attack", "Centre-Forward") == "centroavante"
    assert categoria_posicao("Goalkeeper", "Goalkeeper") == "goleiro"


def test_calcular_percentis_por_posicao_retornam_escala_0_100():
    df = pd.DataFrame(
        {
            "position": ["Defender", "Defender", "Defender", "Defender", "Midfield"],
            "sub_position": ["Left-Back", "Left-Back", "Right-Back", "Centre-Back", "Central Midfield"],
            "temporada": ["2023/24"] * 5,
            "metrica": ["x"] * 5,
            "valor_por90": [1.0, 2.0, 3.0, 4.0, 10.0],
        }
    )

    out = calcular_percentis_por_posicao(df, "valor_por90", metrica_col="metrica")

    assert set(out.columns) >= {"categoria", "valor_por90", "percentil_0_100"}
    assert out["percentil_0_100"].between(0, 100).all()
    assert out.loc[out["valor_por90"] == 4.0, "percentil_0_100"].iat[0] > 75


def test_calcular_percentis_por_posicao_trata_amostra_pequena():
    df = pd.DataFrame(
        {
            "position": ["Midfield", "Midfield"],
            "sub_position": ["Defensive Midfield", "Defensive Midfield"],
            "temporada": ["2023/24", "2023/24"],
            "metrica": ["x", "x"],
            "valor_por90": [1.0, 2.0],
        }
    )

    out = calcular_percentis_por_posicao(df, "valor_por90", metrica_col="metrica")
    assert out["percentil_0_100"].notna().all()
