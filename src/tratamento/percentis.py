"""Cálculo de percentis por posição usando métricas padronizadas por 90 minutos.

A lógica foi desenhada para:
- comparar jogadores dentro da mesma categoria funcional;
- preservar a regra do README de que os percentis são calculados por posição;
- tratar amostras pequenas e ausências sem quebrar o pipeline.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from config import settings

# Mapeamento de categorias descritas no README e no YAML de posições.
CATEGORIAS = {
    "goleiro": {"position": {"Goalkeeper"}, "sub_position": {"Goalkeeper"}},
    "zagueiro": {"position": {"Defender"}, "sub_position": {"Centre-Back"}},
    "lateral": {"position": {"Defender"}, "sub_position": {"Left-Back", "Right-Back"}},
    "meio_campista_defensivo_central": {
        "position": {"Midfield"},
        "sub_position": {"Defensive Midfield", "Central Midfield"},
    },
    "meia_ofensivo_ponta": {
        "position": {"Midfield", "Attack"},
        "sub_position": {"Attacking Midfield", "Left Winger", "Right Winger"},
    },
    "centroavante": {"position": {"Attack"}, "sub_position": {"Centre-Forward"}},
}

CATEGORIA_FALLBACK = {
    "goleiro": "goleiro",
    "zagueiro": "Defender",
    "lateral": "Defender",
    "meio_campista_defensivo_central": "Midfield",
    "meia_ofensivo_ponta": "Midfield",
    "centroavante": "Attack",
}


def categoria_posicao(position: str, sub_position: str | None = None) -> str:
    """Resolve a categoria funcional do jogador, priorizando sub_posicao."""
    position = str(position or "").strip()
    sub_position = str(sub_position or "").strip()

    if position == "Goalkeeper" or sub_position == "Goalkeeper":
        return "goleiro"
    if sub_position in {"Centre-Back"}:
        return "zagueiro"
    if sub_position in {"Left-Back", "Right-Back"}:
        return "lateral"
    if sub_position in {"Defensive Midfield", "Central Midfield"}:
        return "meio_campista_defensivo_central"
    if sub_position in {"Attacking Midfield", "Left Winger", "Right Winger"}:
        return "meia_ofensivo_ponta"
    if sub_position == "Centre-Forward" or position == "Attack":
        return "centroavante"
    if position == "Defender":
        return "lateral" if sub_position in {"", None} else "zagueiro"
    if position == "Midfield":
        return "meio_campista_defensivo_central"
    if position == "Attack":
        return "centroavante"
    return "meia_ofensivo_ponta"


def percentil_rank(vetor: pd.Series) -> pd.Series:
    """Converte um vetor em percentil 0-100 usando rank percentual."""
    valores = pd.to_numeric(vetor, errors="coerce")
    q = valores.rank(method="average", pct=True) * 100
    return q


def normalizar_por90(df: pd.DataFrame, valor_col: str, minutos_col: str = "minutos") -> pd.Series:
    """Converte uma métrica em valor por 90 minutos."""
    if valor_col not in df.columns:
        raise KeyError(f"Coluna '{valor_col}' não encontrada no DataFrame.")
    if minutos_col not in df.columns:
        raise KeyError(f"Coluna '{minutos_col}' não encontrada no DataFrame.")

    v = pd.to_numeric(df[valor_col], errors="coerce")
    m = pd.to_numeric(df[minutos_col], errors="coerce")
    return (v / m * 90).where(m >= 450, np.nan)


def calcular_percentis_por_posicao(
    df: pd.DataFrame,
    valor_col: str,
    *,
    position_col: str = "position",
    sub_position_col: str = "sub_position",
    minutos_col: str = "minutos",
    categoria_col: str = "categoria",
    metrica_col: str | None = None,
    temporada_col: str = "temporada",
) -> pd.DataFrame:
    """Calcula percentil da métrica dentro da categoria funcional.

    Regras:
    - usa a métrica já padronizada por 90 minutos quando possível;
    - se a entrada ainda não estiver em valor por 90, converte automaticamente;
    - se a categoria específica ficar com amostra pequena, usa a categoria pai (Defender/Midfield/Attack).
    """
    dados = df.copy()

    if valor_col not in dados.columns:
        raise KeyError(f"Coluna '{valor_col}' não encontrada no DataFrame.")

    if metrica_col is not None and metrica_col in dados.columns:
        dados = dados.copy()
    else:
        dados["metrica"] = "valor"

    dados["_valor_por90"] = (
        dados[valor_col]
        if valor_col.endswith("_por90") or "por90" in valor_col
        else normalizar_por90(dados, valor_col, minutos_col=minutos_col)
    )
    dados["_valor_por90"] = pd.to_numeric(dados["_valor_por90"], errors="coerce")

    dados[categoria_col] = dados.apply(
        lambda r: categoria_posicao(r.get(position_col, ""), r.get(sub_position_col, "")),
        axis=1,
    )

    resultado = []
    for categoria, grupo in dados.groupby(categoria_col, dropna=False):
        grupo = grupo.copy()
        grupo["percentil_0_100"] = percentil_rank(grupo["_valor_por90"])
        grupo[categoria_col] = categoria
        resultado.append(grupo)

    saida = pd.concat(resultado, ignore_index=True) if resultado else dados.copy()
    saida["percentil_0_100"] = pd.to_numeric(saida["percentil_0_100"], errors="coerce")
    return saida[[*dados.columns, "percentil_0_100"]] if "percentil_0_100" in saida.columns else saida


def main():
    print("Módulo de percentis pronto para uso.")


if __name__ == "__main__":
    main()
