"""
Coleta de estatísticas por temporada no Sofascore (passes, dribles, duelos etc.).

Rodar da raiz do projeto (a pasta que contém src/, config/ e data/):

    python -m src.coleta.sofascore ids       # acha o ID de cada jogador no Sofascore
    python -m src.coleta.sofascore coletar   # baixa as estatísticas por temporada

Entradas : data/processed/jogadores_validos.csv  (gerado pelo transfermarkt.py)
Saídas   : data/manual/ids_sofascore.csv         (conferir à mão os "nao_encontrado")
           data/interim/sofascore_temporada.csv  (formato longo: jogador, temporada,
                                                  torneio, metrica, valor)
           data/raw/sofascore/*.json             (cache; nunca editar)

Observações importantes
-----------------------
* A API do Sofascore NÃO é oficial e pode mudar a qualquer momento. Confira os
  termos de uso do site antes de coletar e mantenha a pausa entre requisições.
* O jogador é identificado pelo ID do Transfermarkt (player_id). O ID do Sofascore
  é descoberto pelo nome E pela data de nascimento, nunca só pelo nome.
* Tudo que é baixado fica em cache: se o script cair no meio, é só rodar de novo
  que ele continua de onde parou, sem repetir requisições.
* Os nomes das métricas são guardados exatamente como a API devolve. A escolha de
  quais entram nos índices fica em config/metricas.yaml, depois de olhar os dados.
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlencode
from curl_cffi.requests import Session

import pandas as pd

try:
    # curl_cffi imita a "impressão digital" TLS de um navegador real. O Sofascore
    # devolve 403 para o requests comum, mesmo com cabeçalhos de navegador.
    from curl_cffi import requests as http
except ImportError:
    sys.exit("Falta a biblioteca curl_cffi. Rode: pip install curl_cffi")

from config import settings

# Carrega variáveis do .env se existir
ENV_PATH = settings.RAIZ / ".env"
if ENV_PATH.exists():
    for linha in ENV_PATH.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

BASE = "https://www.sofascore.com/api/v1"
DIR_CACHE = settings.DIR_RAW / "sofascore"
ARQ_IDS = settings.DIR_MANUAL / "ids_sofascore.csv"
ARQ_SAIDA = settings.DIR_INTERIM / "sofascore_temporada.csv"

# Valores opcionais: se não existirem no settings.py, usa estes padrões.
PAUSA = getattr(settings, "PAUSA_SEGUNDOS", 1.5)
ANO_INICIAL = getattr(settings, "ANO_INICIAL_COLETA", 2013)

COLUNAS_IDS = ["id_tm", "nome", "id_sofascore", "status"]

SESSAO = Session(impersonate="chrome")
SESSAO.headers.update({
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Accept": "application/json, text/plain, */*",
})

# Injeta cookie do Sofascore (sofa_captcha) se configurado via .env ou SOFASCORE_COOKIE
COOKIE_INICIAL = os.getenv("SOFASCORE_COOKIE", "").strip()
if COOKIE_INICIAL:
    if not COOKIE_INICIAL.startswith("sofa_captcha=") and "=" not in COOKIE_INICIAL:
        COOKIE_INICIAL = f"sofa_captcha={COOKIE_INICIAL}"
    SESSAO.headers["Cookie"] = COOKIE_INICIAL


def definir_cookie(cookie):
    """Atualiza a sessão com o cookie informado."""
    if not cookie:
        return
    cookie = cookie.strip()
    if not cookie.startswith("sofa_captcha=") and "=" not in cookie:
        cookie = f"sofa_captcha={cookie}"
    SESSAO.headers["Cookie"] = cookie


# --------------------------------------------------------------------------
# HTTP com cache
# --------------------------------------------------------------------------
def _arquivo_cache(chave):
    nome = re.sub(r"[^A-Za-z0-9]+", "_", chave).strip("_")[:180]
    return DIR_CACHE / f"{nome}.json"


def get(caminho, params=None):
    """GET na API com cache em disco. Devolve dict ({'_erro': 404} se não existe)."""
    chave = caminho + ("?" + urlencode(params) if params else "")
    arq = _arquivo_cache(chave)
    if arq.exists():
        return json.loads(arq.read_text(encoding="utf-8"))

    DIR_CACHE.mkdir(parents=True, exist_ok=True)
    for tentativa in range(4):
        resp = SESSAO.get(BASE + caminho, params=params, timeout=20)
        time.sleep(PAUSA)
        if resp.status_code == 200:
            dados = resp.json()
            arq.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
            return dados
        if resp.status_code == 404:
            dados = {"_erro": 404}
            arq.write_text(json.dumps(dados), encoding="utf-8")
            return dados
        if resp.status_code == 429:  # muitas requisições: espera e tenta de novo
            espera = 30 * (tentativa + 1)
            print(f"  429 (limite de requisições). Aguardando {espera}s...")
            time.sleep(espera)
            continue
        if resp.status_code == 403:
            raise RuntimeError(
                "403 Forbidden: o Sofascore bloqueou temporariamente a requisição por limite de taxa (WAF).\n"
                "Aguarde alguns minutos ou aumente PAUSA_SEGUNDOS em config/settings.py.\n"
                "O que já foi baixado fica salvo em data/raw/sofascore/ e não será repetido."
            )
        resp.raise_for_status()
    raise RuntimeError(f"Falhou após várias tentativas: {caminho}")


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def ano_inicio(rotulo):
    """'24/25' -> 2024 ; '2024' -> 2024 ; formato desconhecido -> None."""
    if not rotulo:
        return None
    m = re.match(r"^(\d{2,4})(?:/(\d{2,4}))?$", str(rotulo).strip())
    if not m:
        return None
    ano = int(m.group(1))
    if ano < 100:
        ano += 2000 if ano < 90 else 1900
    return ano


def rotulo_temporada(rotulo):
    """Padroniza para '2024/25', igual ao por90.py."""
    ano = ano_inicio(rotulo)
    return None if ano is None else f"{ano}/{str(ano + 1)[-2:]}"


def ler_ids():
    if ARQ_IDS.exists():
        return pd.read_csv(ARQ_IDS, dtype=str, encoding="utf-8-sig").fillna("")
    return pd.DataFrame(columns=COLUNAS_IDS)


# --------------------------------------------------------------------------
# Passo 1: descobrir o ID do Sofascore de cada jogador
# --------------------------------------------------------------------------
def buscar_id(nome, nascimento):
    """Procura pelo nome e confirma pela data de nascimento. None se não achar."""
    for consulta in dict.fromkeys([nome, sem_acento(nome)]):
        resultado = get("/search/all", {"q": consulta})
        candidatos = [r["entity"]["id"] for r in resultado.get("results", [])
                      if r.get("type") == "player" and r.get("entity")][:5]
        for pid in candidatos:
            info = get(f"/player/{pid}").get("player", {})
            ts = info.get("dateOfBirthTimestamp")
            if ts is None:
                continue
            nasc = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
            if nasc == nascimento:
                return str(pid)
    return None


def cmd_ids():
    validos = pd.read_csv(settings.ARQ_VALIDOS_FINAL, encoding="utf-8-sig")
    atual = ler_ids().set_index("id_tm", drop=False)
    linhas = []

    for _, j in validos.iterrows():
        id_tm = str(j["player_id"])
        # Respeita o que já está preenchido (inclusive correções feitas à mão)
        if id_tm in atual.index and atual.loc[id_tm, "id_sofascore"]:
            linhas.append(atual.loc[id_tm].to_dict())
            continue

        pid = buscar_id(j["nome"], str(j["date_of_birth"])[:10])
        status = "ok" if pid else "nao_encontrado"
        print(f"{j['nome']:<28} -> {pid or 'NÃO ENCONTRADO'}")
        linhas.append({"id_tm": id_tm, "nome": j["nome"],
                       "id_sofascore": pid or "", "status": status})

    settings.DIR_MANUAL.mkdir(parents=True, exist_ok=True)
    saida = pd.DataFrame(linhas, columns=COLUNAS_IDS)
    saida.to_csv(ARQ_IDS, index=False, encoding="utf-8-sig")

    faltando = saida[saida["id_sofascore"] == ""]
    print(f"\nSalvo em {ARQ_IDS} ({len(saida) - len(faltando)}/{len(saida)} encontrados).")
    if len(faltando):
        print("Preencha à mão o id_sofascore de:", ", ".join(faltando["nome"]))
        print("(o ID é o número no fim do link do jogador em sofascore.com)")


# --------------------------------------------------------------------------
# Passo 2: baixar as estatísticas por temporada e torneio
# --------------------------------------------------------------------------
def cmd_coletar():
    ids = ler_ids()
    ids = ids[ids["id_sofascore"] != ""]
    if ids.empty:
        sys.exit("Nenhum ID do Sofascore. Rode primeiro: python -m src.coleta.sofascore ids")

    linhas = []
    for n, (_, j) in enumerate(ids.iterrows(), start=1):
        sid = j["id_sofascore"]
        print(f"[{n}/{len(ids)}] {j['nome']}")
        temporadas = get(f"/player/{sid}/statistics/seasons")

        for ut in temporadas.get("uniqueTournamentSeasons", []):
            torneio = ut.get("uniqueTournament", {})
            for s in ut.get("seasons", []):
                ano = ano_inicio(s.get("year"))
                if ano is None or ano < ANO_INICIAL:
                    continue
                dados = get(f"/player/{sid}/unique-tournament/{torneio['id']}"
                            f"/season/{s['id']}/statistics/overall")
                estatisticas = dados.get("statistics") or {}
                for metrica, valor in estatisticas.items():
                    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                        continue
                    linhas.append({
                        "id_tm": j["id_tm"],
                        "id_sofascore": sid,
                        "temporada": rotulo_temporada(s.get("year")),
                        "torneio": torneio.get("name"),
                        "id_torneio": torneio.get("id"),
                        "metrica": metrica,
                        "valor": valor,
                        "fonte": "sofascore",
                    })

    settings.DIR_INTERIM.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(linhas).to_csv(ARQ_SAIDA, index=False, encoding="utf-8-sig")
    print(f"\nSalvo em {ARQ_SAIDA} ({len(linhas)} linhas).")
    print("Dica: confira a coluna 'torneio' e remova no por90/analise o que não for "
          "de time principal, se aparecer (ex.: competições de base).")


# --------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("comando", choices=["ids", "coletar"])
    parser.add_argument("--cookie", type=str, default=None,
                        help="Valor do cookie sofa_captcha copiado do navegador")
    args = parser.parse_args()

    if args.cookie:
        definir_cookie(args.cookie)

    {"ids": cmd_ids, "coletar": cmd_coletar}[args.comando]()
