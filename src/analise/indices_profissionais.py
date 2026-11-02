"""Recalcula os índices técnico e explosivo para a coorte profissional histórica."""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import settings
from run_pipeline import construir_indices
from src.analise.jogadores_profissionais import ARQ_SAIDA, gerar_base_profissionais
from src.tratamento.por90 import MIN_MIN_TEMPORADA, tabela_sofascore


ARQ_INDICES = settings.DIR_PROCESSED / "indices_profissionais.csv"
ARQ_SOFA = settings.DIR_INTERIM / "sofascore_profissionais.csv"


def _agregar_appearances(ids: set[int]) -> pd.DataFrame:
	partes = []
	for parte in pd.read_csv(
		settings.ARQ_APPEARANCES,
		usecols=["player_id", "minutes_played", "goals", "assists"],
		chunksize=250_000,
	):
		parte["player_id"] = pd.to_numeric(parte["player_id"], errors="coerce")
		parte = parte[parte["player_id"].isin(ids)]
		if parte.empty:
			continue
		for coluna in ("minutes_played", "goals", "assists"):
			parte[coluna] = pd.to_numeric(parte[coluna], errors="coerce").fillna(0)
		partes.append(
			parte.groupby("player_id", as_index=False).agg(
				minutos=("minutes_played", "sum"),
				gols=("goals", "sum"),
				assistencias=("assists", "sum"),
			)
		)
	if not partes:
		return pd.DataFrame(columns=["player_id", "minutos", "gols", "assistencias", "amostra_suficiente"])
	agregado = (
		pd.concat(partes, ignore_index=True)
		.groupby("player_id", as_index=False)[["minutos", "gols", "assistencias"]]
		.sum()
	)
	agregado["amostra_suficiente"] = agregado["minutos"] >= MIN_MIN_TEMPORADA
	return agregado


def calcular_indices_profissionais() -> pd.DataFrame:
	"""Usa a mesma configuração de métricas, com percentis posicionais na coorte toda."""
	for caminho in (ARQ_SAIDA, ARQ_SOFA, settings.ARQ_PLAYERS, settings.ARQ_APPEARANCES):
		if not caminho.exists():
			raise FileNotFoundError(f"Arquivo obrigatório ausente: {caminho}")

	profissionais = pd.read_csv(ARQ_SAIDA, encoding="utf-8-sig")
	ids = set(pd.to_numeric(profissionais["player_id"], errors="coerce").dropna().astype(int))
	perfis = pd.read_csv(
		settings.ARQ_PLAYERS,
		usecols=[
			"player_id",
			"name",
			"position",
			"sub_position",
			"date_of_birth",
			"height_in_cm",
			"url",
		],
	)
	perfis["player_id"] = pd.to_numeric(perfis["player_id"], errors="coerce")
	perfis = perfis[perfis["player_id"].isin(ids)].drop_duplicates("player_id").rename(
		columns={"name": "nome"}
	)
	perfis["clube"] = "Coorte profissional"

	appearances = _agregar_appearances(ids)
	sofascore = tabela_sofascore(ARQ_SOFA)
	if sofascore is None:
		raise FileNotFoundError(f"Não foi possível ler as métricas Sofascore: {ARQ_SOFA}")

	resultado = construir_indices(
		perfis,
		appearances,
		sofascore,
	)
	indices = resultado["indices"]
	for indice, cobertura in (
		("indice_tecnico", "cobertura_tecnico"),
		("indice_explosivo", "cobertura_explosivo"),
	):
		indices.loc[indices[cobertura] < 0.5, indice] = np.nan

	colunas = [
		"player_id",
		"indice_tecnico",
		"indice_explosivo",
		"cobertura_tecnico",
		"cobertura_explosivo",
		"n_metricas_tecnico",
		"n_metricas_explosivo",
	]
	saida = indices[colunas].copy()
	settings.DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
	saida.to_csv(ARQ_INDICES, index=False, encoding="utf-8-sig")

	profissionais_atualizados = gerar_base_profissionais()
	profissionais_atualizados.to_csv(ARQ_SAIDA, index=False, encoding="utf-8-sig")
	return saida


def main() -> None:
	indices = calcular_indices_profissionais()
	print(f"Índices posicionais salvos em {ARQ_INDICES.relative_to(settings.RAIZ)}")
	print(f"- jogadores no universo de comparação: {len(indices)}")
	print(f"- com índice técnico (cobertura mínima de 50%): {indices['indice_tecnico'].notna().sum()}")
	print(f"- com índice explosivo (cobertura mínima de 50%): {indices['indice_explosivo'].notna().sum()}")
	print(f"- base do frontend atualizada: {ARQ_SAIDA.relative_to(settings.RAIZ)}")


if __name__ == "__main__":
	main()
