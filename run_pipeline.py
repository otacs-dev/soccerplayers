"""Executa o pipeline analítico a partir da seleção manual validada.

Execute na raiz do projeto com ``python run_pipeline.py``. A seleção de jogadores
é a base revisada em data/processed/jogadores_validos.csv; geração de candidatos,
conferência manual e persistência SQL não fazem parte deste pipeline automático.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from config import settings
from src.analise.descritiva import descritiva_por_academia
from src.analise.testes import comparar_academias
from src.features.carreira import calcular_features_carreira
from src.tratamento.integracao import integrar_por_id
from src.tratamento.limpeza import limpar_base_jogadores
from src.tratamento.percentis import categoria_posicao
from src.tratamento.por90 import (
	ARQ_SOFASCORE,
	SAIDA_APPEARANCES,
	SAIDA_SOFASCORE,
	tabela_appearances,
	tabela_sofascore,
)
from src.visual.graficos import (
	grafico_boxplots_indices,
	grafico_dispersao_indices,
	grafico_idade_estreia,
	grafico_revelados,
	preparar_dados_visualizacao,
)


ARQ_INDICES = settings.DIR_PROCESSED / "indices_jogadores.csv"
ARQ_PERCENTIS = settings.DIR_PROCESSED / "percentis_metricas.csv"
ARQ_COBERTURA = settings.DIR_PROCESSED / "cobertura_metricas.csv"
ARQ_DESCRITIVA = settings.DIR_PROCESSED / "descritiva_academias.csv"
ARQ_KRUSKAL = settings.DIR_PROCESSED / "kruskal_wallis.csv"
ARQ_PARES = settings.DIR_PROCESSED / "mann_whitney_bonferroni.csv"
ARQ_CARREIRA = settings.DIR_PROCESSED / "carreira_jogadores.csv"
DIR_GRAFICOS = settings.RAIZ / "reports" / "graficos"
MIN_N_PERCENTIL_POSICAO = 5

MAPEAMENTO_APPEARANCES = {
	"goals": "gols",
	"assists": "assistencias",
}


def _id_inteiro(serie: pd.Series) -> pd.Series:
	return pd.to_numeric(serie, errors="coerce").astype("Int64")


def _dados_metrica(
	variavel: dict,
	jogadores: pd.DataFrame,
	appearances: pd.DataFrame,
	sofascore: pd.DataFrame,
) -> pd.DataFrame:
	nome = variavel["nome"]
	fonte = variavel["fonte"]

	if fonte == "players":
		if nome not in jogadores.columns:
			raise KeyError(f"Métrica de perfil '{nome}' não existe na base validada.")
		return jogadores[["player_id", nome]].rename(columns={nome: "valor"}).assign(metrica=nome)

	if fonte == "appearances":
		coluna = MAPEAMENTO_APPEARANCES.get(nome, nome)
		if coluna not in appearances.columns:
			raise KeyError(f"Métrica '{nome}' não existe em appearances padronizado ({coluna}).")
		base = appearances.copy()
		base["player_id"] = _id_inteiro(base["player_id"])
		base["minutos"] = pd.to_numeric(base["minutos"], errors="coerce")
		base["valor"] = pd.to_numeric(base[coluna], errors="coerce")
		if "amostra_suficiente" in base.columns:
			base = base[base["amostra_suficiente"].astype("boolean").fillna(False)]
		return _agregar_taxa(base, "player_id", nome)

	if fonte == "sofascore":
		if sofascore.empty:
			return pd.DataFrame(columns=["player_id", "valor", "metrica"])
		base = sofascore[sofascore["metrica"] == nome].copy()
		base["id_tm"] = _id_inteiro(base["id_tm"])
		base["minutos"] = pd.to_numeric(base["minutos"], errors="coerce")
		base["valor"] = pd.to_numeric(base["valor"], errors="coerce")
		if "amostra_suficiente" in base.columns:
			base = base[base["amostra_suficiente"].astype("boolean").fillna(False)]
		return _agregar_taxa(base.rename(columns={"id_tm": "player_id"}), "player_id", nome)

	raise ValueError(f"Fonte '{fonte}' não suportada para a métrica '{nome}'.")


def _agregar_taxa(base: pd.DataFrame, id_col: str, metrica: str) -> pd.DataFrame:
	base = base.dropna(subset=[id_col, "valor", "minutos"])
	base = base[base["minutos"] > 0]
	if base.empty:
		return pd.DataFrame(columns=["player_id", "valor", "metrica"])
	agregado = base.groupby(id_col, as_index=False).agg(valor_total=("valor", "sum"), minutos_total=("minutos", "sum"))
	agregado["valor"] = agregado["valor_total"] / agregado["minutos_total"] * 90
	return agregado.rename(columns={id_col: "player_id"})[["player_id", "valor"]].assign(metrica=metrica)


def construir_indices(
	jogadores: pd.DataFrame,
	appearances: pd.DataFrame,
	sofascore: pd.DataFrame,
	definicoes: dict | None = None,
) -> dict[str, pd.DataFrame]:
	"""Monta valores agregados, percentis por posição, índices ponderados e cobertura."""
	if definicoes is None:
		with open(settings.RAIZ / "config" / "metricas.yaml", encoding="utf-8") as arquivo:
			definicoes = yaml.safe_load(arquivo) or {}
	if jogadores.empty:
		raise ValueError("A base validada de jogadores está vazia.")
	if jogadores["player_id"].duplicated().any():
		raise ValueError("A base validada contém player_id duplicados.")

	base_jogadores = limpar_base_jogadores(jogadores)
	base_jogadores["categoria"] = base_jogadores.apply(
		lambda linha: categoria_posicao(linha.get("position", ""), linha.get("sub_position", "")), axis=1
	)

	registros_valores = []
	metadados = []
	for nome_indice, configuracao in definicoes.get("indices", {}).items():
		for variavel in configuracao.get("variaveis", []):
			metrica = variavel["nome"]
			valores = _dados_metrica(variavel, base_jogadores, appearances, sofascore)
			valores["player_id"] = _id_inteiro(valores["player_id"])
			valores["valor"] = pd.to_numeric(valores["valor"], errors="coerce")
			valores = valores.dropna(subset=["player_id", "valor"])
			valores["indice"] = nome_indice
			valores["peso"] = float(variavel.get("peso", 1.0))
			registros_valores.append(valores)
			metadados.append({"indice": nome_indice, "metrica": metrica, "peso": float(variavel.get("peso", 1.0))})

	if not registros_valores:
		raise ValueError("Nenhuma variável de índice foi definida em config/metricas.yaml.")
	valores_longos = pd.concat(registros_valores, ignore_index=True)
	valores_longos = integrar_por_id(
		valores_longos,
		base_jogadores[["player_id", "categoria", "position"]],
		how="left",
		validate="many_to_one",
	)

	percentis = []
	for metrica, grupo_metrica in valores_longos.groupby("metrica", sort=False):
		grupo_metrica = grupo_metrica.copy()
		grupo_metrica["grupo_percentil"] = grupo_metrica["categoria"]
		contagens = grupo_metrica.groupby("categoria")["player_id"].transform("count")
		usar_amplo = contagens < MIN_N_PERCENTIL_POSICAO
		grupo_metrica.loc[usar_amplo, "grupo_percentil"] = "amplo:" + grupo_metrica.loc[usar_amplo, "position"].astype(str)
		grupo_metrica["percentil_0_100"] = grupo_metrica.groupby("grupo_percentil")["valor"].rank(method="average", pct=True) * 100
		percentis.append(grupo_metrica)
	percentis_df = pd.concat(percentis, ignore_index=True)

	pesos = pd.DataFrame(metadados)
	percentis_df = percentis_df.merge(pesos, on=["indice", "metrica", "peso"], how="left", validate="many_to_one")
	percentis_df["contribuicao"] = percentis_df["percentil_0_100"] * percentis_df["peso"]
	agregado = percentis_df.groupby(["player_id", "indice"], as_index=False).agg(
		soma_ponderada=("contribuicao", "sum"), peso_disponivel=("peso", "sum"), metricas_validas=("metrica", "nunique")
	)
	agregado["valor_indice"] = agregado["soma_ponderada"] / agregado["peso_disponivel"]
	agregado["cobertura"] = agregado["metricas_validas"] / agregado["indice"].map(
		{nome: len(cfg.get("variaveis", [])) for nome, cfg in definicoes["indices"].items()}
	)
	indices_largos = agregado.pivot(index="player_id", columns="indice", values="valor_indice").rename(
		columns={"tecnico": "indice_tecnico", "explosivo": "indice_explosivo"}
	)
	cobertura_larga = agregado.pivot(index="player_id", columns="indice", values="cobertura").rename(
		columns={"tecnico": "cobertura_tecnico", "explosivo": "cobertura_explosivo"}
	)
	contagem_larga = agregado.pivot(index="player_id", columns="indice", values="metricas_validas").rename(
		columns={"tecnico": "n_metricas_tecnico", "explosivo": "n_metricas_explosivo"}
	)
	indices_df = base_jogadores.merge(indices_largos, left_on="player_id", right_index=True, how="left")
	indices_df = indices_df.merge(cobertura_larga, left_on="player_id", right_index=True, how="left")
	indices_df = indices_df.merge(contagem_larga, left_on="player_id", right_index=True, how="left")

	cobertura = (
		percentis_df.groupby(["indice", "metrica"], as_index=False)
		.agg(n_jogadores=("player_id", "nunique"), peso=("peso", "first"))
	)
	cobertura["n_amostra"] = len(base_jogadores)
	cobertura["proporcao_coberta"] = cobertura["n_jogadores"] / cobertura["n_amostra"]

	colunas_percentis = [
		"player_id", "nome", "clube", "position", "sub_position", "categoria", "indice", "metrica",
		"valor", "grupo_percentil", "percentil_0_100", "peso",
	]
	return {
		"indices": indices_df,
		"percentis": percentis_df[[coluna for coluna in colunas_percentis if coluna in percentis_df.columns]],
		"cobertura": cobertura,
	}


def _exigir_arquivo(caminho: Path, orientacao: str) -> None:
	if not caminho.exists():
		raise FileNotFoundError(f"Arquivo obrigatório ausente: {caminho}\n{orientacao}")


def executar_pipeline() -> dict[str, Path]:
	"""Executa padronização, índices, análise descritiva/inferencial e gráficos."""
	_exigir_arquivo(settings.ARQ_VALIDOS_FINAL, "Revise data/manual/jogadores_validos.csv e prepare data/processed/jogadores_validos.csv.")
	_exigir_arquivo(settings.ARQ_APPEARANCES, "Coloque appearances.csv em data/raw/.")
	_exigir_arquivo(ARQ_SOFASCORE, "Gere data/interim/sofascore_temporada.csv com src.coleta.sofascore coletar.")

	settings.DIR_INTERIM.mkdir(parents=True, exist_ok=True)
	settings.DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
	DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)
	validos = pd.read_csv(settings.ARQ_VALIDOS_FINAL, encoding="utf-8-sig")
	if "formado_confirmado" in validos and not validos["formado_confirmado"].astype(str).str.lower().eq("sim").all():
		raise ValueError("A base final contém jogadores sem formado_confirmado='sim'. Revise a seleção antes da análise.")

	appearances = tabela_appearances(validos)
	appearances.to_csv(SAIDA_APPEARANCES, index=False, encoding="utf-8-sig")
	carreira = calcular_features_carreira(appearances, validos)
	carreira.to_csv(ARQ_CARREIRA, index=False, encoding="utf-8-sig")
	sofascore = tabela_sofascore()
	if sofascore is None:
		raise FileNotFoundError(f"Não foi possível gerar dados Sofascore; esperado {ARQ_SOFASCORE}.")
	sofascore.to_csv(SAIDA_SOFASCORE, index=False, encoding="utf-8-sig")

	resultado = construir_indices(validos, appearances, sofascore)
	indices = resultado["indices"]
	if indices["indice_tecnico"].notna().sum() < 2 or indices["indice_explosivo"].notna().sum() < 2:
		raise ValueError("Dados insuficientes para construir os dois índices e comparar academias.")
	indices.to_csv(ARQ_INDICES, index=False, encoding="utf-8-sig")
	resultado["percentis"].to_csv(ARQ_PERCENTIS, index=False, encoding="utf-8-sig")
	resultado["cobertura"].to_csv(ARQ_COBERTURA, index=False, encoding="utf-8-sig")

	descritivas = []
	kruskal = []
	pares = []
	for indice in ("indice_tecnico", "indice_explosivo"):
		descritiva = descritiva_por_academia(indices, metricas=[indice], academia_col="clube", posicao_col="categoria")
		descritivas.append(descritiva["metricas"])
		comparacao = comparar_academias(indices, indice, grupo_col="clube")
		kruskal.append({"metrica": indice, **{chave: valor for chave, valor in comparacao["kruskal_wallis"].items() if chave != "grupos"}})
		pares.append(comparacao["pares"].assign(metrica=indice))
	pd.concat(descritivas, ignore_index=True).to_csv(ARQ_DESCRITIVA, index=False, encoding="utf-8-sig")
	pd.DataFrame(kruskal).to_csv(ARQ_KRUSKAL, index=False, encoding="utf-8-sig")
	pd.concat(pares, ignore_index=True).to_csv(ARQ_PARES, index=False, encoding="utf-8-sig")

	base_visual = preparar_dados_visualizacao(indices, validos)
	figuras = {
		"dispersao_tecnico_explosivo": grafico_dispersao_indices(base_visual),
		"boxplots_indices": grafico_boxplots_indices(base_visual),
		"jogadores_revelados": grafico_revelados(base_visual),
	}
	if "idade_estreia" in base_visual and base_visual["idade_estreia"].notna().any():
		figuras["idade_estreia"] = grafico_idade_estreia(base_visual)
	for nome, figura in figuras.items():
		figura.write_image(DIR_GRAFICOS / f"{nome}.png", format="png", width=1400, scale=2)

	return {
		"indices": ARQ_INDICES,
		"percentis": ARQ_PERCENTIS,
		"cobertura": ARQ_COBERTURA,
		"descritiva": ARQ_DESCRITIVA,
		"kruskal": ARQ_KRUSKAL,
		"pares": ARQ_PARES,
		"carreira": ARQ_CARREIRA,
		"graficos": DIR_GRAFICOS,
	}


def main() -> None:
	parser = argparse.ArgumentParser(description="Executa o pipeline analítico de formação de jogadores.")
	parser.parse_args()
	try:
		artefatos = executar_pipeline()
	except (FileNotFoundError, KeyError, ValueError) as erro:
		parser.exit(1, f"Erro no pipeline: {erro}\n")

	print("Pipeline concluído. Artefatos gerados:")
	for nome, caminho in artefatos.items():
		print(f"- {nome}: {caminho.relative_to(settings.RAIZ)}")
	print("Dashboard: execute `streamlit run src/visual/dashboard.py` na raiz do projeto.")


if __name__ == "__main__":
	main()
