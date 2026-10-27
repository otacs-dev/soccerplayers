import pandas as pd

from src.analise.testes import kruskal_wallis, mann_whitney_bonferroni, tamanho_efeito


def test_kruskal_wallis_retorna_estatistica_e_pvalor():
    df = pd.DataFrame(
        {
            "academia": ["Barcelona"] * 6 + ["Real Madrid"] * 6 + ["Manchester City"] * 6 + ["Liverpool"] * 6,
            "indice_tecnico": [70, 72, 74, 76, 78, 80,
                               50, 52, 48, 54, 49, 51,
                               85, 86, 88, 90, 87, 89,
                               60, 61, 63, 62, 64, 65],
        }
    )

    out = kruskal_wallis(df, "indice_tecnico", "academia")

    assert "statistic" in out
    assert "p_value" in out
    assert "significativo" in out
    assert 0.0 <= out["p_value"] <= 1.0
    assert out["statistic"] > 0


def test_mann_whitney_bonferroni_retorna_pares_com_correcao():
    df = pd.DataFrame(
        {
            "academia": ["Barcelona"] * 6 + ["Real Madrid"] * 6 + ["Manchester City"] * 6 + ["Liverpool"] * 6,
            "indice_tecnico": [70, 72, 74, 76, 78, 80,
                               50, 52, 48, 54, 49, 51,
                               85, 86, 88, 90, 87, 89,
                               60, 61, 63, 62, 64, 65],
        }
    )

    out = mann_whitney_bonferroni(df, "indice_tecnico", "academia", alpha=0.05)

    assert {"grupo_a", "grupo_b", "p_value", "p_bonferroni", "significativo", "rank_biserial"}.issubset(out.columns)
    assert len(out) == 6
    assert out["p_bonferroni"].between(0, 1).all()


def test_tamanho_efeito_retorna_mediana_e_rank_biserial():
    res = tamanho_efeito([8, 9, 10, 11], [1, 2, 3, 4])

    assert {"median_diff", "rank_biserial"}.issubset(res)
    assert res["median_diff"] > 0
    assert -1 <= res["rank_biserial"] <= 1
