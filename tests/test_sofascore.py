import pandas as pd
import pytest

from config import settings
from src.coleta.sofascore import importar_snapshot


def test_importa_snapshot_local_validado(tmp_path, monkeypatch):
	interim = tmp_path / "interim"
	monkeypatch.setattr(settings, "DIR_INTERIM", interim)
	entrada = tmp_path / "snapshot.csv"
	pd.DataFrame(
		[
			{
				"id_tm": 123,
				"temporada": "2023/24",
				"torneio": "League",
				"metrica": "accuratePasses",
				"valor": 500,
			}
		]
	).to_csv(entrada, index=False)

	saida = importar_snapshot(entrada, "profissionais")

	assert saida == interim / "sofascore_profissionais.csv"
	importado = pd.read_csv(saida)
	assert importado.loc[0, "id_tm"] == 123
	assert importado.loc[0, "fonte"] == "snapshot_local_autorizado"
	assert {"id_sofascore", "id_torneio"}.issubset(importado.columns)


@pytest.mark.parametrize(
	("colunas", "mensagem"),
	[
		(
			{"temporada": ["2023/24"], "torneio": ["League"], "metrica": ["goals"], "valor": [1]},
			"precisa conter as colunas",
		),
		(
			{
				"id_tm": [1, 1],
				"temporada": ["2023/24", "2023/24"],
				"torneio": ["League", "League"],
				"metrica": ["goals", "goals"],
				"valor": [1, 2],
			},
			"chaves jogador-temporada-torneio-métrica duplicadas",
		),
		(
			{
				"id_tm": ["id inválido"],
				"temporada": ["2023/24"],
				"torneio": ["League"],
				"metrica": ["goals"],
				"valor": [1],
			},
			"IDs Transfermarkt inteiros",
		),
	],
)
def test_importacao_rejeita_snapshot_invalido(tmp_path, colunas, mensagem):
	entrada = tmp_path / "invalido.csv"
	pd.DataFrame(colunas).to_csv(entrada, index=False)

	with pytest.raises(ValueError, match=mensagem):
		importar_snapshot(entrada)
