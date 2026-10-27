"""Gráficos interativos para apresentação dos resultados por academia."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PALETA_ACADEMIAS = {
	"Barcelona": "#A50044",
	"Real Madrid": "#D6A400",
	"Manchester City": "#55B7D9",
	"Liverpool": "#00856A",
}


def _academia_col(df: pd.DataFrame) -> str:
	for coluna in ("academia", "clube"):
		if coluna in df.columns:
			return coluna
	raise KeyError("A tabela precisa conter a coluna 'academia' ou 'clube'.")


def _validar_indices(df: pd.DataFrame) -> None:
	faltantes = {"indice_tecnico", "indice_explosivo"}.difference(df.columns)
	if faltantes:
		raise KeyError(f"Colunas de índice ausentes: {', '.join(sorted(faltantes))}")
	_academia_col(df)


def preparar_dados_visualizacao(
	indices: pd.DataFrame,
	jogadores: pd.DataFrame | None = None,
) -> pd.DataFrame:
	"""Une os índices por jogador à base validada e calcula idade na estreia.

	A tabela de índices precisa ter academia/clube e os dois índices. Quando há
	base de jogadores, a junção é feita pelo identificador Transfermarkt.
	"""
	if not isinstance(indices, pd.DataFrame):
		raise TypeError("indices precisa ser um pandas.DataFrame.")
	if indices.empty:
		raise ValueError("A tabela de índices está vazia.")
	_validar_indices(indices)

	dados = indices.copy()
	coluna_academia = _academia_col(dados)
	dados = dados.rename(columns={coluna_academia: "academia"})

	if jogadores is not None:
		if "player_id" not in dados.columns or "player_id" not in jogadores.columns:
			raise KeyError("As duas tabelas precisam conter 'player_id' para a junção.")
		if jogadores["player_id"].duplicated().any():
			raise ValueError("A base validada contém player_id duplicados.")
		colunas_contexto = [
			coluna
			for coluna in (
				"player_id", "position", "sub_position", "categoria", "date_of_birth",
				"estreia", "idade_estreia", "minutos",
			)
			if coluna in jogadores.columns and (coluna == "player_id" or coluna not in dados.columns)
		]
		dados["player_id"] = dados["player_id"].astype("string")
		base_jogadores = jogadores[colunas_contexto].copy()
		base_jogadores["player_id"] = base_jogadores["player_id"].astype("string")
		dados = dados.merge(base_jogadores, on="player_id", how="left", validate="one_to_one")

	if "idade_estreia" in dados.columns:
		dados["idade_estreia"] = pd.to_numeric(dados["idade_estreia"], errors="coerce")
	elif {"date_of_birth", "estreia"}.issubset(dados.columns):
		nascimento = pd.to_datetime(dados["date_of_birth"], errors="coerce")
		estreia = pd.to_datetime(dados["estreia"], errors="coerce")
		dados["idade_estreia"] = (estreia - nascimento).dt.days / 365.2425

	for coluna in ("indice_tecnico", "indice_explosivo"):
		dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")
	return dados


def _base_figura(figura: go.Figure, titulo: str, altura: int = 430) -> go.Figure:
	figura.update_layout(
		title={"text": titulo, "x": 0.02, "xanchor": "left"},
		font={"family": "Arial, sans-serif", "size": 13, "color": "#20332F"},
		paper_bgcolor="#FFFFFF",
		plot_bgcolor="#FFFFFF",
		height=altura,
		margin={"l": 48, "r": 24, "t": 72, "b": 48},
		legend_title_text="Academia",
	)
	figura.update_xaxes(showgrid=False, linecolor="#DCE5E1", automargin=True)
	figura.update_yaxes(gridcolor="#E8EEEB", zerolinecolor="#DCE5E1", automargin=True)
	return figura


def grafico_dispersao_indices(df: pd.DataFrame) -> go.Figure:
	"""Cria a dispersão técnico × explosivo, colorida por academia."""
	_validar_indices(df)
	coluna_academia = _academia_col(df)
	dados = df.dropna(subset=["indice_tecnico", "indice_explosivo", coluna_academia]).copy()
	if dados.empty:
		raise ValueError("Não há jogadores com os dois índices para gerar a dispersão.")
	hover_data = [coluna for coluna in ("player_id", "position", "sub_position", "idade_estreia") if coluna in dados]
	figura = px.scatter(
		dados,
		x="indice_tecnico",
		y="indice_explosivo",
		color=coluna_academia,
		color_discrete_map=PALETA_ACADEMIAS,
		hover_name="nome" if "nome" in dados.columns else None,
		hover_data=hover_data,
		labels={
			"indice_tecnico": "Índice técnico (0–100)",
			"indice_explosivo": "Índice explosivo (0–100)",
			coluna_academia: "Academia",
		},
	)
	figura.update_traces(marker={"size": 11, "opacity": 0.82, "line": {"width": 1, "color": "white"}})
	figura.update_xaxes(range=[0, 100], dtick=20)
	figura.update_yaxes(range=[0, 100], dtick=20)
	return _base_figura(figura, "Perfil técnico × explosivo")


def grafico_boxplots_indices(df: pd.DataFrame) -> go.Figure:
	"""Compara as distribuições dos índices por academia em painéis paralelos."""
	_validar_indices(df)
	coluna_academia = _academia_col(df)
	dados = df.melt(
		id_vars=[coluna_academia],
		value_vars=["indice_tecnico", "indice_explosivo"],
		var_name="perfil",
		value_name="indice",
	).dropna(subset=["indice"])
	if dados.empty:
		raise ValueError("Não há valores de índice para gerar os boxplots.")
	dados["perfil"] = dados["perfil"].map(
		{"indice_tecnico": "Índice técnico", "indice_explosivo": "Índice explosivo"}
	)
	figura = px.box(
		dados,
		x=coluna_academia,
		y="indice",
		color=coluna_academia,
		facet_col="perfil",
		points="all",
		color_discrete_map=PALETA_ACADEMIAS,
		labels={coluna_academia: "Academia", "indice": "Índice (0–100)"},
	)
	figura.update_yaxes(range=[0, 100], dtick=20)
	figura.update_layout(showlegend=False, boxmode="group")
	return _base_figura(figura, "Distribuição dos índices por academia", altura=470)


def grafico_revelados(df: pd.DataFrame) -> go.Figure:
	"""Mostra quantos jogadores válidos estão representados por academia."""
	coluna_academia = _academia_col(df)
	if df.empty:
		raise ValueError("Não há jogadores para contabilizar.")
	if "player_id" in df.columns:
		contagens = df.groupby(coluna_academia)["player_id"].nunique().rename("revelados").reset_index()
	else:
		contagens = df.groupby(coluna_academia).size().rename("revelados").reset_index()
	figura = px.bar(
		contagens,
		x=coluna_academia,
		y="revelados",
		color=coluna_academia,
		color_discrete_map=PALETA_ACADEMIAS,
		text="revelados",
		labels={coluna_academia: "Academia", "revelados": "Jogadores"},
	)
	figura.update_traces(textposition="outside", cliponaxis=False)
	figura.update_yaxes(rangemode="tozero", dtick=1)
	figura.update_layout(showlegend=False)
	return _base_figura(figura, "Jogadores revelados na amostra", altura=380)


def grafico_idade_estreia(df: pd.DataFrame) -> go.Figure:
	"""Mostra a idade média de estreia profissional por academia."""
	coluna_academia = _academia_col(df)
	if "idade_estreia" not in df.columns:
		raise KeyError("A tabela precisa conter 'idade_estreia'.")
	dados = df.copy()
	dados["idade_estreia"] = pd.to_numeric(dados["idade_estreia"], errors="coerce")
	resumo = dados.groupby(coluna_academia)["idade_estreia"].mean().dropna().rename("idade_media").reset_index()
	if resumo.empty:
		raise ValueError("Não há idades de estreia válidas para resumir.")
	figura = px.bar(
		resumo,
		x=coluna_academia,
		y="idade_media",
		color=coluna_academia,
		color_discrete_map=PALETA_ACADEMIAS,
		text="idade_media",
		labels={coluna_academia: "Academia", "idade_media": "Idade média (anos)"},
	)
	figura.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
	figura.update_yaxes(rangemode="tozero")
	figura.update_layout(showlegend=False)
	return _base_figura(figura, "Idade média na estreia profissional", altura=380)


__all__ = [
	"preparar_dados_visualizacao",
	"grafico_dispersao_indices",
	"grafico_boxplots_indices",
	"grafico_revelados",
	"grafico_idade_estreia",
]
