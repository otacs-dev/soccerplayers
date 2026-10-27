import pandas as pd

from src.coleta.sofascore import ano_inicio, rotulo_temporada, ler_ids


def test_ano_inicio_converte_formatos_esperados():
    assert ano_inicio("2024") == 2024
    assert ano_inicio("24/25") == 2024
    assert ano_inicio("2023/24") == 2023
    assert ano_inicio("2024/25") == 2024


def test_rotulo_temporada_padroniza_ano_esportivo():
    assert rotulo_temporada("2024") == "2024/25"
    assert rotulo_temporada("2023/24") == "2023/24"


def test_ler_ids_retornou_df_com_colunas_necessarias():
    df = ler_ids()
    assert isinstance(df, pd.DataFrame)
    assert {"id_tm", "nome", "id_sofascore", "status"}.issubset(set(df.columns))
