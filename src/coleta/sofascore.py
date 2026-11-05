"""Importa snapshots locais e autorizados de métricas por temporada.

O projeto não consulta a API do Sofascore nem tenta contornar controles de acesso.
Prepare um CSV local com o identificador Transfermarkt ``id_tm`` e as colunas
``temporada``, ``torneio``, ``metrica`` e ``valor``; depois execute:

    python -m src.coleta.sofascore importar caminho/para/snapshot.csv --destino profissionais
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import settings


COLUNAS_OBRIGATORIAS = {"id_tm", "temporada", "torneio", "metrica", "valor"}
COLUNAS_SAIDA = [
	"id_tm",
	"id_sofascore",
	"temporada",
	"torneio",
	"id_torneio",
	"metrica",
	"valor",
	"fonte",
]
DESTINOS = {
	"amostra": "sofascore_temporada.csv",
	"profissionais": "sofascore_profissionais.csv",
}


def importar_snapshot(entrada: Path, destino: str = "amostra") -> Path:
	"""Valida e grava um snapshot CSV local no formato usado pelo pipeline."""
	if destino not in DESTINOS:
		raise ValueError(f"Destino inválido: {destino!r}. Use um de {sorted(DESTINOS)}.")
	if not entrada.is_file():
		raise FileNotFoundError(f"Snapshot local não encontrado: {entrada}")

	dados = pd.read_csv(entrada, encoding="utf-8-sig")
	dados.columns = [str(coluna).strip() for coluna in dados.columns]
	faltantes = COLUNAS_OBRIGATORIAS.difference(dados.columns)
	if faltantes:
		raise ValueError(f"O snapshot precisa conter as colunas: {sorted(faltantes)}.")
	if dados.empty:
		raise ValueError("O snapshot local está vazio.")

	dados["id_tm"] = pd.to_numeric(dados["id_tm"], errors="coerce")
	if dados["id_tm"].isna().any() or (dados["id_tm"] % 1 != 0).any():
		raise ValueError("A coluna 'id_tm' precisa conter IDs Transfermarkt inteiros.")
	dados["id_tm"] = dados["id_tm"].astype("int64")
	dados["valor"] = pd.to_numeric(dados["valor"], errors="coerce")
	if dados["valor"].isna().any():
		raise ValueError("A coluna 'valor' contém valores ausentes ou não numéricos.")

	for coluna in ("temporada", "torneio", "metrica"):
		dados[coluna] = dados[coluna].astype("string").str.strip()
		if dados[coluna].isna().any() or dados[coluna].eq("").any():
			raise ValueError(f"A coluna '{coluna}' contém valores ausentes ou vazios.")

	chaves = ["id_tm", "temporada", "torneio", "metrica"]
	duplicados = dados.duplicated(chaves, keep=False)
	if duplicados.any():
		amostras = dados.loc[duplicados, chaves].head(5).to_dict("records")
		raise ValueError(
			"O snapshot contém chaves jogador-temporada-torneio-métrica duplicadas: "
			f"{amostras}"
		)

	for coluna in ("id_sofascore", "id_torneio"):
		if coluna not in dados:
			dados[coluna] = ""
	if "fonte" not in dados:
		dados["fonte"] = "snapshot_local_autorizado"
	dados = dados[COLUNAS_SAIDA]

	saida = settings.DIR_INTERIM / DESTINOS[destino]
	settings.DIR_INTERIM.mkdir(parents=True, exist_ok=True)
	dados.to_csv(saida, index=False, encoding="utf-8-sig")
	return saida


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	subparsers = parser.add_subparsers(dest="comando", required=True)
	importar = subparsers.add_parser("importar", help="Validar e importar um snapshot CSV local.")
	importar.add_argument("arquivo", type=Path, help="CSV local obtido e licenciado para uso.")
	importar.add_argument(
		"--destino",
		choices=sorted(DESTINOS),
		default="amostra",
		help="Tabela intermediária a atualizar.",
	)
	args = parser.parse_args()

	try:
		saida = importar_snapshot(args.arquivo, args.destino)
	except (FileNotFoundError, ValueError) as erro:
		parser.error(str(erro))
	print(f"Snapshot validado e salvo em {saida.relative_to(settings.RAIZ)}")


if __name__ == "__main__":
	main()
