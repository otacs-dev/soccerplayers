"""Gera um relatório local de cobertura de métricas da coorte profissional."""

from __future__ import annotations

import pandas as pd
import yaml

from config import settings


ARQ_RELATORIO = settings.DIR_PROCESSED / "lacunas_estatisticas_profissionais.csv"
ARQ_INDICES = settings.DIR_PROCESSED / "indices_profissionais.csv"
ARQ_SOFASCORE = settings.DIR_INTERIM / "sofascore_profissionais.csv"


def _metricas_configuradas() -> dict[str, str]:
    caminho = settings.RAIZ / "config" / "metricas.yaml"
    with caminho.open(encoding="utf-8") as arquivo:
        definicoes = yaml.safe_load(arquivo) or {}
    return {
        variavel["nome"]: variavel["fonte"]
        for configuracao in definicoes.get("indices", {}).values()
        for variavel in configuracao.get("variaveis", [])
    }


def construir_relatorio_lacunas(
    coorte: pd.DataFrame,
    metricas_por_fonte: dict[str, str],
    ids_disponiveis: dict[str, set[int]],
    indices: pd.DataFrame,
    ids_snapshot: set[int],
) -> pd.DataFrame:
    """Monta uma linha por jogador e uma coluna de disponibilidade por métrica."""
    relatorio = coorte.drop_duplicates("player_id").copy()
    relatorio["player_id"] = pd.to_numeric(relatorio["player_id"], errors="raise").astype("int64")
    relatorio = relatorio.sort_values(["clube", "nome", "player_id"]).reset_index(drop=True)

    for metrica in metricas_por_fonte:
        coluna = f"tem_{metrica}"
        relatorio[coluna] = relatorio["player_id"].isin(ids_disponiveis.get(metrica, set()))

    colunas_disponibilidade = [f"tem_{metrica}" for metrica in metricas_por_fonte]
    colunas_sofascore = [
        f"tem_{metrica}"
        for metrica, fonte in metricas_por_fonte.items()
        if fonte == "sofascore"
    ]
    relatorio["tem_metrica_sofascore_configurada"] = (
        relatorio[colunas_sofascore].any(axis=1) if colunas_sofascore else False
    )
    relatorio["tem_snapshot_sofascore"] = relatorio["player_id"].isin(ids_snapshot)
    relatorio["metricas_faltantes"] = relatorio.apply(
        lambda linha: "; ".join(
            metrica
            for metrica in metricas_por_fonte
            if not linha[f"tem_{metrica}"]
        ),
        axis=1,
    )
    relatorio["n_metricas_faltantes"] = relatorio[colunas_disponibilidade].eq(False).sum(axis=1)

    indices_relatorio = indices.drop_duplicates("player_id")
    colunas_indices = [
        coluna
        for coluna in (
            "player_id",
            "indice_tecnico",
            "indice_explosivo",
            "cobertura_tecnico",
            "cobertura_explosivo",
        )
        if coluna in indices_relatorio.columns
    ]
    relatorio = relatorio.merge(
        indices_relatorio[colunas_indices],
        on="player_id",
        how="left",
        validate="one_to_one",
    )
    relatorio["indice_tecnico_disponivel"] = relatorio["indice_tecnico"].notna()
    relatorio["indice_explosivo_disponivel"] = relatorio["indice_explosivo"].notna()

    colunas_identificacao = [
        coluna
        for coluna in ("player_id", "nome", "clube", "position", "sub_position")
        if coluna in relatorio.columns
    ]
    colunas_resultado = [
        *colunas_identificacao,
        "tem_snapshot_sofascore",
        "tem_metrica_sofascore_configurada",
        *colunas_disponibilidade,
        "metricas_faltantes",
        "n_metricas_faltantes",
        "indice_tecnico",
        "cobertura_tecnico",
        "indice_tecnico_disponivel",
        "indice_explosivo",
        "cobertura_explosivo",
        "indice_explosivo_disponivel",
    ]
    return relatorio[colunas_resultado]


def gerar_relatorio_lacunas() -> pd.DataFrame:
    """Lê os dados locais, calcula cobertura e grava o relatório CSV."""
    caminho_coorte = settings.DIR_PROCESSED / "jogadores_profissionais.csv"
    for caminho in (caminho_coorte, ARQ_SOFASCORE, ARQ_INDICES, settings.ARQ_APPEARANCES, settings.ARQ_PLAYERS):
        if not caminho.is_file():
            raise FileNotFoundError(f"Arquivo obrigatório ausente: {caminho}")

    profissionais = pd.read_csv(caminho_coorte, encoding="utf-8-sig")
    coorte = (
        profissionais.groupby("player_id", as_index=False)
        .agg(
            nome=("nome", "first"),
            clube=("clube", lambda valores: "; ".join(sorted(set(valores.dropna().astype(str))))),
            position=("position", "first"),
            sub_position=("sub_position", "first"),
        )
    )
    ids_coorte = set(pd.to_numeric(coorte["player_id"], errors="raise").astype(int))
    metricas_por_fonte = _metricas_configuradas()
    ids_disponiveis: dict[str, set[int]] = {}

    sofascore = pd.read_csv(
        ARQ_SOFASCORE,
        usecols=["id_tm", "metrica", "valor"],
        encoding="utf-8-sig",
    )
    sofascore["id_tm"] = pd.to_numeric(sofascore["id_tm"], errors="coerce")
    sofascore["valor"] = pd.to_numeric(sofascore["valor"], errors="coerce")
    sofascore = sofascore.dropna(subset=["id_tm", "valor"])
    sofascore["id_tm"] = sofascore["id_tm"].astype("int64")
    ids_snapshot = set(sofascore["id_tm"])
    for metrica, fonte in metricas_por_fonte.items():
        if fonte == "sofascore":
            ids_disponiveis[metrica] = set(
                sofascore.loc[sofascore["metrica"] == metrica, "id_tm"].astype(int)
            )

    for metrica, fonte in metricas_por_fonte.items():
        if fonte == "appearances":
            ids_disponiveis[metrica] = set()
    metricas_appearances = [
        metrica for metrica, fonte in metricas_por_fonte.items() if fonte == "appearances"
    ]
    if metricas_appearances:
        for parte in pd.read_csv(
            settings.ARQ_APPEARANCES,
            usecols=["player_id", *metricas_appearances],
            chunksize=250_000,
        ):
            parte["player_id"] = pd.to_numeric(parte["player_id"], errors="coerce")
            parte = parte[parte["player_id"].isin(ids_coorte)]
            for metrica in metricas_appearances:
                ids_disponiveis[metrica].update(
                    parte.loc[parte[metrica].notna(), "player_id"].astype(int)
                )

    metricas_players = [
        metrica for metrica, fonte in metricas_por_fonte.items() if fonte == "players"
    ]
    if metricas_players:
        perfis = pd.read_csv(
            settings.ARQ_PLAYERS,
            usecols=["player_id", *metricas_players],
        )
        perfis["player_id"] = pd.to_numeric(perfis["player_id"], errors="coerce")
        perfis = perfis[perfis["player_id"].isin(ids_coorte)]
        for metrica in metricas_players:
            ids_disponiveis[metrica] = set(
                perfis.loc[perfis[metrica].notna(), "player_id"].astype(int)
            )

    indices = pd.read_csv(ARQ_INDICES, encoding="utf-8-sig")
    relatorio = construir_relatorio_lacunas(
        coorte,
        metricas_por_fonte,
        ids_disponiveis,
        indices,
        ids_snapshot,
    )
    settings.DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    relatorio.to_csv(ARQ_RELATORIO, index=False, encoding="utf-8-sig")
    return relatorio


def main() -> None:
    relatorio = gerar_relatorio_lacunas()
    print(f"Relatório salvo em {ARQ_RELATORIO.relative_to(settings.RAIZ)}")
    print(f"- jogadores únicos: {len(relatorio)}")
    print(f"- com qualquer registro no snapshot: {int(relatorio['tem_snapshot_sofascore'].sum())}")
    print(
        "- com alguma métrica Sofascore configurada: "
        f"{int(relatorio['tem_metrica_sofascore_configurada'].sum())}"
    )
    print(f"- com índice técnico: {int(relatorio['indice_tecnico_disponivel'].sum())}")
    print(f"- com índice explosivo: {int(relatorio['indice_explosivo_disponivel'].sum())}")


if __name__ == "__main__":
    main()
