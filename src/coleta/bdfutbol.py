"""Importação local de temporadas de formação documentadas no BDFutbol.

O módulo não faz scraping. Use um CSV autorizado com ``player_id`` Transfermarkt,
``academia``, ``temporada`` e, opcionalmente, ``url``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import settings
from src.coleta._trajetoria import normalizar_temporadas


def ler_temporadas(caminho: str | Path) -> pd.DataFrame:
	"""Lê e valida o CSV local previamente obtido no BDFutbol."""
	dados = pd.read_csv(caminho, dtype={"temporada": "string"}, encoding="utf-8-sig")
	return normalizar_temporadas(dados, fonte="bdfutbol")


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("csv", type=Path, help="CSV local com player_id, academia e temporada")
	parser.add_argument(
		"--saida",
		type=Path,
		default=settings.DIR_INTERIM / "trajetoria_bdfutbol.csv",
		help="Caminho do CSV normalizado",
	)
	args = parser.parse_args()
	resultado = ler_temporadas(args.csv)
	args.saida.parent.mkdir(parents=True, exist_ok=True)
	resultado.to_csv(args.saida, index=False, encoding="utf-8-sig")
	print(f"Temporadas BDFutbol normalizadas: {len(resultado)} linhas em {args.saida}")


if __name__ == "__main__":
	main()