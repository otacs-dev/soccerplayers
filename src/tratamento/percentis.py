"""Classificação posicional usada para os percentis do pipeline."""

from __future__ import annotations


def categoria_posicao(position: str, sub_position: str | None = None) -> str:
	"""Resolve categorias conhecidas e rejeita posições não classificadas."""
	posicao = str(position or "").strip()
	sub_posicao = str(sub_position or "").strip()

	if posicao == "Goalkeeper" and sub_posicao in {"", "Goalkeeper"}:
		return "goleiro"
	if posicao == "Defender":
		if sub_posicao == "Centre-Back":
			return "zagueiro"
		if sub_posicao in {"Left-Back", "Right-Back"}:
			return "lateral"
	if posicao == "Midfield":
		if sub_posicao in {"Defensive Midfield", "Central Midfield"}:
			return "meio_campista_defensivo_central"
		if sub_posicao in {
			"Attacking Midfield",
			"Left Winger",
			"Right Winger",
			"Left Midfield",
			"Right Midfield",
		}:
			return "meia_ofensivo_ponta"
	if posicao == "Attack":
		if sub_posicao in {"Attacking Midfield", "Left Winger", "Right Winger"}:
			return "meia_ofensivo_ponta"
		if sub_posicao in {"Centre-Forward", "Second Striker"}:
			return "centroavante"

	raise ValueError(
		f"Posição não classificada: position={posicao!r}, "
		f"sub_position={sub_posicao!r}."
	)
