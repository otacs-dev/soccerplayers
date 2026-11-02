"""Normalização compartilhada para arquivos de formação obtidos manualmente."""

from __future__ import annotations

import re

import pandas as pd

from config import settings
from src.tratamento.limpeza import normalizar_player_id


_TEMPORADA = re.compile(r"^(?P<inicio>\d{4})(?:[/-]\d{2,4})?$")


def normalizar_temporadas(
	df: pd.DataFrame,
	*,
	fonte: str,
	incluir_competicao: bool = False,
) -> pd.DataFrame:
	"""Valida esquema comum e retorna uma linha por jogador, academia e temporada."""
	if not isinstance(df, pd.DataFrame):
		raise TypeError("df precisa ser um pandas.DataFrame.")
	dados = df.copy()
	dados.columns = [str(coluna).strip() for coluna in dados.columns]
	requeridas = {"player_id", "academia", "temporada"}
	if incluir_competicao:
		requeridas.add("competicao")
	faltantes = requeridas.difference(dados.columns)
	if faltantes:
		raise KeyError(f"Colunas obrigatórias ausentes: {', '.join(sorted(faltantes))}")
	if dados.empty:
		raise ValueError("O arquivo de temporadas está vazio.")

	dados["player_id"] = normalizar_player_id(dados["player_id"])
	dados["academia"] = dados["academia"].astype("string").str.strip()
	if dados["academia"].isna().any() or dados["academia"].eq("").any():
		raise ValueError("Há linhas sem nome de academia.")
	clubes_validos = set(settings.CLUBES.values())
	academias_desconhecidas = sorted(set(dados["academia"].dropna()) - clubes_validos)
	if academias_desconhecidas:
		raise ValueError(f"Academias fora do escopo atual: {academias_desconhecidas}")

	def ano_inicio(temporada: object) -> int:
		match = _TEMPORADA.fullmatch(str(temporada).strip())
		if not match:
			raise ValueError(f"Rótulo de temporada inválido: {temporada!r}")
		return int(match.group("inicio"))

	dados["ano_temporada"] = dados["temporada"].map(ano_inicio)
	dados["fonte"] = fonte
	if "url" not in dados:
		dados["url"] = pd.NA
	if incluir_competicao:
		dados["competicao"] = dados["competicao"].astype("string").str.strip()
		if dados["competicao"].isna().any() or dados["competicao"].eq("").any():
			raise ValueError("Há participações sem nome de competição.")
	colunas = ["player_id", "academia", "ano_temporada", "fonte", "url"]
	if incluir_competicao:
		colunas.append("competicao")
	return (
		dados[colunas]
		.drop_duplicates()
		.sort_values(["player_id", "ano_temporada", "academia"])
		.reset_index(drop=True)
	)
