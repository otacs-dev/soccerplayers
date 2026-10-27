"""Helpers para o tamanho de efeito dentro da análise estatística."""

from src.analise.testes import tamanho_efeito


def calcular_efeito(amostra_a, amostra_b):
	"""Alias para o cálculo de efeito em comparação entre grupos."""
	return tamanho_efeito(amostra_a, amostra_b)


__all__ = ["calcular_efeito", "tamanho_efeito"]
