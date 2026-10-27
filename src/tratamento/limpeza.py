"""Validação e normalização conservadora das tabelas de jogadores."""

from __future__ import annotations

import pandas as pd


def normalizar_player_id(valores: pd.Series, *, nome_coluna: str = "player_id") -> pd.Series:
	"""Converte IDs Transfermarkt em inteiros nullable e rejeita valores inválidos."""
	ids = pd.to_numeric(valores, errors="coerce")
	invalidos = ids.isna() | (ids % 1 != 0)
	if invalidos.any():
		amostras = valores[invalidos].astype(str).head(5).tolist()
		raise ValueError(f"'{nome_coluna}' contém IDs ausentes ou não inteiros: {amostras}")
	return ids.astype("Int64")


def limpar_base_jogadores(df: pd.DataFrame, id_col: str = "player_id") -> pd.DataFrame:
	"""Limpa espaços e marcadores nulos sem descartar linhas da amostra."""
	if not isinstance(df, pd.DataFrame):
		raise TypeError("df precisa ser um pandas.DataFrame.")
	if df.empty:
		raise ValueError("A base de jogadores está vazia.")

	dados = df.copy()
	dados.columns = [str(coluna).strip() for coluna in dados.columns]
	if dados.columns.duplicated().any():
		duplicadas = dados.columns[dados.columns.duplicated()].tolist()
		raise ValueError(f"A normalização dos nomes de colunas criou duplicatas: {duplicadas}")
	if id_col not in dados.columns:
		raise KeyError(f"Coluna obrigatória '{id_col}' não encontrada.")

	marcadores_nulos = {"", "nan", "none", "null", "na", "n/a"}
	for coluna in dados.select_dtypes(include=["object", "string"]).columns:
		dados[coluna] = dados[coluna].map(
			lambda valor: (
				pd.NA
				if isinstance(valor, str) and valor.strip().lower() in marcadores_nulos
				else valor.strip() if isinstance(valor, str) else valor
			)
		)

	dados[id_col] = normalizar_player_id(dados[id_col], nome_coluna=id_col)
	if dados[id_col].duplicated().any():
		duplicados = dados.loc[dados[id_col].duplicated(keep=False), id_col].astype(str).unique()
		raise ValueError(f"A base contém IDs duplicados: {duplicados[:5].tolist()}")
	return dados