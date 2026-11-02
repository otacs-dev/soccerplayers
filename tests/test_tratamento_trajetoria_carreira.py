import pandas as pd
import pytest

from src.analise.correlacao import correlacionar_trajetoria_carreira
from src.coleta._trajetoria import normalizar_temporadas
from src.coleta.bdfutbol import ler_temporadas
from src.coleta.uefa_youth import ler_participacoes
from src.features.carreira import calcular_features_carreira
from src.features.trajetoria import resumir_trajetoria
from src.qualitativo.metodos_academias import base_metodos_academias
from src.tratamento.integracao import integrar_por_id
from src.tratamento.limpeza import limpar_base_jogadores


def test_limpar_base_normaliza_colunas_texto_e_ids_sem_apagar_linhas():
    entrada = pd.DataFrame(
        {
            " player_id ": ["12", "13"],
            " nome ": [" Ana ", "NA"],
        }
    )

    resultado = limpar_base_jogadores(entrada)

    assert resultado["player_id"].tolist() == [12, 13]
    assert resultado["nome"].iloc[0] == "Ana"
    assert pd.isna(resultado["nome"].iloc[1])
    assert len(resultado) == 2


def test_limpar_base_rejeita_ids_duplicados_e_invalidos():
    with pytest.raises(ValueError, match="duplicados"):
        limpar_base_jogadores(pd.DataFrame({"player_id": [1, 1]}))
    with pytest.raises(ValueError, match="não inteiros"):
        limpar_base_jogadores(pd.DataFrame({"player_id": [1, "id-incorreto"]}))


def test_integrar_por_id_normaliza_chave_e_valida_cardinalidade():
    resultado = integrar_por_id(
        pd.DataFrame({"player_id": ["1", "1"], "valor": [2, 3]}),
        pd.DataFrame({"player_id": [1], "nome": ["A"]}),
    )
    assert resultado["nome"].tolist() == ["A", "A"]

    with pytest.raises(pd.errors.MergeError):
        integrar_por_id(
            pd.DataFrame({"player_id": [1]}),
            pd.DataFrame({"player_id": [1, 1]}),
        )


def test_features_carreira_agrega_aparicoes_e_calcula_idade_de_estreia():
    aparicoes = pd.DataFrame(
        {
            "player_id": [1, 1, 2],
            "temporada": ["2022/23", "2023/24", "2023/24"],
            "jogos": [10, 12, 8],
            "minutos": [700, 900, 600],
            "gols": [2, 3, 1],
            "assistencias": [1, 2, 0],
        }
    )
    jogadores = pd.DataFrame(
        {
            "player_id": [1, 2],
            "date_of_birth": ["2000-01-01", "2001-01-01"],
            "estreia": ["2018-01-01", "2019-01-01"],
        }
    )

    resultado = calcular_features_carreira(aparicoes, jogadores).set_index("player_id")

    assert resultado.loc[1, "jogos_profissionais"] == 22
    assert resultado.loc[1, "minutos_profissionais"] == 1600
    assert resultado.loc[1, "temporadas_com_aparicoes"] == 2
    assert resultado.loc[1, "idade_estreia"] == pytest.approx(18.0, abs=0.1)


def test_normalizador_de_temporadas_exige_ids_e_academias_do_escopo():
    resultado = normalizar_temporadas(
        pd.DataFrame(
            {
                "player_id": [10, 10],
                "academia": ["Barcelona", "Barcelona"],
                "temporada": ["2018/19", "2019-2020"],
            }
        ),
        fonte="bdfutbol",
    )
    assert resultado["ano_temporada"].tolist() == [2018, 2019]
    with pytest.raises(ValueError, match="fora do escopo"):
        normalizar_temporadas(
            pd.DataFrame(
                {"player_id": [10], "academia": ["Ajax"], "temporada": ["2018/19"]}
            ),
            fonte="bdfutbol",
        )


def test_importadores_locais_bdfutbol_e_uefa_normalizam_csvs(tmp_path):
    bdfutbol = tmp_path / "bdfutbol.csv"
    pd.DataFrame(
        {"player_id": [20], "academia": ["Barcelona"], "temporada": ["2018/19"]}
    ).to_csv(bdfutbol, index=False)
    assert ler_temporadas(bdfutbol).iloc[0]["fonte"] == "bdfutbol"

    uefa = tmp_path / "uefa.csv"
    pd.DataFrame(
        {
            "player_id": [20],
            "academia": ["Barcelona"],
            "temporada": ["2019/20"],
            "competicao": ["UEFA Youth League"],
        }
    ).to_csv(uefa, index=False)
    resultado = ler_participacoes(uefa).iloc[0]
    assert resultado["ano_temporada"] == 2019
    assert resultado["fonte"] == "uefa_youth_league"
    assert resultado["competicao"] == "UEFA Youth League"


def test_resumo_trajetoria_deduplica_temporadas_e_conta_academia_alvo():
    temporadas = pd.DataFrame(
        {
            "player_id": [1, 1, 1, 1],
            "academia": ["Barcelona", "Barcelona", "Liverpool", "Liverpool"],
            "ano_temporada": [2018, 2018, 2019, 2020],
        }
    )
    jogadores = pd.DataFrame({"player_id": [1], "clube": ["Liverpool"]})

    resultado = resumir_trajetoria(temporadas, jogadores).iloc[0]

    assert resultado["n_academias_documentadas"] == 2
    assert resultado["temporadas_formacao_observadas"] == 3
    assert resultado["temporadas_academia_alvo_observadas"] == 2


def test_correlacao_spearman_ajusta_pvalores_e_trata_variavel_constante():
    trajetoria = pd.DataFrame(
        {
            "player_id": range(1, 7),
            "temporadas_formacao_observadas": [1, 2, 3, 4, 5, 6],
            "constante": [1] * 6,
        }
    )
    carreira = pd.DataFrame(
        {
            "player_id": range(1, 7),
            "minutos_profissionais": [100, 200, 300, 400, 500, 600],
        }
    )

    resultado = correlacionar_trajetoria_carreira(
        trajetoria,
        carreira,
        variaveis_trajetoria=("temporadas_formacao_observadas", "constante"),
        indicadores_carreira=("minutos_profissionais",),
        minimo_observacoes=5,
    )

    assert resultado.loc[0, "rho"] == pytest.approx(1.0)
    assert resultado.loc[0, "p_bonferroni"] == min(1.0, resultado.loc[0, "p_value"] * 2)
    assert pd.isna(resultado.loc[1, "rho"])
    assert not resultado["significativo"].iloc[1]


def test_tabela_qualitativa_cita_cada_academia_e_declara_limites():
    resultado = base_metodos_academias()

    assert set(resultado["academia"]) == {
        "Barcelona", "Real Madrid", "Manchester City", "Liverpool"
    }
    assert resultado["url_fonte"].notna().all()
    assert resultado["limite"].str.len().gt(0).all()
