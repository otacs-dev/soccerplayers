"""
Seleção de jogadores formados nas 4 academias a partir do dataset do Kaggle
(Transfermarkt: davidcariboo/player-scores).

COMO USAR (da raiz do projeto, com o ambiente virtual ativo)
------------------------------------------------------------

Observações
-----------
- "Promovido da base" é um SINAL, não prova: usa o histórico de transferências
  (ex.: "Barça U19" -> Barcelona). Há falsos positivos (jogador que veio da base
  de outro clube e passou pela equipe sub-23 do atual) e falsos negativos
  (formados que saíram e voltaram). Por isso existe a conferência manual.
- Minutos e estreia consideram só os jogos presentes no appearances.csv.
"""
import argparse
import sys

import pandas as pd

from config import settings as cfg


# --------------------------------------------------------------------------
# Leitura
# --------------------------------------------------------------------------
def _exigir(caminho):
    if not caminho.exists():
        sys.exit(
            f"Arquivo não encontrado: {caminho}\n"
            f"Baixe os CSVs do Kaggle (davidcariboo/player-scores) e coloque em {cfg.DIR_RAW}"
        )


def _ler_dados():
    for arq in (cfg.ARQ_PLAYERS, cfg.ARQ_APPEARANCES, cfg.ARQ_TRANSFERS):
        _exigir(arq)

    appearances = pd.read_csv(
        cfg.ARQ_APPEARANCES,
        usecols=["game_id", "player_id", "player_club_id", "date", "minutes_played", "player_name"],
        parse_dates=["date"],
    )
    transfers = pd.read_csv(
        cfg.ARQ_TRANSFERS,
        usecols=["player_id", "to_club_id", "from_club_name"],
    )
    players = pd.read_csv(
        cfg.ARQ_PLAYERS,
        usecols=["player_id", "position", "sub_position", "date_of_birth", "height_in_cm", "url"],
    )
    return appearances, transfers, players


# --------------------------------------------------------------------------
# Cálculos
# --------------------------------------------------------------------------
def _minutos_por_clube(appearances):
    """Estreia (primeira partida), minutos e jogos de cada jogador em cada um dos 4 clubes."""
    a = appearances[appearances["player_club_id"].isin(cfg.CLUBES)]
    return (
        a.groupby(["player_id", "player_club_id"])
        .agg(
            nome=("player_name", "first"),
            estreia=("date", "min"),
            minutos=("minutes_played", "sum"),
            jogos=("game_id", "nunique"),
        )
        .reset_index()
    )


def _marcar_promocoes(transfers):
    """Para cada jogador e clube, indica se chegou vindo da base do próprio clube."""
    t = transfers[transfers["to_club_id"].isin(cfg.CLUBES)].copy()
    t["from_club_name"] = t["from_club_name"].fillna("")
    t["promovido"] = False
    for clube_id, padrao in cfg.PADROES_BASE.items():
        mask = (t["to_club_id"] == clube_id) & t["from_club_name"].str.contains(padrao, regex=True)
        t.loc[mask, "promovido"] = True

    return (
        t.groupby(["player_id", "to_club_id"])
        .agg(
            promovido_da_base=("promovido", "any"),
            origens_no_transfers=("from_club_name", lambda s: " | ".join(sorted({x for x in s if x}))),
        )
        .reset_index()
        .rename(columns={"to_club_id": "player_club_id"})
    )


# --------------------------------------------------------------------------
# Etapa 1: candidatos
# --------------------------------------------------------------------------
COLUNAS_MANUAL = [
    "clube", "player_id", "nome", "position", "sub_position", "date_of_birth",
    "height_in_cm", "estreia", "minutos", "jogos", "origens_no_transfers", "url",
    "formado_confirmado", "fonte_conferencia",
]


def gerar_candidatos():
    appearances, transfers, players = _ler_dados()

    if pd.Timestamp(cfg.CAND_ESTREIA_DESDE) < pd.Timestamp(cfg.INICIO_COBERTURA):
        print("AVISO: o appearances.csv começa em 2012; cortes de estreia antes de 2013 não são confiáveis.")

    base = _minutos_por_clube(appearances).merge(
        _marcar_promocoes(transfers), on=["player_id", "player_club_id"], how="left"
    )
    base["promovido_da_base"] = base["promovido_da_base"].fillna(False)
    base = base.merge(players, on="player_id", how="left")
    base["clube"] = base["player_club_id"].map(cfg.CLUBES)
    base["estreia"] = base["estreia"].dt.date
    base["date_of_birth"] = base["date_of_birth"].astype(str).str[:10]

    cand = base[
        base["promovido_da_base"]
        & (base["estreia"] >= pd.Timestamp(cfg.CAND_ESTREIA_DESDE).date())
        & (base["minutos"] >= cfg.CAND_MIN_MINUTOS)
    ].sort_values(["clube", "minutos"], ascending=[True, False])
    cand = cand.assign(formado_confirmado="", fonte_conferencia="")[COLUNAS_MANUAL]

    cfg.DIR_INTERIM.mkdir(parents=True, exist_ok=True)
    cfg.DIR_MANUAL.mkdir(parents=True, exist_ok=True)
    cand.to_csv(cfg.ARQ_CANDIDATOS, index=False, encoding="utf-8-sig")
    print(f"Candidatos salvos em {cfg.ARQ_CANDIDATOS}")

    _atualizar_arquivo_manual(cand)
    print(cand.groupby("clube").size().to_string())
    return cand


def _atualizar_arquivo_manual(cand):
    """Cria o arquivo manual ou acrescenta só as linhas novas, sem tocar no que já foi preenchido."""
    arq = cfg.ARQ_VALIDOS_MANUAL
    if not arq.exists() or arq.stat().st_size == 0:
        cand.to_csv(arq, index=False, encoding="utf-8-sig")
        print(f"Arquivo manual criado em {arq}: preencha formado_confirmado e fonte_conferencia.")
        return

    atual = pd.read_csv(arq, dtype=str, keep_default_na=False)
    chaves = set(zip(atual["player_id"], atual["clube"]))
    novas = cand[[(str(p), c) not in chaves for p, c in zip(cand["player_id"], cand["clube"])]]
    if novas.empty:
        print(f"{arq} já contém todos os candidatos; nada foi alterado.")
        return
    pd.concat([atual, novas.astype(str)], ignore_index=True).to_csv(arq, index=False, encoding="utf-8-sig")
    print(f"{len(novas)} candidatos novos acrescentados a {arq}; o que já estava preenchido foi mantido.")


# --------------------------------------------------------------------------
# Etapa 2: lista final
# --------------------------------------------------------------------------
def montar_jogadores_validos():
    arq = cfg.ARQ_VALIDOS_MANUAL
    if not arq.exists() or arq.stat().st_size == 0:
        sys.exit(f"{arq} não existe. Rode primeiro: python -m src.coleta.transfermarkt candidatos")

    df = pd.read_csv(arq, dtype=str, keep_default_na=False)
    confirmados = df[df["formado_confirmado"].str.strip().str.lower().isin(["sim", "s", "yes"])].copy()
    if confirmados.empty:
        sys.exit("Nenhum jogador com formado_confirmado = sim. Preencha o arquivo manual antes.")

    confirmados["minutos"] = pd.to_numeric(confirmados["minutos"])
    confirmados["estreia"] = pd.to_datetime(confirmados["estreia"])
    final = confirmados[
        (confirmados["estreia"] >= pd.Timestamp(cfg.ESTREIA_DESDE))
        & (confirmados["minutos"] >= cfg.MIN_MINUTOS)
    ]
    final = (
        final.sort_values(["clube", "minutos"], ascending=[True, False])
        .groupby("clube", group_keys=False)
        .head(cfg.MAX_POR_CLUBE)
    )

    cfg.DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    final.to_csv(cfg.ARQ_VALIDOS_FINAL, index=False, encoding="utf-8-sig")
    print(f"Lista final salva em {cfg.ARQ_VALIDOS_FINAL}")

    contagem = final.groupby("clube").size().reindex(list(cfg.CLUBES.values()), fill_value=0)
    print(contagem.to_string())
    for clube, n in contagem.items():
        if n < cfg.MIN_RECOMENDADO_POR_CLUBE:
            print(f"AVISO: {clube} ficou com {n} jogadores (mínimo recomendado: {cfg.MIN_RECOMENDADO_POR_CLUBE}). "
                  f"Considere afrouxar ESTREIA_DESDE/MIN_MINUTOS em config/settings.py.")
    return final


# --------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Seleção de jogadores formados (Transfermarkt/Kaggle)")
    ap.add_argument("etapa", choices=["candidatos", "validos"])
    args = ap.parse_args()
    if args.etapa == "candidatos":
        gerar_candidatos()
    else:
        montar_jogadores_validos()
