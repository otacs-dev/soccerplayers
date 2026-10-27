"""
Converte contagens em métricas por 90 minutos: valor / minutos x 90.

Rodar da raiz do projeto:

    python -m src.tratamento.por90

Entradas : data/processed/jogadores_validos.csv
           data/raw/appearances.csv                   (Kaggle/Transfermarkt)
           data/interim/sofascore_temporada.csv       (opcional, do sofascore.py)
Saídas   : data/interim/por90_appearances.csv   uma linha por jogador e temporada
           data/interim/por90_sofascore.csv     uma linha por jogador, temporada,
                                                torneio e métrica

Regras
------
* Temporada vai de julho a junho ('2023/24'), o mesmo rótulo nas duas fontes.
* Com menos de MIN_MIN_TEMPORADA minutos a amostra é pequena demais e o valor por 90
  fica vazio (NaN). A linha NÃO é apagada, para o relatório de dados ausentes
  continuar contando o jogador.
* Só contagens viram "por 90". Percentuais e notas (ex.: % de passes certos, rating)
  são mantidos como estão, porque dividir por minutos não faz sentido para eles.
"""
import re

import pandas as pd

from config import settings

# Mínimo de minutos na temporada para o valor por 90 ser confiável.
MIN_MIN_TEMPORADA = getattr(settings, "MIN_MIN_TEMPORADA", 450)

ARQ_SOFASCORE = settings.DIR_INTERIM / "sofascore_temporada.csv"
SAIDA_APPEARANCES = settings.DIR_INTERIM / "por90_appearances.csv"
SAIDA_SOFASCORE = settings.DIR_INTERIM / "por90_sofascore.csv"

# Métricas do Sofascore que não são "algo que aconteceu em campo"
NAO_E_METRICA = {"minutesPlayed", "appearances", "matchesStarted", "id"}
PADRAO_TAXA = re.compile(r"percentage|rating", re.IGNORECASE)


# --------------------------------------------------------------------------
# Funções puras (fáceis de testar em tests/test_por90.py)
# --------------------------------------------------------------------------
def temporada_de(data):
    """'2024-03-10' -> '2023/24' ; '2023-09-01' -> '2023/24'."""
    d = pd.to_datetime(data)
    inicio = d.year if d.month >= 7 else d.year - 1
    return f"{inicio}/{str(inicio + 1)[-2:]}"


def por90(valor, minutos, minimo=MIN_MIN_TEMPORADA):
    """valor / minutos x 90, ou NaN se a amostra for pequena demais."""
    valor = pd.to_numeric(valor, errors="coerce")
    minutos = pd.to_numeric(minutos, errors="coerce")
    return (valor / minutos * 90).where(minutos >= minimo)


def eh_taxa(metrica):
    return bool(PADRAO_TAXA.search(str(metrica)))


# --------------------------------------------------------------------------
# Parte 1: gols, assistências e cartões (appearances.csv)
# --------------------------------------------------------------------------
def tabela_appearances(validos):
    ap = pd.read_csv(
        settings.ARQ_APPEARANCES,
        usecols=["player_id", "date", "yellow_cards", "red_cards",
                 "goals", "assists", "minutes_played"],
    )
    ap = ap[ap["player_id"].isin(validos["player_id"])].copy()
    ap["temporada"] = ap["date"].map(temporada_de)

    t = (ap.groupby(["player_id", "temporada"], as_index=False)
           .agg(jogos=("date", "size"),
                minutos=("minutes_played", "sum"),
                gols=("goals", "sum"),
                assistencias=("assists", "sum"),
                amarelos=("yellow_cards", "sum"),
                vermelhos=("red_cards", "sum")))

    for col in ["gols", "assistencias", "amarelos", "vermelhos"]:
        t[f"{col}_por90"] = por90(t[col], t["minutos"])
    t["amostra_suficiente"] = t["minutos"] >= MIN_MIN_TEMPORADA

    info = validos[["player_id", "nome", "clube", "position", "sub_position"]]
    return t.merge(info, on="player_id", how="left")


# --------------------------------------------------------------------------
# Parte 2: métricas do Sofascore
# --------------------------------------------------------------------------
def tabela_sofascore():
    if not ARQ_SOFASCORE.exists():
        print(f"Aviso: {ARQ_SOFASCORE.name} não existe ainda. "
              "Pulei a parte do Sofascore (rode src.coleta.sofascore coletar).")
        return None

    s = pd.read_csv(ARQ_SOFASCORE, encoding="utf-8-sig")
    chaves = ["id_tm", "temporada", "torneio"]

    # minutos de cada jogador naquele torneio e temporada
    minutos = (s[s["metrica"] == "minutesPlayed"]
               .rename(columns={"valor": "minutos"})[chaves + ["minutos"]]
               .drop_duplicates(chaves))

    m = s[~s["metrica"].isin(NAO_E_METRICA)].merge(minutos, on=chaves, how="left")
    m["tipo"] = m["metrica"].map(lambda x: "taxa" if eh_taxa(x) else "contagem")
    m["valor_por90"] = por90(m["valor"], m["minutos"])
    m.loc[m["tipo"] == "taxa", "valor_por90"] = float("nan")
    m["amostra_suficiente"] = m["minutos"] >= MIN_MIN_TEMPORADA
    return m


# --------------------------------------------------------------------------
def main():
    validos = pd.read_csv(settings.ARQ_VALIDOS_FINAL, encoding="utf-8-sig")
    settings.DIR_INTERIM.mkdir(parents=True, exist_ok=True)

    a = tabela_appearances(validos)
    a.to_csv(SAIDA_APPEARANCES, index=False, encoding="utf-8-sig")
    print(f"{SAIDA_APPEARANCES.name}: {len(a)} linhas, "
          f"{a['player_id'].nunique()} jogadores, "
          f"{int(a['amostra_suficiente'].sum())} temporadas com amostra suficiente.")

    s = tabela_sofascore()
    if s is not None:
        s.to_csv(SAIDA_SOFASCORE, index=False, encoding="utf-8-sig")
        print(f"{SAIDA_SOFASCORE.name}: {len(s)} linhas, "
              f"{s['metrica'].nunique()} métricas diferentes.")


if __name__ == "__main__":
    main()
