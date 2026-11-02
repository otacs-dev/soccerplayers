"""Base qualitativa com afirmações limitadas ao que as fontes consultadas sustentam."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import settings


def base_metodos_academias() -> pd.DataFrame:
    """Retorna evidências institucionais; não presume um estilo tático sem fonte."""
    dados = [
        {
            "academia": "Barcelona",
            "aspecto_documentado": (
                "A descrição oficial apresenta acompanhamento multidisciplinar do atleta, "
                "incluindo dimensões esportiva, pessoal e educacional."
            ),
            "tipo_evidencia": "Descrição institucional da própria academia",
            "fonte": "FC Barcelona — All about La Masia",
            "url_fonte": "https://www.fcbarcelona.com/en/news/783458/all-about-la-masia",
            "limite": (
                "Fonte institucional, não avaliação independente; não permite comparar "
                "resultados nem afirmar que esse modelo causou desempenho."
            ),
        },
        {
            "academia": "Real Madrid",
            "aspecto_documentado": (
                "O portal oficial identifica a academia de futebol masculino e divulga "
                "equipes de formação e suas competições."
            ),
            "tipo_evidencia": "Portal oficial da academia",
            "fonte": "Real Madrid — Men's Youth Academy",
            "url_fonte": "https://www.realmadrid.com/en-US/football/academy",
            "limite": (
                "A página consultada não descreve com detalhe um método de treino; "
                "não se atribui um estilo técnico ou tático."
            ),
        },
        {
            "academia": "Manchester City",
            "aspecto_documentado": (
                "A página institucional consultada não forneceu evidência suficiente "
                "para descrever práticas específicas de formação."
            ),
            "tipo_evidencia": "Página institucional consultada; evidência insuficiente",
            "fonte": "Manchester City — site oficial do clube",
            "url_fonte": "https://www.mancity.com/club",
            "limite": (
                "Não se infere foco em posse, intensidade ou qualquer estilo de jogo "
                "a partir da identidade do time profissional."
            ),
        },
        {
            "academia": "Liverpool",
            "aspecto_documentado": (
                "O endereço institucional da equipe de formação não expôs conteúdo "
                "suficiente para caracterizar práticas específicas."
            ),
            "tipo_evidencia": "Página institucional consultada; evidência insuficiente",
            "fonte": "Liverpool FC — Academy",
            "url_fonte": "https://www.liverpoolfc.com/teams/academy",
            "limite": (
                "Não se infere foco em pressão ou transição a partir da identidade "
                "do time profissional."
            ),
        },
    ]
    return pd.DataFrame(dados).assign(data_consulta="2026-10-27")


def salvar_metodos_academias(
    caminho: str | Path = settings.DIR_MANUAL / "metodos_academias.csv",
) -> pd.DataFrame:
    """Salva a base qualitativa em CSV, criando o diretório se necessário."""
    df = base_metodos_academias()
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, encoding="utf-8-sig")
    return df


def main() -> None:
    df = salvar_metodos_academias()
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
