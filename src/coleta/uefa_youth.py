"""Importação local de participações na UEFA Youth League.

O módulo não faz scraping. Use um CSV autorizado com ``player_id`` Transfermarkt,
``academia``, ``temporada``, ``competicao`` e, opcionalmente, ``url``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import settings
from src.coleta._trajetoria import normalizar_temporadas


def ler_participacoes(caminho: str | Path) -> pd.DataFrame:
	"""Lê e valida um CSV local de participações juvenis."""
	dados = pd.read_csv(caminho, dtype={"temporada": "string", "competicao": "string"}, encoding="utf-8-sig")
	return normalizar_temporadas(dados, fonte="uefa_youth_league", incluir_competicao=True)


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("csv", type=Path, help="CSV com player_id, academia, temporada e competicao")
	parser.add_argument(
		"--saida",
		type=Path,
		default=settings.DIR_INTERIM / "trajetoria_uefa_youth.csv",
		help="Caminho do CSV normalizado",
	)
	args = parser.parse_args()
	resultado = ler_participacoes(args.csv)
	args.saida.parent.mkdir(parents=True, exist_ok=True)
	resultado.to_csv(args.saida, index=False, encoding="utf-8-sig")
	print(f"Participações UEFA Youth League normalizadas: {len(resultado)} linhas em {args.saida}")


if __name__ == "__main__":
	main()