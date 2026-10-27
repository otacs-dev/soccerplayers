"""Características de carreira calculadas a partir de aparições observadas."""

from __future__ import annotations

import pandas as pd

from src.tratamento.integracao import integrar_por_id
from src.tratamento.limpeza import normalizar_player_id


COLUNAS_CONTAGEM = ("jogos", "minutos", "gols", "assistencias")


def calcular_features_carreira(
	aparicoes: pd.DataFrame,
	jogadores: pd.DataFrame | None = None,
) -> pd.DataFrame:
	"""Resume jogos observados por jogador; valores ausentes não viram zero."""
	if not isinstance(aparicoes, pd.DataFrame):
		raise TypeError("aparicoes precisa ser um pandas.DataFrame.")
	if aparicoes.empty:
		raise ValueError("A tabela de aparições está vazia.")
	requeridas = {"player_id", "temporada", *COLUNAS_CONTAGEM}
	faltantes = requeridas.difference(aparicoes.columns)
	if faltantes:
		raise KeyError(f"Colunas ausentes em aparicoes: {', '.join(sorted(faltantes))}")

	dados = aparicoes.copy()
	dados["player_id"] = normalizar_player_id(dados["player_id"])
	for coluna in COLUNAS_CONTAGEM:
		dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")

	agrupado = dados.groupby("player_id")
	resumo = agrupado["temporada"].nunique().rename("temporadas_com_aparicoes").to_frame()
	for coluna in COLUNAS_CONTAGEM:
		resumo[f"{coluna}_profissionais"] = agrupado[coluna].sum(min_count=1)
	resumo = resumo.reset_index()

	if jogadores is None:
		return resumo
	if "player_id" not in jogadores.columns:
		raise KeyError("A tabela jogadores precisa conter 'player_id'.")
	contexto = jogadores.copy()
	contexto["player_id"] = normalizar_player_id(contexto["player_id"])
	colunas_contexto = [
		coluna for coluna in ("player_id", "nome", "clube", "date_of_birth", "estreia")
		if coluna in contexto.columns
	]
	resumo = integrar_por_id(
		contexto[colunas_contexto],
		resumo,
		validate="one_to_one",
	)
	if {"date_of_birth", "estreia"}.issubset(resumo.columns):
		nascimento = pd.to_datetime(resumo["date_of_birth"], errors="coerce")
		estreia = pd.to_datetime(resumo["estreia"], errors="coerce")
		resumo["idade_estreia"] = (estreia - nascimento).dt.days / 365.2425
	return resumo