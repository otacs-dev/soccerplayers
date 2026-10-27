"""Dashboard Streamlit da análise comparativa de academias.

Execute na raiz do projeto com ``streamlit run src/visual/dashboard.py``.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import settings
from src.visual.graficos import (
	grafico_boxplots_indices,
	grafico_dispersao_indices,
	grafico_idade_estreia,
	grafico_revelados,
	preparar_dados_visualizacao,
)


ARQUIVO_INDICES = settings.DIR_PROCESSED / "indices_jogadores.csv"
ARQUIVO_JOGADORES = settings.ARQ_VALIDOS_FINAL


def _ler_indices(arquivo_carregado) -> pd.DataFrame | None:
	if arquivo_carregado is not None:
		return pd.read_csv(arquivo_carregado)
	if ARQUIVO_INDICES.exists():
		return pd.read_csv(ARQUIVO_INDICES)
	return None


def main() -> None:
	st.set_page_config(page_title="Formação de Jogadores", page_icon="⚽", layout="wide")
	st.markdown(
		"""
		<style>
		:root { --ink: #20332f; --green: #167c63; --line: #dce5e1; }
		.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1440px; }
		h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
		[data-testid="stMetric"] { background: #f3f7f5; border-left: 3px solid var(--green); padding: 14px; }
		[data-testid="stFileUploader"] { border: 1px solid var(--line); border-radius: 6px; padding: 8px; }
		</style>
		""",
		unsafe_allow_html=True,
	)
	st.title("Formação de Jogadores")
	st.caption("Comparação dos perfis técnico e explosivo de jogadores formados em quatro academias.")
	st.divider()

	coluna_arquivo, coluna_filtro = st.columns([2, 1])
	with coluna_arquivo:
		arquivo_carregado = st.file_uploader(
			"Arquivo de índices por jogador (CSV)",
			type=["csv"],
			help="Esperado: player_id, clube/academia, indice_tecnico e indice_explosivo.",
		)
	with coluna_filtro:
		st.write("**Fonte padrão**")
		st.code("data/processed/indices_jogadores.csv", language=None)

	try:
		indices = _ler_indices(arquivo_carregado)
		if indices is None:
			st.info(
				"A base de índices ainda não foi gerada. Carregue um CSV com `player_id`, "
				"`clube` ou `academia`, `indice_tecnico` e `indice_explosivo`; ou salve-o em "
				"`data/processed/indices_jogadores.csv`. As notas não serão estimadas pelo dashboard."
			)
			st.stop()
		jogadores = pd.read_csv(ARQUIVO_JOGADORES) if ARQUIVO_JOGADORES.exists() else None
		base = preparar_dados_visualizacao(indices, jogadores)
	except (KeyError, TypeError, ValueError, pd.errors.ParserError) as erro:
		st.error(f"Não foi possível preparar os dados: {erro}")
		st.stop()

	academias = sorted(base["academia"].dropna().unique().tolist())
	selecionadas = st.multiselect("Academias", academias, default=academias)
	visao = base[base["academia"].isin(selecionadas)]
	if visao.empty:
		st.warning("Selecione ao menos uma academia para exibir a comparação.")
		st.stop()

	metricas = st.columns(3)
	metricas[0].metric("Jogadores atuais que vieram da base", int(visao["player_id"].nunique()) if "player_id" in visao else len(visao))
	metricas[1].metric("Academias", len(selecionadas))
	metricas[2].metric("Índices em escala", "0–100")

	coluna_esquerda, coluna_direita = st.columns(2, gap="large")
	with coluna_esquerda:
		st.plotly_chart(grafico_dispersao_indices(visao), use_container_width=True)
	with coluna_direita:
		st.plotly_chart(grafico_boxplots_indices(visao), use_container_width=True)

	coluna_esquerda, coluna_direita = st.columns(2, gap="large")
	with coluna_esquerda:
		st.plotly_chart(grafico_revelados(visao), use_container_width=True)
	with coluna_direita:
		if "idade_estreia" in visao.columns and visao["idade_estreia"].notna().any():
			st.plotly_chart(grafico_idade_estreia(visao), use_container_width=True)
		else:
			st.info("Idade de estreia indisponível: confirme `date_of_birth` e `estreia` na base validada.")

	with st.expander("Dados usados na visualização"):
		colunas = [
			coluna
			for coluna in (
				"player_id", "nome", "academia", "position", "sub_position",
				"indice_tecnico", "indice_explosivo", "idade_estreia",
			)
			if coluna in visao.columns
		]
		st.dataframe(visao[colunas], use_container_width=True, hide_index=True)
	st.caption("Os gráficos descrevem a amostra selecionada; não indicam causalidade entre academia e desempenho.")


if __name__ == "__main__":
	main()
