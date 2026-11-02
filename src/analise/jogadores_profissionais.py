"""Gera a base histórica dos jogadores com partidas pelos quatro clubes."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import settings


ARQ_SAIDA = settings.DIR_PROCESSED / "jogadores_profissionais.csv"
ARQ_INDICES_PROFISSIONAIS = settings.DIR_PROCESSED / "indices_profissionais.csv"
COLUNAS_APARICOES = [
	"player_id",
	"player_club_id",
	"game_id",
	"date",
	"player_name",
	"minutes_played",
]


def gerar_base_profissionais(
	arquivo_aparicoes: Path = settings.ARQ_APPEARANCES,
	arquivo_jogadores: Path = settings.ARQ_PLAYERS,
	arquivo_validos: Path = settings.ARQ_VALIDOS_FINAL,
	arquivo_indices: Path | None = None,
) -> pd.DataFrame:
	"""Agrega partidas observadas por jogador e clube, marcando só formação confirmada."""
	if arquivo_indices is None:
		arquivo_indices = (
			ARQ_INDICES_PROFISSIONAIS
			if ARQ_INDICES_PROFISSIONAIS.exists()
			else settings.DIR_PROCESSED / "indices_jogadores.csv"
		)
	for caminho in (arquivo_aparicoes, arquivo_jogadores, arquivo_validos, arquivo_indices):
		if not caminho.exists():
			raise FileNotFoundError(f"Arquivo obrigatório ausente: {caminho}")

	clubes_por_id = {identificador: nome for identificador, nome in settings.CLUBES.items()}
	aparicoes_selecionadas = []
	for parte in pd.read_csv(
		arquivo_aparicoes,
		usecols=COLUNAS_APARICOES,
		chunksize=250_000,
	):
		parte["player_club_id"] = pd.to_numeric(parte["player_club_id"], errors="coerce")
		parte = parte[parte["player_club_id"].isin(clubes_por_id)]
		if not parte.empty:
			aparicoes_selecionadas.append(parte)
	if not aparicoes_selecionadas:
		raise ValueError("Não foram encontradas aparições pelos quatro clubes configurados.")

	aparicoes = pd.concat(aparicoes_selecionadas, ignore_index=True)
	aparicoes["date"] = pd.to_datetime(aparicoes["date"], errors="coerce")
	aparicoes["minutes_played"] = pd.to_numeric(aparicoes["minutes_played"], errors="coerce").fillna(0)
	aparicoes["player_id"] = pd.to_numeric(aparicoes["player_id"], errors="coerce")
	aparicoes = aparicoes.dropna(subset=["player_id", "date"])
	aparicoes["ano"] = aparicoes["date"].dt.year
	agregados = (
		aparicoes.groupby(["player_id", "player_club_id"], as_index=False)
		.agg(
			nome=("player_name", "last"),
			ano_primeira_aparicao=("ano", "min"),
			ano_ultima_aparicao=("ano", "max"),
			jogos_profissionais=("game_id", "nunique"),
			minutos_profissionais=("minutes_played", "sum"),
		)
	)
	agregados["player_id"] = agregados["player_id"].astype("int64")
	agregados["player_club_id"] = agregados["player_club_id"].astype("int64")
	agregados["clube"] = agregados["player_club_id"].map(clubes_por_id)

	ids = set(agregados["player_id"])
	perfis = pd.read_csv(
		arquivo_jogadores,
		usecols=["player_id", "position", "sub_position", "date_of_birth", "url"],
	)
	perfis["player_id"] = pd.to_numeric(perfis["player_id"], errors="coerce")
	perfis = perfis[perfis["player_id"].isin(ids)].drop_duplicates("player_id")
	agregados = agregados.merge(perfis, on="player_id", how="left", validate="many_to_one")

	validos = pd.read_csv(
		arquivo_validos,
		usecols=["clube", "player_id", "formado_confirmado"],
		dtype={"clube": "string", "formado_confirmado": "string"},
	)
	validos["player_id"] = pd.to_numeric(validos["player_id"], errors="coerce")
	validos = validos[
		validos["formado_confirmado"].str.strip().str.lower().isin(["sim", "s", "yes"])
	][["clube", "player_id"]].drop_duplicates()
	validos["formacao_status"] = "confirmada"
	agregados = agregados.merge(
		validos[["clube", "player_id", "formacao_status"]],
		on=["clube", "player_id"],
		how="left",
		validate="one_to_one",
	)
	agregados["formacao_status"] = agregados["formacao_status"].fillna("nao_confirmada")

	arquivo_indices_profissionais = arquivo_indices
	colunas_indices = pd.read_csv(arquivo_indices_profissionais, nrows=0).columns
	chaves_indices = ["clube", "player_id"] if "clube" in colunas_indices else ["player_id"]
	colunas_cobertura = [
		coluna
		for coluna in ("cobertura_tecnico", "cobertura_explosivo")
		if coluna in colunas_indices
	]
	colunas_metricas = [
		coluna
		for coluna in ("n_metricas_tecnico", "n_metricas_explosivo")
		if coluna in colunas_indices
	]
	indices = pd.read_csv(
		arquivo_indices_profissionais,
		usecols=[
			*chaves_indices,
			"indice_tecnico",
			"indice_explosivo",
			*colunas_cobertura,
			*colunas_metricas,
		],
	)
	indices["player_id"] = pd.to_numeric(indices["player_id"], errors="coerce")
	agregados = agregados.merge(
		indices,
		on=chaves_indices,
		how="left",
		validate="many_to_one" if chaves_indices == ["player_id"] else "one_to_one",
	)
	agregados["universo_indices"] = (
		"coorte_profissional" if arquivo_indices_profissionais == ARQ_INDICES_PROFISSIONAIS
		else "amostra_validada"
	)

	colunas = [
		"player_id",
		"clube",
		"nome",
		"position",
		"sub_position",
		"date_of_birth",
		"ano_primeira_aparicao",
		"ano_ultima_aparicao",
		"jogos_profissionais",
		"minutos_profissionais",
		"formacao_status",
		"indice_tecnico",
		"indice_explosivo",
		*colunas_cobertura,
		*colunas_metricas,
		"universo_indices",
		"url",
	]
	resultado = agregados[colunas].sort_values(["clube", "nome"]).reset_index(drop=True)
	return resultado


def main() -> None:
	settings.DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
	dados = gerar_base_profissionais()
	dados.to_csv(ARQ_SAIDA, index=False, encoding="utf-8-sig")
	print(f"Base profissional salva em {ARQ_SAIDA.relative_to(settings.RAIZ)}")
	print(f"- vínculos jogador-clube: {len(dados)}")
	print(f"- jogadores com formação confirmada: {(dados['formacao_status'] == 'confirmada').sum()}")
	print(f"- jogadores com índice técnico: {dados['indice_tecnico'].notna().sum()}")
	print(f"- jogadores com índice explosivo: {dados['indice_explosivo'].notna().sum()}")
	for clube, quantidade in dados.groupby("clube").size().items():
		print(f"- {clube}: {quantidade}")


if __name__ == "__main__":
	main()
