"""Base qualitativa dos métodos de academias.

Este módulo organiza a descrição dos métodos de formação de cada academia,
conforme a metodologia do README: abordagem qualitativa, com fonte em cada linha.
"""

from __future__ import annotations

import pandas as pd


def base_metodos_academias() -> pd.DataFrame:
    """Retorna uma tabela de métodos de formação por academia."""
    dados = [
        {
            "academia": "Barcelona",
            "metodo": "La Masia — modelo de desenvolvimento integrado com foco em técnica, leitura de jogo e posse, com transição gradual da base ao profissional.",
            "fonte": "README do projeto; contexto bibliográfico do estudo e descrição qualitativa das academias.",
        },
        {
            "academia": "Real Madrid",
            "metodo": "La Fábrica — sistema orientado a alto nível técnico, competitividade e exigência por performance em diferentes faixas etárias.",
            "fonte": "README do projeto; contexto bibliográfico do estudo e descrição qualitativa das academias.",
        },
        {
            "academia": "Manchester City",
            "metodo": "City Football Academy — modelo de formação com foco em jogo posicional, intensidade, controle de fases e padronização tática.",
            "fonte": "README do projeto; contexto bibliográfico do estudo e descrição qualitativa das academias.",
        },
        {
            "academia": "Liverpool",
            "metodo": "The Academy — abordagem baseada em dinâmica de alto pressionamento, transição rápida e desenvolvimento de jogadores versáteis.",
            "fonte": "README do projeto; contexto bibliográfico do estudo e descrição qualitativa das academias.",
        },
    ]
    return pd.DataFrame(dados)


def salvar_metodos_academias(caminho: str = "data/manual/metodos_academias.csv") -> pd.DataFrame:
    """Salva a base qualitativa em CSV para uso no relatório."""
    df = base_metodos_academias()
    df.to_csv(caminho, index=False, encoding="utf-8-sig")
    return df


def main() -> None:
    df = salvar_metodos_academias()
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
