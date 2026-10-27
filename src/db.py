"""Inicialização e carga do banco SQLite analítico do projeto.

Execute na raiz do repositório após rodar o pipeline:

    python -m src.db
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Any

from config import settings


ARQ_BANCO = settings.DIR_PROCESSED / "formacao_jogadores.sqlite3"
DIR_SQL = settings.RAIZ / "sql"
ACADEMIAS = {
	1: ("Barcelona", "Espanha"),
	2: ("Real Madrid", "Espanha"),
	3: ("Manchester City", "Inglaterra"),
	4: ("Liverpool", "Inglaterra"),
}
ID_ACADEMIA = {nome: clube_id for clube_id, (nome, _) in ACADEMIAS.items()}


def conectar(caminho: Path = ARQ_BANCO) -> sqlite3.Connection:
	"""Abre o banco com chaves estrangeiras habilitadas."""
	caminho.parent.mkdir(parents=True, exist_ok=True)
	conexao = sqlite3.connect(caminho)
	conexao.row_factory = sqlite3.Row
	conexao.execute("PRAGMA foreign_keys = ON")
	return conexao


def inicializar_esquema(conexao: sqlite3.Connection) -> None:
	"""Aplica os scripts SQL em ordem."""
	for nome in ("01_schema.sql", "02_indices.sql", "03_views.sql"):
		(conexao.executescript((DIR_SQL / nome).read_text(encoding="utf-8")))


def _ler_csv(caminho: Path) -> list[dict[str, str]]:
	if not caminho.exists():
		return []
	with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
		return list(csv.DictReader(arquivo))


def _opcional_texto(valor: Any) -> str | None:
	if valor is None:
		return None
	texto = str(valor).strip()
	return texto if texto and texto.lower() not in {"nan", "none", "null"} else None


def _opcional_numero(valor: Any) -> float | None:
	texto = _opcional_texto(valor)
	if texto is None:
		return None
	try:
		return float(texto)
	except ValueError:
		return None


def _bool(valor: Any) -> int | None:
	texto = _opcional_texto(valor)
	if texto is None:
		return None
	return int(texto.lower() in {"true", "1", "sim", "yes"})


def carregar_dados(conexao: sqlite3.Connection) -> dict[str, int]:
	"""Recarrega tabelas analíticas a partir dos CSVs do pipeline."""
	validos = _ler_csv(settings.DIR_PROCESSED / "jogadores_validos.csv")
	indices = _ler_csv(settings.DIR_PROCESSED / "indices_jogadores.csv")
	if not validos or not indices:
		raise FileNotFoundError("Rode `python run_pipeline.py` antes de carregar o banco.")

	conexao.execute("DELETE FROM estatistica_temporada")
	conexao.execute("DELETE FROM indice_jogador")
	conexao.execute("DELETE FROM passagem_base")
	conexao.execute("DELETE FROM jogador")
	conexao.execute("DELETE FROM clube")
	conexao.executemany(
		"INSERT INTO clube (clube_id, nome, pais) VALUES (?, ?, ?)",
		[(clube_id, nome, pais) for clube_id, (nome, pais) in ACADEMIAS.items()],
	)

	for linha in validos:
		player_id = int(linha["player_id"])
		clube_id = ID_ACADEMIA[linha["clube"]]
		conexao.execute(
			"""INSERT INTO jogador (
				player_id, nome, position, sub_position, date_of_birth, height_in_cm,
				estreia, minutos_profissionais, jogos_profissionais, url_perfil
			) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
			(
				player_id, linha["nome"], _opcional_texto(linha.get("position")),
				_opcional_texto(linha.get("sub_position")), _opcional_texto(linha.get("date_of_birth")),
				_opcional_numero(linha.get("height_in_cm")), _opcional_texto(linha.get("estreia")),
				_opcional_numero(linha.get("minutos")), _opcional_numero(linha.get("jogos")),
				_opcional_texto(linha.get("url")),
			),
		)
		conexao.execute(
			"""INSERT INTO passagem_base (
				player_id, clube_id, formado_confirmado, fonte_conferencia
			) VALUES (?, ?, ?, ?)""",
			(
				player_id, clube_id,
				int((_opcional_texto(linha.get("formado_confirmado")) or "").lower() == "sim"),
				_opcional_texto(linha.get("fonte_conferencia")),
			),
		)

	for linha in indices:
		conexao.execute(
			"""INSERT INTO indice_jogador (
				player_id, indice_tecnico, indice_explosivo, cobertura_tecnico,
				cobertura_explosivo, n_metricas_tecnico, n_metricas_explosivo
			) VALUES (?, ?, ?, ?, ?, ?, ?)""",
			(
				int(linha["player_id"]), _opcional_numero(linha.get("indice_tecnico")),
				_opcional_numero(linha.get("indice_explosivo")),
				_opcional_numero(linha.get("cobertura_tecnico")),
				_opcional_numero(linha.get("cobertura_explosivo")),
				_opcional_numero(linha.get("n_metricas_tecnico")),
				_opcional_numero(linha.get("n_metricas_explosivo")),
			),
		)

	stats = 0
	for nome_arquivo, fonte in (
		("por90_appearances.csv", "appearances"),
		("por90_sofascore.csv", "sofascore"),
	):
		for linha in _ler_csv(settings.DIR_INTERIM / nome_arquivo):
			player_id = _opcional_numero(linha.get("player_id") or linha.get("id_tm"))
			if player_id is None:
				continue
			temporada = _opcional_texto(linha.get("temporada"))
			if temporada is None:
				continue
			if fonte == "sofascore":
				metricas = [(
					_opcional_texto(linha.get("metrica")), _opcional_numero(linha.get("valor")),
					_opcional_numero(linha.get("minutos")), _opcional_numero(linha.get("valor_por90")),
					_bool(linha.get("amostra_suficiente")),
				)]
			else:
				metricas = []
				for metrica in ("gols", "assistencias", "amarelos", "vermelhos"):
					metricas.append((
						metrica, _opcional_numero(linha.get(metrica)),
						_opcional_numero(linha.get("minutos")),
						_opcional_numero(linha.get(f"{metrica}_por90")),
						_bool(linha.get("amostra_suficiente")),
					))
			for metrica, valor, minutos, valor_por90, amostra in metricas:
				if metrica is None:
					continue
				conexao.execute(
					"""INSERT OR REPLACE INTO estatistica_temporada (
						player_id, temporada, torneio, metrica, valor, minutos,
						valor_por90, amostra_suficiente, fonte
					) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
					(
						int(player_id), temporada, _opcional_texto(linha.get("torneio")) or "",
						metrica, valor, minutos, valor_por90, amostra, fonte,
					),
				)
				stats += 1

	return {
		"academias": len(ACADEMIAS),
		"jogadores": len(validos),
		"indices": len(indices),
		"estatisticas": stats,
	}


def inicializar_banco(caminho: Path = ARQ_BANCO) -> dict[str, int]:
	"""Cria o esquema, importa as tabelas analíticas e retorna contagens."""
	with conectar(caminho) as conexao:
		inicializar_esquema(conexao)
		return carregar_dados(conexao)


def main() -> None:
	contagens = inicializar_banco()
	print(f"Banco pronto: {ARQ_BANCO.relative_to(settings.RAIZ)}")
	for tabela, quantidade in contagens.items():
		print(f"- {tabela}: {quantidade}")


if __name__ == "__main__":
	main()