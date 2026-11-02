"""Correlação exploratória de Spearman entre trajetória e carreira."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from scipy import stats

from src.tratamento.integracao import integrar_por_id


def correlacionar_trajetoria_carreira(
	trajetoria: pd.DataFrame,
	carreira: pd.DataFrame,
	*,
	variaveis_trajetoria: Sequence[str] = ("temporadas_formacao_observadas",),
	indicadores_carreira: Sequence[str] = (
		"idade_estreia",
		"jogos_profissionais",
		"minutos_profissionais",
		"gols_profissionais",
		"assistencias_profissionais",
	),
	minimo_observacoes: int = 5,
	alpha: float = 0.05,
) -> pd.DataFrame:
	"""Calcula rho e p-valor bicaudal; ajusta os p-valores por Bonferroni."""
	if minimo_observacoes < 3:
		raise ValueError("minimo_observacoes deve ser pelo menos 3.")
	if not 0 < alpha < 1:
		raise ValueError("alpha deve estar entre 0 e 1.")
	if "player_id" not in trajetoria.columns or "player_id" not in carreira.columns:
		raise KeyError("As duas tabelas precisam conter 'player_id'.")
	if trajetoria["player_id"].duplicated().any() or carreira["player_id"].duplicated().any():
		raise ValueError("Cada tabela precisa conter no máximo uma linha por jogador.")

	variaveis_trajetoria = tuple(variaveis_trajetoria)
	indicadores_carreira = tuple(indicadores_carreira)
	if not variaveis_trajetoria or not indicadores_carreira:
		return pd.DataFrame(
			columns=["variavel_trajetoria", "indicador_carreira", "n", "rho", "p_value", "p_bonferroni", "significativo"]
		)
	if len(set(variaveis_trajetoria)) != len(variaveis_trajetoria):
		raise ValueError("variaveis_trajetoria não pode conter nomes duplicados.")
	if len(set(indicadores_carreira)) != len(indicadores_carreira):
		raise ValueError("indicadores_carreira não pode conter nomes duplicados.")
	for coluna in variaveis_trajetoria:
		if coluna not in trajetoria.columns:
			raise KeyError(f"Variável de trajetória não encontrada: '{coluna}'.")
	for coluna in indicadores_carreira:
		if coluna not in carreira.columns:
			raise KeyError(f"Indicador de carreira não encontrado: '{coluna}'.")

	esquerda = trajetoria[["player_id", *variaveis_trajetoria]].rename(
		columns={coluna: f"traj__{coluna}" for coluna in variaveis_trajetoria}
	)
	direita = carreira[["player_id", *indicadores_carreira]].rename(
		columns={coluna: f"car__{coluna}" for coluna in indicadores_carreira}
	)
	dados = integrar_por_id(esquerda, direita, validate="one_to_one")

	resultados = []
	for variavel in variaveis_trajetoria:
		for indicador in indicadores_carreira:
			x = pd.to_numeric(dados[f"traj__{variavel}"], errors="coerce")
			y = pd.to_numeric(dados[f"car__{indicador}"], errors="coerce")
			validos = pd.concat([x, y], axis=1).dropna()
			rho = p_value = float("nan")
			if (
				len(validos) >= minimo_observacoes
				and validos.iloc[:, 0].nunique() > 1
				and validos.iloc[:, 1].nunique() > 1
			):
				resultado = stats.spearmanr(validos.iloc[:, 0], validos.iloc[:, 1])
				rho, p_value = float(resultado.statistic), float(resultado.pvalue)
			resultados.append(
				{
					"variavel_trajetoria": variavel,
					"indicador_carreira": indicador,
					"n": int(len(validos)),
					"rho": rho,
					"p_value": p_value,
				}
			)

	saida = pd.DataFrame(resultados)
	n_testes = len(saida)
	saida["p_bonferroni"] = (saida["p_value"] * n_testes).clip(upper=1)
	saida["significativo"] = saida["p_bonferroni"].lt(alpha).fillna(False)
	return saida