"""Junções de fontes por identificador Transfermarkt validado."""

from __future__ import annotations

import pandas as pd

from src.tratamento.limpeza import normalizar_player_id


def integrar_por_id(
	base: pd.DataFrame,
	referencia: pd.DataFrame,
	*,
	id_col: str = "player_id",
	how: str = "left",
	validate: str = "many_to_one",
) -> pd.DataFrame:
	"""Junta duas tabelas pelo ID numérico, aplicando a validação de cardinalidade."""
	if not isinstance(base, pd.DataFrame) or not isinstance(referencia, pd.DataFrame):
		raise TypeError("base e referencia precisam ser pandas.DataFrame.")
	if id_col not in base.columns or id_col not in referencia.columns:
		raise KeyError(f"As duas tabelas precisam conter '{id_col}'.")
	if how not in {"left", "right", "inner", "outer"}:
		raise ValueError(f"Tipo de junção não suportado: {how}")

	esquerda = base.copy()
	direita = referencia.copy()
	esquerda[id_col] = normalizar_player_id(esquerda[id_col], nome_coluna=f"{id_col} (base)")
	direita[id_col] = normalizar_player_id(direita[id_col], nome_coluna=f"{id_col} (referência)")
	return esquerda.merge(
		direita,
		on=id_col,
		how=how,
		validate=validate,
		suffixes=("", "_referencia"),
	)