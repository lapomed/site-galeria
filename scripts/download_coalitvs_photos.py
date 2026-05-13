#!/usr/bin/env python3
"""Baixa fotos dos 53 pesquisadores do COALITVS via discovery automatico.

Estrategia (em ordem, para cada pesquisador):
  1. Wikipedia REST API (en, depois pt) -> pega thumbnail oficial
  2. URL hardcoded de override (para casos especificos)
  3. Marca como FALHA no relatorio

Saida: media/coalitvs/<slug>.jpg + scripts/download_report.txt

Como rodar:
  python scripts/download_coalitvs_photos.py

O script eh idempotente: se ja existe media/coalitvs/<slug>.<ext>, pula.

Apos rodar:
  1. Confira media/coalitvs/ visualmente, delete fotos ruins
  2. Para os que falharam (ver download_report.txt), faca upload manual
     pelo admin: /admin/core/coalitvsmember/
  3. Commit + push -> Railway redeploya -> migration 0028 popula DB
"""

from __future__ import annotations
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# ============================================================
# 53 pesquisadores (espelho do core/migrations/0024_coalitvs_seed.py)
# Tuple: (name, group_slug, [optional manual_override_url])
# ============================================================
MEMBERS: list[tuple[str, str, str | None]] = [
    # ---------- INTERNACIONAIS ----------
    ("Ian Hodder",                       "internacional", None),
    ("Justin Leidwanger",                "internacional", None),
    ("Andrea Berlin",                    "internacional", None),
    ("C Michael Barton",                 "internacional", None),
    ("Jaś Elsner",                       "internacional", None),
    ("Mark Altaweel",                    "internacional", None),
    ("Carlos Augusto Ribeiro Machado",   "internacional", None),
    ("Gregg E. Gardner",                 "internacional", None),
    ("Achim Lichtenberger",              "internacional", None),  # NB: seed tem "Litchenberger" (typo)
    ("Florian Janoscha Kreppner",        "internacional", None),
    ("Naoise Mac Sweeney",               "internacional", None),
    ("Matteo Bigongiari",                "internacional", None),
    ("Aris Ymir Politopoulos",           "internacional", None),
    ("Marta Lorenzon",                   "internacional", None),
    ("Hannah M. Moots",                  "internacional", None),
    ("Margozata Kajzer",                 "internacional", None),  # provavelmente "Małgorzata"
    ("Oren Tal",                         "internacional", None),
    ("Alexander Fantalkin",              "internacional", None),
    ("Mordechai Aviam",                  "internacional", None),
    ("Carlos Jorge Soares Fabião",       "internacional", None),
    ("Jose Remesal Rodriguez",           "internacional", None),
    ("Jérémie Schiettecatte",            "internacional", None),
    ("Benjamin Isakhan",                 "internacional", None),
    ("Rodrigo Laham Cohen",              "internacional", None),
    ("Roberto R. Rodríguez",             "internacional", None),
    ("Bülent Arikan",                    "internacional", None),
    ("Ergün Lafli",                      "internacional", None),
    ("Hanan Charaf",                     "internacional", None),
    # ---------- NACIONAIS ----------
    ("Marcio Teixeira-Bastos",                    "nacional", None),
    ("Paulo Martins",                             "nacional", None),
    ("Marcelo Knörich Zuffo",                     "nacional", None),
    ("João Felipe Ferreira Gonçalves",            "nacional", None),
    ("Suzana Chwarts",                            "nacional", None),
    ("Júlio César Magalhães de Oliveira",         "nacional", None),
    ("Beatriz Piccolotto Siqueira Bueno",         "nacional", None),
    ("Eliane Aparecida Del Lama",                 "nacional", None),
    ("Lucelene Martins",                          "nacional", None),
    ("Márcia de Almeida Rizzutto",                "nacional", None),
    ("Ximena Suarez Villagran",                   "nacional", None),
    ("Maria Isabel D'Agostino Fleming",           "nacional", None),
    ("Vagner Carvalheiro Porto",                  "nacional", None),
    ("Juliana Figueira da Hora",                  "nacional", None),
    ("Pedro Paulo Funari",                        "nacional", None),
    ("Ivan Esperança Rocha",                      "nacional", None),
    ("Margarida Maria de Carvalho",               "nacional", None),
    ("Pedro Merlussi",                            "nacional", None),
    ("Filipe Noé da Silva",                       "nacional", None),
    ("Flávio de Leão Bastos Pereira",             "nacional", None),
    ("Claudio Walter Gomez Duarte",               "nacional", None),
    ("Márcia Severina Vasques",                   "nacional", None),
    ("Gilvan Ventura da Silva",                   "nacional", None),
    ("Lucio Menezes Ferreira",                    "nacional", None),
    ("Kátia Maria Paim Pozzer",                   "nacional", None),
]


# ============================================================
# Config
# ============================================================
ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = ROOT / "media" / "coalitvs"
REPORT = Path(__file__).resolve().parent / "download_report.txt"

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": UA, "Accept": "*/*"}


# ============================================================
# Helpers
# ============================================================
def slugify_local(name: str) -> str:
    """Reproduz django.utils.text.slugify para nao depender do Django."""
    import unicodedata
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[-\s]+", "-", s)
    return s


def http_get(url: str, timeout: int = 15) -> bytes | None:
    """GET com user-agent e tratamento de erro. Retorna bytes ou None."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as exc:
        print(f"   ! HTTP error: {exc}", file=sys.stderr)
        return None


def wikipedia_thumbnail(name: str, lang: str = "en") -> str | None:
    """Tenta o REST summary API. Retorna URL da imagem original (full size) ou None."""
    enc = urllib.parse.quote(name.replace(" ", "_"))
    api = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{enc}"
    data = http_get(api)
    if not data:
        return None
    try:
        j = json.loads(data)
    except Exception:
        return None
    # Preferir originalimage (resolucao alta) sobre thumbnail
    for key in ("originalimage", "thumbnail"):
        img = j.get(key) or {}
        src = img.get("source")
        if src and src.startswith("http"):
            return src
    return None


def extract_ext(url: str, content_type: str = "") -> str:
    """Determina extensao da imagem a partir da URL ou content-type."""
    m = re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", url, re.I)
    if m:
        return m.group(1).lower().replace("jpeg", "jpg")
    if "png" in content_type:
        return "png"
    if "webp" in content_type:
        return "webp"
    return "jpg"


def download(url: str, dest_no_ext: Path) -> Path | None:
    """Baixa imagem e salva. Retorna o path final ou None se falhar."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            ct = r.headers.get("Content-Type", "")
            data = r.read()
        ext = extract_ext(url, ct)
        out = dest_no_ext.with_suffix(f".{ext}")
        out.write_bytes(data)
        return out
    except Exception as exc:
        print(f"   ! Download error: {exc}", file=sys.stderr)
        return None


# ============================================================
# Main
# ============================================================
def process(name: str, group: str, override: str | None) -> tuple[str, str, str]:
    """Processa um pesquisador. Retorna (status, slug, info)."""
    slug = slugify_local(name)
    print(f"\n[{group}/{slug}] {name}")

    # 0. Ja existe arquivo?
    target_no_ext = MEDIA_DIR / slug
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = target_no_ext.with_suffix(f".{ext}")
        if p.exists():
            print(f"   = ja existe: {p.name}")
            return ("EXISTS", slug, p.name)

    # 1. Override manual
    if override:
        print(f"   -> override: {override}")
        out = download(override, target_no_ext)
        if out:
            return ("OK_OVERRIDE", slug, out.name)

    # 2. Wikipedia en
    img = wikipedia_thumbnail(name, lang="en")
    if img:
        print(f"   -> wikipedia/en: {img[:80]}...")
        out = download(img, target_no_ext)
        if out:
            return ("OK_WIKIPEDIA_EN", slug, out.name)

    # 3. Wikipedia pt (mais util pra brasileiros e ibericos)
    img = wikipedia_thumbnail(name, lang="pt")
    if img:
        print(f"   -> wikipedia/pt: {img[:80]}...")
        out = download(img, target_no_ext)
        if out:
            return ("OK_WIKIPEDIA_PT", slug, out.name)

    # 4. Falhou
    print(f"   X NAO ENCONTRADO")
    return ("FAIL", slug, "sem foto encontrada")


def main() -> int:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, str, str, str]] = []  # (status, group, slug, info)

    for name, group, override in MEMBERS:
        status, slug, info = process(name, group, override)
        results.append((status, group, slug, info))
        # Cortesia: pausa pra nao machucar a Wikipedia
        time.sleep(0.3)

    # Relatorio
    by_status: dict[str, list[str]] = {}
    for status, group, slug, info in results:
        by_status.setdefault(status, []).append(f"  - {group}/{slug}  ({info})")

    lines = ["COALITVS Photo Download Report", "=" * 50, ""]
    for status in ("OK_WIKIPEDIA_EN", "OK_WIKIPEDIA_PT", "OK_OVERRIDE", "EXISTS", "FAIL"):
        items = by_status.get(status, [])
        lines.append(f"[{status}] {len(items)}")
        lines.extend(items)
        lines.append("")
    REPORT.write_text("\n".join(lines))

    fail_count = len(by_status.get("FAIL", []))
    ok_count = sum(len(by_status.get(s, [])) for s in ("OK_WIKIPEDIA_EN", "OK_WIKIPEDIA_PT", "OK_OVERRIDE"))
    exist_count = len(by_status.get("EXISTS", []))
    total = len(results)
    print("\n" + "=" * 50)
    print(f"Total: {total}  |  Baixados: {ok_count}  |  Ja existia: {exist_count}  |  Falhou: {fail_count}")
    print(f"Relatorio: {REPORT}")
    print(f"Fotos:     {MEDIA_DIR}")
    if fail_count:
        print(f"\n⚠  {fail_count} pesquisadores sem foto. Veja o relatorio e:")
        print("   - Adicione URL no campo `override` do MEMBERS no topo deste script, OU")
        print("   - Faca upload manual pelo admin: /admin/core/coalitvsmember/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
