"""Geração dos índices técnico e explosivo a partir dos percentis.

A lógica segue a metodologia do README:
- cada índice é agregado por percentis;
- a escala final fica em 0 a 100;
- cada jogador recebe um índice técnico e um explosivo para comparação entre academias.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from config import settings


def carregar_metricas(path: str | Path | None = None) -> dict:
    """Lê a configuração dos índices em config/metricas.yaml."""
    if path is None:
        path = settings.RAIZ / "config" / "metricas.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def agregador_media_percentis(series: pd.Series, pesos: list[float] | None = None) -> float:
    """Calcula a média dos percentis, ponderada quando pesos forem informados."""
    valores = pd.to_numeric(series, errors="coerce").dropna()
    if valores.empty:
        return float("nan")

    if pesos is not None:
        pesos = pd.to_numeric(pd.Series(pesos), errors="coerce").dropna().to_list()
        if len(pesos) != len(valores):
            pesos = None

    if pesos is not None:
        p = pd.Series(pesos, index=valores.index)
        return float((valores * p).sum() / p.sum())

    return float(valores.mean())


def calcular_indices_jogador(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega percentis por jogador em índices técnico e explosivo.

    Entrada esperada:
    - colunas opcionais: player_id, nome, clube, categoria, percentil_0_100, indice
    - quando houver coluna 'indice', ela deve indicar 'tecnico' ou 'explosivo'
    - caso a entrada venha em formato de métricas por percentil, a função também
      consegue agrupar por 'player_id' e 'indice'
    """
    dados = df.copy()
    if dados.empty:
        return pd.DataFrame(columns=["player_id", "nome", "clube", "indice_tecnico", "indice_explosivo"])

    if "percentil_0_100" not in dados.columns:
        raise KeyError("Coluna 'percentil_0_100' necessária para calcular o índice final.")

    if "player_id" not in dados.columns:
        dados["player_id"] = range(len(dados))

    if 'nome' not in dados.columns:
        dados['nome'] = dados.get('player_id').map(str)

    if 'clube' not in dados.columns:
        dados['clube'] = "desconhecido"

    grupos = []
    for _, jogador in dados.groupby(["player_id", "nome", "clube"], dropna=False):
        base = {
            "player_id": jogador["player_id"].iat[0],
            "nome": jogador["nome"].iat[0],
            "clube": jogador["clube"].iat[0],
        }

        # Se a tabela já possui coluna 'indice', cada linha representa um dos índices.
        if "indice" in jogador.columns:
            for nome_indice in ["tecnico", "explosivo"]:
                subset = jogador[jogador["indice"].astype(str).str.lower() == nome_indice]
                if subset.empty:
                    base[f"indice_{nome_indice}"] = float("nan")
                else:
                    base[f"indice_{nome_indice}"] = agregador_media_percentis(subset["percentil_0_100"])
        else:
            # Fallback: usa a configuração do YAML para associar métricas por índice.
            metricas = carregar_metricas()
            for nome_indice in ["tecnico", "explosivo"]:
                variaveis = metricas.get("indices", {}).get(nome_indice, {}).get("variaveis", [])
                if not variaveis:
                    base[f"indice_{nome_indice}"] = float("nan")
                    continue
                nome_variaveis = {v.get("nome") for v in variaveis if isinstance(v, dict) and v.get("nome")}
                subset = jogador[jogador.get("metrica", pd.Series(["valor"] * len(jogador))).astype(str).isin(nome_variaveis)]
                if subset.empty:
                    base[f"indice_{nome_indice}"] = float("nan")
                else:
                    base[f"indice_{nome_indice}"] = agregador_media_percentis(subset["percentil_0_100"])

        grupos.append(base)

    saida = pd.DataFrame(grupos)
    if saida.empty:
        return saida

    for col in ["indice_tecnico", "indice_explosivo"]:
        if col in saida.columns:
            saida[col] = pd.to_numeric(saida[col], errors="coerce")
            saida[col] = saida[col].clip(lower=0, upper=100)

    return saida[["player_id", "nome", "clube", "indice_tecnico", "indice_explosivo"]]


def main() -> None:
    print("Índices técnico e explosivo prontos para uso.")


if __name__ == "__main__":
    main()
