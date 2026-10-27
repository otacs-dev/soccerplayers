import pandas as pd

from config import settings
from src.tratamento.por90 import por90, temporada_de


def test_temporada_de_usa_ano_esportivo():
    assert temporada_de("2024-03-10") == "2023/24"
    assert temporada_de("2023-09-01") == "2023/24"
    assert temporada_de("2022-07-01") == "2022/23"


def test_por90_calcula_valor_ajustado_por_minutos():
    assert por90(9, 450) == 1.8
    assert por90(9, 200) is pd.NA or pd.isna(por90(9, 200))


def test_config_tem_minimo_temporada_definido():
    assert hasattr(settings, "MIN_MIN_TEMPORADA")
    assert settings.MIN_MIN_TEMPORADA >= 400
