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
	if texto.lower() in {"true", "1", "sim", "yes"}:
		return 1
	if texto.lower() in {"false", "0", "não", "nao", "no"}:
		return 0
	raise ValueError(f"Valor booleano inválido: {valor!r}")


def carregar_dados(conexao: sqlite3.Connection) -> dict[str, int]:
	"""Recarrega jogadores, métricas e resultados analíticos a partir dos CSVs."""
	validos = _ler_csv(settings.DIR_PROCESSED / "jogadores_validos.csv")
	indices = _ler_csv(settings.DIR_PROCESSED / "indices_jogadores.csv")
	if not validos or not indices:
		raise FileNotFoundError("Rode `python run_pipeline.py` antes de carregar o banco.")

	ids_validos = {int(linha["player_id"]) for linha in validos}
	ids_indices = {int(linha["player_id"]) for linha in indices}
	if ids_validos != ids_indices:
		raise ValueError(
			"A seleção validada e os índices não contêm os mesmos jogadores "
			f"(sem índice: {sorted(ids_validos - ids_indices)[:5]}; "
			f"sem seleção: {sorted(ids_indices - ids_validos)[:5]})."
		)
	clubes_validos = {linha["clube"] for linha in validos}
	clubes_desconhecidos = clubes_validos.difference(ID_ACADEMIA)
	if clubes_desconhecidos:
		raise ValueError(f"Academias não cadastradas no banco: {sorted(clubes_desconhecidos)}")

	percentis = _ler_csv(settings.DIR_PROCESSED / "percentis_metricas.csv")
	cobertura = _ler_csv(settings.DIR_PROCESSED / "cobertura_metricas.csv")
	descritivas = _ler_csv(settings.DIR_PROCESSED / "descritiva_academias.csv")
	kruskal = _ler_csv(settings.DIR_PROCESSED / "kruskal_wallis.csv")
	pares = _ler_csv(settings.DIR_PROCESSED / "mann_whitney_bonferroni.csv")
	if not all((percentis, cobertura, descritivas, kruskal, pares)):
		raise FileNotFoundError(
			"Faltam CSVs de análise em data/processed/. Rode `python run_pipeline.py` para "
			"gerar percentis, cobertura, descritiva e testes antes de carregar o banco."
		)

	percentis_com_ids_invalidos = [
		linha["player_id"]
		for linha in percentis
		if int(linha["player_id"]) not in ids_validos
	]
	if percentis_com_ids_invalidos:
		raise ValueError(
			"Há percentis de jogadores fora da seleção validada: "
			f"{percentis_com_ids_invalidos[:5]}."
		)

	conexao.execute("DELETE FROM estatistica_temporada")
	conexao.execute("DELETE FROM carreira_jogador")
	conexao.execute("DELETE FROM teste_mann_whitney")
	conexao.execute("DELETE FROM teste_kruskal_wallis")
	conexao.execute("DELETE FROM descritiva_academia")
	conexao.execute("DELETE FROM cobertura_metrica")
	conexao.execute("DELETE FROM percentil_metrica")
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

	conexao.executemany(
		"""INSERT INTO percentil_metrica (
			player_id, position, categoria, indice, metrica, valor,
			grupo_percentil, percentil_0_100, peso
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
		[
			(
				int(linha["player_id"]), _opcional_texto(linha.get("position")),
				_opcional_texto(linha.get("categoria")), linha["indice"], linha["metrica"],
				_opcional_numero(linha.get("valor")), _opcional_texto(linha.get("grupo_percentil")),
				_opcional_numero(linha.get("percentil_0_100")), _opcional_numero(linha.get("peso")) or 0.0,
			)
			for linha in percentis
		],
	)
	conexao.executemany(
		"""INSERT INTO cobertura_metrica (
			indice, metrica, n_jogadores, peso, n_amostra, proporcao_coberta
		) VALUES (?, ?, ?, ?, ?, ?)""",
		[
			(
				linha["indice"], linha["metrica"], int(linha["n_jogadores"]),
				_opcional_numero(linha.get("peso")), int(linha["n_amostra"]),
				_opcional_numero(linha.get("proporcao_coberta")),
			)
			for linha in cobertura
		],
	)
	conexao.executemany(
		"""INSERT INTO descritiva_academia (
			academia, metrica, n, n_ausentes, mediana, q1, q3, minimo, maximo
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
		[
			(
				linha["academia"], linha["metrica"], int(linha["n"]),
				int(linha["n_ausentes"]), _opcional_numero(linha.get("mediana")),
				_opcional_numero(linha.get("q1")), _opcional_numero(linha.get("q3")),
				_opcional_numero(linha.get("minimo")), _opcional_numero(linha.get("maximo")),
			)
			for linha in descritivas
		],
	)
	conexao.executemany(
		"""INSERT INTO teste_kruskal_wallis (
			metrica, statistic, p_value, significativo, alpha, n_grupos
		) VALUES (?, ?, ?, ?, ?, ?)""",
		[
			(
				linha["metrica"], _opcional_numero(linha.get("statistic")),
				_opcional_numero(linha.get("p_value")), _bool(linha.get("significativo")),
				_opcional_numero(linha.get("alpha")), int(linha["n_grupos"]),
			)
			for linha in kruskal
		],
	)
	conexao.executemany(
		"""INSERT INTO teste_mann_whitney (
			metrica, grupo_a, grupo_b, statistic, p_value, p_bonferroni,
			significativo, median_diff, rank_biserial
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
		[
			(
				linha["metrica"], linha["grupo_a"], linha["grupo_b"],
				_opcional_numero(linha.get("statistic")), _opcional_numero(linha.get("p_value")),
				_opcional_numero(linha.get("p_bonferroni")), _bool(linha.get("significativo")),
				_opcional_numero(linha.get("median_diff")), _opcional_numero(linha.get("rank_biserial")),
			)
			for linha in pares
		],
	)

	carreira = _ler_csv(settings.DIR_PROCESSED / "carreira_jogadores.csv")
	if carreira:
		if {int(linha["player_id"]) for linha in carreira} != ids_validos:
			raise ValueError("carreira_jogadores.csv não contém exatamente os jogadores validados.")
		conexao.executemany(
			"""INSERT INTO carreira_jogador (
				player_id, temporadas_com_aparicoes, jogos_profissionais,
				minutos_profissionais, gols_profissionais, assistencias_profissionais,
				idade_estreia
			) VALUES (?, ?, ?, ?, ?, ?, ?)""",
			[
				(
					int(linha["player_id"]), int(linha["temporadas_com_aparicoes"]),
					_opcional_numero(linha.get("jogos_profissionais")),
					_opcional_numero(linha.get("minutos_profissionais")),
					_opcional_numero(linha.get("gols_profissionais")),
					_opcional_numero(linha.get("assistencias_profissionais")),
					_opcional_numero(linha.get("idade_estreia")),
				)
				for linha in carreira
			],
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
		"percentis": len(percentis),
		"cobertura": len(cobertura),
		"descritivas": len(descritivas),
		"testes_kruskal": len(kruskal),
		"testes_mann_whitney": len(pares),
		"carreira": len(carreira),
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