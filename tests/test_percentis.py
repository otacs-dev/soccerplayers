import pytest

from src.tratamento.percentis import categoria_posicao


@pytest.mark.parametrize(
	("position", "sub_position", "expected"),
	[
		("Defender", "Left-Back", "lateral"),
		("Defender", "Centre-Back", "zagueiro"),
		("Midfield", "Defensive Midfield", "meio_campista_defensivo_central"),
		("Midfield", "Attacking Midfield", "meia_ofensivo_ponta"),
		("Midfield", "Left Midfield", "meia_ofensivo_ponta"),
		("Midfield", "Right Midfield", "meia_ofensivo_ponta"),
		("Attack", "Right Winger", "meia_ofensivo_ponta"),
		("Attack", "Centre-Forward", "centroavante"),
		("Attack", "Second Striker", "centroavante"),
		("Goalkeeper", "Goalkeeper", "goleiro"),
		("Goalkeeper", "", "goleiro"),
	],
)
def test_categoria_posicao_classifica_posicoes_conhecidas(position, sub_position, expected):
	assert categoria_posicao(position, sub_position) == expected


@pytest.mark.parametrize(
	("position", "sub_position"),
	[
		("Defender", ""),
		("Defender", "Unknown"),
		("Attack", ""),
		("Midfield", "Unknown"),
		("", ""),
	],
)
def test_categoria_posicao_rejeita_posicoes_ausentes_ou_desconhecidas(position, sub_position):
	with pytest.raises(ValueError, match="Posição não classificada"):
		categoria_posicao(position, sub_position)
