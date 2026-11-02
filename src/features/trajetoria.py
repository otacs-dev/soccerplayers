"""Resumo transparente de temporadas de formação documentadas."""

from __future__ import annotations

import pandas as pd

from src.tratamento.integracao import integrar_por_id
from src.tratamento.limpeza import normalizar_player_id


def resumir_trajetoria(
	temporadas: pd.DataFrame,
	jogadores: pd.DataFrame | None = None,
) -> pd.DataFrame:
	"""Resume temporadas observadas, sem presumir continuidade em lacunas da fonte."""
	if not isinstance(temporadas, pd.DataFrame):
		raise TypeError("temporadas precisa ser um pandas.DataFrame.")
	requeridas = {"player_id", "academia", "ano_temporada"}
	faltantes = requeridas.difference(temporadas.columns)
	if faltantes:
		raise KeyError(f"Colunas ausentes em temporadas: {', '.join(sorted(faltantes))}")
	if temporadas.empty:
		raise ValueError("A tabela de temporadas de formação está vazia.")

	dados = temporadas.copy()
	dados["player_id"] = normalizar_player_id(dados["player_id"])
	dados["academia"] = dados["academia"].astype("string").str.strip()
	dados["ano_temporada"] = pd.to_numeric(dados["ano_temporada"], errors="coerce")
	if dados["academia"].isna().any() or dados["academia"].eq("").any():
		raise ValueError("Há temporadas sem nome de academia.")
	if dados["ano_temporada"].isna().any() or (dados["ano_temporada"] % 1 != 0).any():
		raise ValueError("'ano_temporada' precisa conter anos inteiros.")

	anos = dados.drop_duplicates(["player_id", "academia", "ano_temporada"])
	resumo = anos.groupby("player_id", as_index=False).agg(
		n_academias_documentadas=("academia", "nunique"),
		temporadas_formacao_observadas=("ano_temporada", "nunique"),
		primeiro_ano_formacao=("ano_temporada", "min"),
		ultimo_ano_formacao=("ano_temporada", "max"),
	)

	if jogadores is None:
		return resumo
	if not {"player_id", "clube"}.issubset(jogadores.columns):
		raise KeyError("A tabela jogadores precisa conter 'player_id' e 'clube'.")
	alvos = jogadores[["player_id", "clube"]].copy()
	alvos["player_id"] = normalizar_player_id(alvos["player_id"])
	alvos = alvos.rename(columns={"clube": "academia_alvo"})
	dados = integrar_por_id(dados, alvos, validate="many_to_one")
	alvo = dados[dados["academia"] == dados["academia_alvo"]]
	contagem_alvo = (
		alvo.drop_duplicates(["player_id", "ano_temporada"])
		.groupby("player_id")["ano_temporada"]
		.nunique()
		.rename("temporadas_academia_alvo_observadas")
	)
	resumo = resumo.merge(contagem_alvo, on="player_id", how="left", validate="one_to_one")
	resumo["temporadas_academia_alvo_observadas"] = (
		resumo["temporadas_academia_alvo_observadas"].fillna(0).astype("int64")
	)
	return resumo