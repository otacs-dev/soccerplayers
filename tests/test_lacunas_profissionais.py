import pandas as pd

from src.analise.lacunas_profissionais import construir_relatorio_lacunas


def test_relatorio_marca_metricas_ausentes_e_indices_por_jogador():
    coorte = pd.DataFrame(
        [
            {"player_id": 1, "nome": "A", "clube": "Barcelona", "position": "Midfield", "sub_position": "Central Midfield"},
            {"player_id": 2, "nome": "B", "clube": "Liverpool", "position": "Attack", "sub_position": "Centre-Forward"},
        ]
    )
    indices = pd.DataFrame(
        [
            {"player_id": 1, "indice_tecnico": 75, "indice_explosivo": 60, "cobertura_tecnico": 1.0, "cobertura_explosivo": 1.0},
            {"player_id": 2, "indice_tecnico": float("nan"), "indice_explosivo": 55, "cobertura_tecnico": 0.4, "cobertura_explosivo": 0.8},
        ]
    )

    resultado = construir_relatorio_lacunas(
        coorte,
        {"accuratePasses": "sofascore", "goals": "appearances"},
        {"accuratePasses": {1}, "goals": {1, 2}},
        indices,
        {1, 2},
    ).set_index("player_id")

    assert resultado.loc[1, "tem_snapshot_sofascore"]
    assert resultado.loc[1, "metricas_faltantes"] == ""
    assert resultado.loc[1, "n_metricas_faltantes"] == 0
    assert resultado.loc[1, "indice_tecnico_disponivel"]
    assert resultado.loc[2, "metricas_faltantes"] == "accuratePasses"
    assert resultado.loc[2, "n_metricas_faltantes"] == 1
    assert resultado.loc[2, "tem_snapshot_sofascore"]
    assert not resultado.loc[2, "tem_metrica_sofascore_configurada"]
    assert not resultado.loc[2, "indice_tecnico_disponivel"]
    assert resultado.loc[2, "indice_explosivo_disponivel"]
