"""Testes estatísticos não paramétricos para comparação entre academias.

Este módulo implementa a parte metodológica exigida no README:
- Kruskal-Wallis para diferença global entre as academias;
- Mann-Whitney U para pares com correção de Bonferroni;
- tamanho de efeito com diferença de medianas e rank-biserial.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

try:
	from scipy import stats
except ModuleNotFoundError as exc:  # pragma: no cover - depende da env do projeto
	raise ModuleNotFoundError(
		"SciPy não está instalado. Instale com `pip install scipy` antes de usar a análise estatística."
	) from exc


def _validar_colunas(df: pd.DataFrame, valor_col: str, grupo_col: str) -> pd.DataFrame:
	if not isinstance(df, pd.DataFrame):
		raise TypeError("df precisa ser um pandas.DataFrame.")
	if valor_col not in df.columns:
		raise KeyError(f"Coluna '{valor_col}' não encontrada.")
	if grupo_col not in df.columns:
		raise KeyError(f"Coluna '{grupo_col}' não encontrada.")

	dados = df[[grupo_col, valor_col]].copy()
	dados[valor_col] = pd.to_numeric(dados[valor_col], errors="coerce")
	dados = dados.dropna(subset=[grupo_col, valor_col])
	return dados


def kruskal_wallis(
	df: pd.DataFrame,
	valor_col: str,
	grupo_col: str = "academia",
	alpha: float = 0.05,
) -> dict:
	"""Executa o teste de Kruskal-Wallis para comparar as academias.

	Retorna um dicionário com estatística, valor-p, indicação de significância
	e o número de grupos comparados.
	"""
	dados = _validar_colunas(df, valor_col, grupo_col)
	grupos = [grupo[valor_col].to_numpy(dtype=float) for _, grupo in dados.groupby(grupo_col)]

	if len(grupos) < 2:
		return {
			"statistic": float("nan"),
			"p_value": float("nan"),
			"significativo": False,
			"alpha": alpha,
			"n_grupos": len(grupos),
			"grupos": sorted(dados[grupo_col].unique().tolist()),
		}

	statistic, p_value = stats.kruskal(*grupos)
	return {
		"statistic": float(statistic),
		"p_value": float(p_value),
		"significativo": bool(p_value < alpha),
		"alpha": float(alpha),
		"n_grupos": len(grupos),
		"grupos": sorted(dados[grupo_col].unique().tolist()),
	}


def tamanho_efeito(amostra_a, amostra_b) -> dict:
	"""Calcula diferença de medianas e rank-biserial para o efeito de uma comparação.

	A entrada pode ser lista, Series ou array NumPy. O sinal da diferença segue a
	regra: valores positivos indicam que a amostra A supera a amostra B.
	"""
	a = pd.to_numeric(pd.Series(amostra_a), errors="coerce").dropna().to_numpy(dtype=float)
	b = pd.to_numeric(pd.Series(amostra_b), errors="coerce").dropna().to_numpy(dtype=float)

	if a.size == 0 or b.size == 0:
		raise ValueError("As duas amostras precisam conter observações válidas.")

	median_diff = float(np.median(a) - np.median(b))

	combinado = np.concatenate([a, b])
	ranks = stats.rankdata(combinado, method="average")
	rank_sum_a = float(ranks[: a.size].sum())
	u_a = rank_sum_a - (a.size * (a.size + 1) / 2.0)
	rank_biserial = float((2 * u_a) / (a.size * b.size) - 1.0)

	return {
		"median_diff": median_diff,
		"rank_biserial": rank_biserial,
		"u_a": float(u_a),
		"n_a": int(a.size),
		"n_b": int(b.size),
	}


def mann_whitney_bonferroni(
	df: pd.DataFrame,
	valor_col: str,
	grupo_col: str = "academia",
	alpha: float = 0.05,
	alternative: str = "two-sided",
) -> pd.DataFrame:
	"""Compara cada par de grupos com teste Mann-Whitney U e correção de Bonferroni."""
	dados = _validar_colunas(df, valor_col, grupo_col)
	grupos = sorted(dados[grupo_col].unique().tolist())
	pares = list(combinations(grupos, 2))
	if not pares:
		return pd.DataFrame(
			columns=[
				"grupo_a",
				"grupo_b",
				"statistic",
				"p_value",
				"p_bonferroni",
				"significativo",
				"median_diff",
				"rank_biserial",
			]
		)

	numero_pares = len(pares)
	linhas = []

	for grupo_a, grupo_b in pares:
		amostra_a = dados.loc[dados[grupo_col] == grupo_a, valor_col].to_numpy(dtype=float)
		amostra_b = dados.loc[dados[grupo_col] == grupo_b, valor_col].to_numpy(dtype=float)

		statistic, p_value = stats.mannwhitneyu(amostra_a, amostra_b, alternative=alternative)
		p_bonferroni = min(1.0, p_value * numero_pares)
		efeito = tamanho_efeito(amostra_a, amostra_b)

		linhas.append(
			{
				"grupo_a": grupo_a,
				"grupo_b": grupo_b,
				"statistic": float(statistic),
				"p_value": float(p_value),
				"p_bonferroni": float(p_bonferroni),
				"significativo": bool(p_bonferroni < alpha),
				"median_diff": efeito["median_diff"],
				"rank_biserial": efeito["rank_biserial"],
			}
		)

	tabela = pd.DataFrame(linhas)
	return tabela.sort_values(["p_bonferroni", "grupo_a", "grupo_b"]).reset_index(drop=True)


def comparar_academias(
	df: pd.DataFrame,
	valor_col: str,
	grupo_col: str = "academia",
	alpha: float = 0.05,
) -> dict:
	"""Resumo geral da comparação entre academias: diferença global e por pares."""
	global_test = kruskal_wallis(df, valor_col, grupo_col=grupo_col, alpha=alpha)
	pares = mann_whitney_bonferroni(df, valor_col, grupo_col=grupo_col, alpha=alpha)

	return {
		"kruskal_wallis": global_test,
		"pares": pares,
		"ha_diferenca_global": bool(global_test["significativo"]),
		"ha_diferenca_entre_pares": bool((pares["significativo"]).any()) if not pares.empty else False,
		"alpha": float(alpha),
	}


__all__ = [
	"kruskal_wallis",
	"tamanho_efeito",
	"mann_whitney_bonferroni",
	"comparar_academias",
]
