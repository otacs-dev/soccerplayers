"""Estatísticas descritivas dos índices e posições por academia."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def _primeira_coluna(df: pd.DataFrame, candidatas: Sequence[str], papel: str) -> str:
	for coluna in candidatas:
		if coluna in df.columns:
			return coluna
	raise KeyError(f"Não foi encontrada uma coluna para {papel}. Esperado uma de: {', '.join(candidatas)}")


def descritiva_por_academia(
	df: pd.DataFrame,
	metricas: Sequence[str] | None = None,
	academia_col: str | None = None,
	posicao_col: str | None = None,
	id_col: str | None = None,
) -> dict[str, pd.DataFrame]:
	"""Gera tabelas descritivas de métricas e posições por academia.

	Por padrão, resume os índices técnico e explosivo quando disponíveis. A
	proporção posicional é informada tanto entre posições conhecidas quanto sobre
	todos os jogadores da academia, tornando explícita a presença de posições ausentes.
	Retorna ``{"metricas": ..., "posicoes": ...}`` para facilitar interpretação,
	exportação e visualização posteriores.
	"""
	if not isinstance(df, pd.DataFrame):
		raise TypeError("df precisa ser um pandas.DataFrame.")
	if df.empty:
		raise ValueError("df não pode estar vazio.")

	academia_col = academia_col or _primeira_coluna(df, ("academia", "clube"), "academia")
	posicao_col = posicao_col or _primeira_coluna(
		df, ("categoria", "position", "sub_position"), "posição"
	)
	if academia_col not in df.columns:
		raise KeyError(f"Coluna '{academia_col}' não encontrada.")
	if posicao_col not in df.columns:
		raise KeyError(f"Coluna '{posicao_col}' não encontrada.")
	if id_col is not None and id_col not in df.columns:
		raise KeyError(f"Coluna '{id_col}' não encontrada.")

	if metricas is None:
		metricas = [
			coluna
			for coluna in ("indice_tecnico", "indice_explosivo")
			if coluna in df.columns
		]
	else:
		metricas = list(metricas)
		faltantes = [coluna for coluna in metricas if coluna not in df.columns]
		if faltantes:
			raise KeyError(f"Métricas não encontradas: {', '.join(faltantes)}")

	dados = df.copy()
	dados = dados.dropna(subset=[academia_col])
	if id_col is not None:
		duplicados = dados[id_col].duplicated(keep=False) & dados[id_col].notna()
		if duplicados.any():
			raise ValueError("A entrada deve conter no máximo uma linha por jogador.")

	grupos = []
	for academia, grupo in dados.groupby(academia_col, sort=True, dropna=True):
		for metrica in metricas:
			valores = pd.to_numeric(grupo[metrica], errors="coerce")
			validos = valores.dropna()
			grupos.append(
				{
					"academia": academia,
					"metrica": metrica,
					"n": int(validos.size),
					"n_ausentes": int(valores.isna().sum()),
					"mediana": float(validos.median()) if not validos.empty else float("nan"),
					"q1": float(validos.quantile(0.25)) if not validos.empty else float("nan"),
					"q3": float(validos.quantile(0.75)) if not validos.empty else float("nan"),
					"minimo": float(validos.min()) if not validos.empty else float("nan"),
					"maximo": float(validos.max()) if not validos.empty else float("nan"),
				}
			)
	resumo_metricas = pd.DataFrame(
			grupos,
			columns=[
				"academia", "metrica", "n", "n_ausentes", "mediana", "q1", "q3", "minimo", "maximo"
			],
		)

	totais = dados.groupby(academia_col, sort=True).size().rename("n_academia")
	posicoes_validas = dados.dropna(subset=[posicao_col])
	contagens = (
		posicoes_validas.groupby([academia_col, posicao_col], sort=True)
		.size()
		.rename("n_posicao")
		.reset_index()
	)
	if contagens.empty:
		resumo_posicoes = pd.DataFrame(
			columns=["academia", "posicao", "n_posicao", "n_academia", "n_posicao_valida", "proporcao", "proporcao_total"]
		)
	else:
		contagens = contagens.rename(columns={academia_col: "academia", posicao_col: "posicao"})
		contagens["n_academia"] = contagens["academia"].map(totais).astype(int)
		contagens["n_posicao_valida"] = contagens["academia"].map(
			posicoes_validas.groupby(academia_col).size()
		).astype(int)
		contagens["proporcao"] = contagens["n_posicao"] / contagens["n_posicao_valida"]
		contagens["proporcao_total"] = contagens["n_posicao"] / contagens["n_academia"]
		resumo_posicoes = contagens[
			["academia", "posicao", "n_posicao", "n_academia", "n_posicao_valida", "proporcao", "proporcao_total"]
		]

	return {"metricas": resumo_metricas, "posicoes": resumo_posicoes.reset_index(drop=True)}


__all__ = ["descritiva_por_academia"]
