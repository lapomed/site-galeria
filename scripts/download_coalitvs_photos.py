#!/usr/bin/env python3
"""Baixa fotos dos 53 pesquisadores do COALITVS via discovery automatico.

Estrategia (em ordem, para cada pesquisador):
  1. URL hardcoded de override (se houver)
  2. Para cada variante do nome (original, ASCII, primeiro+ultimo):
     a. Wikipedia EN summary -> thumbnail
     b. Wikipedia PT summary -> thumbnail
     c. Wikidata wbsearchentities -> P18 (imagem) -> Commons FilePath
  3. Marca como FALHA no relatorio

Saida: media/coalitvs/<slug>.<ext> + scripts/download_report.txt

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
import argparse
import html
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

# Garante UTF-8 no stdout/stderr (Windows cp1252 quebra com nomes acentuados).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
# 53 pesquisadores (espelho do core/migrations/0024_coalitvs_seed.py)
# Tuple: (name, group_slug, institution, city, country, [optional override URL])
# ============================================================
MEMBERS: list[tuple[str, str, str, str, str, str | None]] = [
    # ---------- INTERNACIONAIS ----------
    ("Ian Hodder",                     "internacional", "Stanford University", "Stanford", "Estados Unidos", None),
    ("Justin Leidwanger",              "internacional", "Stanford University", "Stanford", "Estados Unidos", None),
    ("Andrea Berlin",                  "internacional", "Boston University", "Boston", "Estados Unidos", None),
    ("C Michael Barton",               "internacional", "Arizona State University", "Tempe", "Estados Unidos", None),
    ("Jaś Elsner",                     "internacional", "University of Oxford", "Oxford", "Reino Unido", None),
    ("Mark Altaweel",                  "internacional", "University College London", "Londres", "Reino Unido", None),
    ("Carlos Augusto Ribeiro Machado", "internacional", "University of St Andrews", "St Andrews", "Reino Unido", None),
    ("Gregg E. Gardner",               "internacional", "University of British Columbia", "Vancouver", "Canadá", None),
    ("Achim Lichtenberger",            "internacional", "Münster University", "Münster", "Alemanha", None),  # seed tem typo "Litchenberger"
    ("Florian Janoscha Kreppner",      "internacional", "Münster University", "Münster", "Alemanha", None),
    ("Naoise Mac Sweeney",             "internacional", "University of Vienna", "Viena", "Áustria", None),
    ("Matteo Bigongiari",              "internacional", "University of Florence", "Florença", "Itália", None),
    ("Aris Ymir Politopoulos",         "internacional", "Leiden University", "Leiden", "Países Baixos", None),
    ("Marta Lorenzon",                 "internacional", "University of Helsinki", "Helsinque", "Finlândia", None),
    ("Hannah M. Moots",                "internacional", "Stockholm University", "Estocolmo", "Suécia", None),
    ("Margozata Kajzer",               "internacional", "Polish Academy of Sciences", "Varsóvia", "Polônia", None),  # typo: "Małgorzata"
    ("Oren Tal",                       "internacional", "Tel Aviv University", "Tel Aviv", "Israel", None),
    ("Alexander Fantalkin",            "internacional", "Tel Aviv University", "Tel Aviv", "Israel", None),
    ("Mordechai Aviam",                "internacional", "Kinneret Academic College", "Tzemach", "Israel", None),
    ("Carlos Jorge Soares Fabião",     "internacional", "Universidade de Lisboa", "Lisboa", "Portugal", None),
    ("Jose Remesal Rodriguez",         "internacional", "Universitat de Barcelona", "Barcelona", "Espanha", None),
    ("Jérémie Schiettecatte",          "internacional", "CNRS-Paris", "Paris", "França", None),
    ("Benjamin Isakhan",               "internacional", "Deakin University", "Geelong", "Austrália", None),
    ("Rodrigo Laham Cohen",            "internacional", "Universidad de Buenos Aires", "Buenos Aires", "Argentina", None),
    ("Roberto R. Rodríguez",           "internacional", "Universidad Nacional de la Patagonia", "Comodoro Rivadavia", "Argentina", None),
    ("Bülent Arikan",                  "internacional", "Istanbul Technical University", "Istambul", "Turquia", None),
    ("Ergün Lafli",                    "internacional", "Dokuz Eylül University", "Esmirna", "Turquia", None),
    ("Hanan Charaf",                   "internacional", "Lebanese University", "Beirute", "Líbano", None),
    # ---------- NACIONAIS ----------
    ("Marcio Teixeira-Bastos",            "nacional", "DA FFLCH USP", "São Paulo", "Brasil", None),
    ("Paulo Martins",                     "nacional", "DLCV FFLCH USP", "São Paulo", "Brasil", None),
    ("Marcelo Knörich Zuffo",             "nacional", "Poli USP", "São Paulo", "Brasil", None),
    ("João Felipe Ferreira Gonçalves",    "nacional", "DA FFLCH USP", "São Paulo", "Brasil", None),
    ("Suzana Chwarts",                    "nacional", "FFLCH USP", "São Paulo", "Brasil", None),
    ("Júlio César Magalhães de Oliveira", "nacional", "DH FFLCH USP", "São Paulo", "Brasil", None),
    ("Beatriz Piccolotto Siqueira Bueno", "nacional", "FAU USP", "São Paulo", "Brasil", None),
    ("Eliane Aparecida Del Lama",         "nacional", "IGC USP", "São Paulo", "Brasil", None),
    ("Lucelene Martins",                  "nacional", "IGC USP", "São Paulo", "Brasil", None),
    ("Márcia de Almeida Rizzutto",        "nacional", "IF USP", "São Paulo", "Brasil", None),
    ("Ximena Suarez Villagran",           "nacional", "MAE USP", "São Paulo", "Brasil", None),
    ("Maria Isabel D'Agostino Fleming",   "nacional", "MAE USP", "São Paulo", "Brasil", None),
    ("Vagner Carvalheiro Porto",          "nacional", "MAE USP", "São Paulo", "Brasil", None),
    ("Juliana Figueira da Hora",          "nacional", "MAE USP", "São Paulo", "Brasil", None),
    ("Pedro Paulo Funari",                "nacional", "UNICAMP", "Campinas", "Brasil", None),
    ("Ivan Esperança Rocha",              "nacional", "UNESP Assis", "Assis", "Brasil", None),
    ("Margarida Maria de Carvalho",       "nacional", "UNESP Franca", "Franca", "Brasil", None),
    ("Pedro Merlussi",                    "nacional", "PUC-RJ", "Rio de Janeiro", "Brasil", None),
    ("Filipe Noé da Silva",               "nacional", "UDESC", "Florianópolis", "Brasil", None),
    ("Flávio de Leão Bastos Pereira",     "nacional", "Mackenzie", "São Paulo", "Brasil", None),
    ("Claudio Walter Gomez Duarte",       "nacional", "UNIMES", "Santos", "Brasil", None),
    ("Márcia Severina Vasques",           "nacional", "UFRN", "Natal", "Brasil", None),
    ("Gilvan Ventura da Silva",           "nacional", "UFES", "Vitória", "Brasil", None),
    ("Lucio Menezes Ferreira",            "nacional", "UFPEL", "Pelotas", "Brasil", None),
    ("Kátia Maria Paim Pozzer",           "nacional", "UFRGS", "Porto Alegre", "Brasil", None),
]


# ============================================================
# Config
# ============================================================
ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = ROOT / "media" / "coalitvs"
REPORT = Path(__file__).resolve().parent / "download_report.txt"

# Wikimedia User-Agent policy exige UA descritivo com contato.
# https://meta.wikimedia.org/wiki/User-Agent_policy
UA = "lapomed-coalitvs-bot/1.0 (https://lapomed-dev.up.railway.app; galhardo.dn@gmail.com) Python-urllib"
HEADERS = {"User-Agent": UA, "Accept": "*/*"}


# ============================================================
# Helpers
# ============================================================
def slugify_local(name: str) -> str:
    """Reproduz django.utils.text.slugify para nao depender do Django."""
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[-\s]+", "-", s)
    return s


def ascii_fold(name: str) -> str:
    """Remove acentos/diacriticos do nome (Ä -> A, ã -> a, ś -> s)."""
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def name_variants(name: str) -> list[str]:
    """Gera variantes de nome em ordem de preferencia, sem duplicatas."""
    variants: list[str] = [name]
    ascii_name = ascii_fold(name)
    if ascii_name != name:
        variants.append(ascii_name)
    # Primeiro + ultimo (drop middle names)
    parts = [p for p in name.split() if p]
    if len(parts) > 2:
        short = f"{parts[0]} {parts[-1]}"
        variants.append(short)
        short_ascii = ascii_fold(short)
        if short_ascii != short:
            variants.append(short_ascii)
    # Dedup mantendo ordem
    seen = set()
    out: list[str] = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def http_get(url: str, timeout: int = 15) -> bytes | None:
    """GET com user-agent e tratamento de erro. Retorna bytes ou None."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as exc:
        print(f"   ! HTTP error: {exc}", file=sys.stderr)
        return None


def http_get_json(url: str, timeout: int = 15) -> dict | None:
    data = http_get(url, timeout=timeout)
    if not data:
        return None
    try:
        return json.loads(data)
    except Exception:
        return None


# ----- Wikipedia -----
# Filenames que Wikipedia/Wikidata as vezes retornam mas NAO sao foto da pessoa
# (logos de redes sociais, placeholders, simbolos, badges, etc.)
BLOCKED_IMAGE_PATTERNS = (
    "protwitter", "twitter", "facebook", "instagram", "linkedin", "youtube",
    "wikipedia-logo", "wiki-logo", "commons-logo",
    "no_image", "no-image", "noimage", "placeholder",
    "question_mark", "questionmark",
    "flag_of_", "coat_of_arms",
    "p_book", "p_vip", "p_christianity",
)


def _is_blocked_image(url: str) -> bool:
    low = url.lower()
    return any(pat in low for pat in BLOCKED_IMAGE_PATTERNS)


def wikipedia_thumbnail(name: str, lang: str = "en") -> str | None:
    """REST summary API. Retorna URL da imagem (preferindo originalimage)."""
    enc = urllib.parse.quote(name.replace(" ", "_"))
    api = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{enc}"
    j = http_get_json(api)
    if not j:
        return None
    for key in ("originalimage", "thumbnail"):
        img = j.get(key) or {}
        src = img.get("source")
        if src and src.startswith("http") and not _is_blocked_image(src):
            return src
    return None


def wikipedia_search_thumbnail(name: str, lang: str = "en", context: str = "") -> str | None:
    """Full-text search -> primeiro hit relevante -> summary thumbnail.
    Util quando o titulo da pagina nao bate exatamente com o nome buscado.
    Se `context` (instituicao/cidade) eh dado, vira parte da query — reduz
    bastante o risco de homônimo.
    """
    query = f'"{name}" {context}'.strip() if context else name
    params = urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 3,
        "format": "json",
    })
    url = f"https://{lang}.wikipedia.org/w/api.php?{params}"
    j = http_get_json(url)
    if not j:
        return None
    hits = ((j.get("query") or {}).get("search") or [])
    if not hits:
        return None
    # Tenta cada hit em ordem. Aceita o primeiro que tenha thumbnail valido
    # E cujo titulo contenha pelo menos um sobrenome do alvo (filtro contra
    # paginas tipo "Lista de arqueologos" ou totalmente off-topic).
    name_tokens = {ascii_fold(t).lower() for t in name.split() if len(t) > 2}
    for hit in hits[:3]:
        title = hit.get("title")
        if not title:
            continue
        title_tokens = {ascii_fold(t).lower() for t in title.split()}
        if name_tokens and not (name_tokens & title_tokens):
            # Nenhum token do nome bate com o titulo -> provavelmente outro tema
            continue
        img = wikipedia_thumbnail(title, lang=lang)
        if img:
            return img
    return None


# ----- Wikidata -----
def wikidata_search_entity(name: str, lang: str = "en") -> str | None:
    """wbsearchentities por nome. Retorna Q-id do primeiro hit, ou None."""
    params = urllib.parse.urlencode({
        "action": "wbsearchentities",
        "search": name,
        "language": lang,
        "format": "json",
        "type": "item",
        "limit": 5,
    })
    url = f"https://www.wikidata.org/w/api.php?{params}"
    j = http_get_json(url)
    if not j:
        return None
    hits = j.get("search") or []
    if not hits:
        return None
    # Filtra hits que parecem ser pessoas (descricao tipica: "researcher",
    # "archaeologist", "professor", "historian", "academic"...).
    person_terms = ("researcher", "archaeologist", "professor", "historian",
                    "academic", "scholar", "scientist", "author")
    for hit in hits:
        desc = (hit.get("description") or "").lower()
        if any(t in desc for t in person_terms):
            return hit.get("id")
    # Sem match preciso: pega o primeiro.
    return hits[0].get("id")


def wikidata_image(qid: str) -> str | None:
    """Pega P18 (imagem) de um Q-id. Retorna URL Commons resolvida ou None."""
    params = urllib.parse.urlencode({
        "action": "wbgetclaims",
        "entity": qid,
        "property": "P18",
        "format": "json",
    })
    url = f"https://www.wikidata.org/w/api.php?{params}"
    j = http_get_json(url)
    if not j:
        return None
    claims = (j.get("claims") or {}).get("P18") or []
    if not claims:
        return None
    try:
        filename = claims[0]["mainsnak"]["datavalue"]["value"]
    except (KeyError, TypeError, IndexError):
        return None
    if _is_blocked_image(filename):
        return None
    enc = urllib.parse.quote(filename.replace(" ", "_"))
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{enc}"


def wikidata_thumbnail(name: str) -> str | None:
    """Pipeline completo Wikidata: search -> P18 -> URL."""
    for lang in ("en", "pt"):
        qid = wikidata_search_entity(name, lang=lang)
        if not qid:
            continue
        img = wikidata_image(qid)
        if img:
            return img
    return None


# ----- Bing image search (com contexto de instituicao) -----
def bing_image_search(query: str) -> str | None:
    """Bing image search HTML scrape. Retorna URL da 1a imagem media-grande
    cujo dominio nao seja redes sociais ou agregadores ruins.

    NB: Bing pode anti-botar. Sem garantia de funcionamento. Use com cautela.
    """
    qs = urllib.parse.urlencode({
        "q": query,
        "qft": "+filterui:imagesize-medium+filterui:photo-photo",
        "form": "HDRSC2",
    })
    url = f"https://www.bing.com/images/search?{qs}"
    data = http_get(url, timeout=20)
    if not data:
        return None
    text = data.decode("utf-8", errors="replace")
    # Cada thumb na pagina tem um JSON `m={"murl":"<url-original>"...}`
    # codificado dentro de um atributo. Procura pelo padrao `murl&quot;:&quot;<url>&quot;`.
    candidates = re.findall(r'murl&quot;:&quot;([^&]+?)&quot;', text)
    bad_domains = (
        "twitter.com", "x.com", "facebook.com", "fbcdn.net",
        "instagram.com", "tiktok.com", "pinterest.com", "pinimg.com",
        "youtube.com", "ytimg.com",
        "lookaside.fbsbx", "scontent",
    )
    for raw in candidates:
        candidate = html.unescape(raw)
        low = candidate.lower()
        if not low.startswith("http"):
            continue
        if any(d in low for d in bad_domains):
            continue
        if _is_blocked_image(candidate):
            continue
        if not re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", low):
            # Aceita se URL nao mostrar extensao (vai cair no content-type)
            pass
        return candidate
    return None


def bing_with_institution(name: str, institution: str, city: str = "") -> str | None:
    """Tenta varias queries derivadas: nome+instituicao, nome+cidade, etc."""
    queries = []
    if institution:
        queries.append(f'"{name}" {institution}')
    if institution and city:
        queries.append(f'"{name}" {institution} {city}')
    if institution:
        queries.append(f"{name} {institution}")
    for q in queries:
        img = bing_image_search(q)
        if img:
            return img
        time.sleep(0.5)
    return None


# ----- Download -----
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
        # Sanity check: se for HTML, descarta (pagina de erro disfarcada).
        if b"<html" in data[:200].lower() or b"<!doctype" in data[:200].lower():
            print("   ! Resposta parece HTML, ignorando", file=sys.stderr)
            return None
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
def process(name: str, group: str, institution: str, city: str,
            country: str, override: str | None) -> tuple[str, str, str]:
    """Processa um pesquisador. Retorna (status, slug, info)."""
    slug = slugify_local(name)
    ctx = f" @ {institution}" if institution else ""
    print(f"\n[{group}/{slug}] {name}{ctx}")

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

    # 2. Para cada variante do nome, tenta as 3 estrategias.
    variants = name_variants(name)
    # Wikidata primeiro: P18 e estruturado ("imagem do sujeito"), Wikipedia
    # summary as vezes pega imagem aleatoria da pagina. Wikipedia search
    # augmentada com instituicao cobre homonimos.
    # NB: Bing image search foi removido — retornava lixo (Dom Pedro pro Funari,
    # Volvo pra Rizzutto). DDG block bots. Lattes exige reCAPTCHA. Pra esses
    # pesquisadores, o que falhar aqui vai precisar de override manual.
    strategies: list[tuple[str, callable]] = [  # type: ignore[valid-type]
        ("wikidata",            lambda v: wikidata_thumbnail(v)),
        ("wikipedia_en",        lambda v: wikipedia_thumbnail(v, lang="en")),
        ("wikipedia_pt",        lambda v: wikipedia_thumbnail(v, lang="pt")),
        ("wiki_search_inst_en", lambda v: wikipedia_search_thumbnail(v, lang="en", context=institution)),
        ("wiki_search_inst_pt", lambda v: wikipedia_search_thumbnail(v, lang="pt", context=institution)),
    ]
    for variant in variants:
        if variant != name:
            print(f"   . variante: {variant}")
        for label, fn in strategies:
            print(f"   . tentando {label}({variant})")
            try:
                img = fn(variant)
            except Exception as exc:
                print(f"   ! {label} exception: {exc}", file=sys.stderr)
                img = None
            # Pausa entre chamadas pra nao bater no rate limit do Wikimedia
            time.sleep(0.5)
            if not img:
                continue
            print(f"   -> {label}: {img[:90]}")
            out = download(img, target_no_ext)
            if out:
                return (f"OK_{label.upper()}", slug, out.name)

    # 3. Falhou
    print("   X NAO ENCONTRADO")
    return ("FAIL", slug, "sem foto encontrada")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-group", choices=("internacional", "nacional"),
                    help="Limita aos pesquisadores deste grupo.")
    ap.add_argument("--only-slug", help="Re-baixa apenas um slug (forca overwrite).")
    args = ap.parse_args()

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, str, str, str]] = []  # (status, group, slug, info)

    selected = MEMBERS
    if args.only_group:
        selected = [m for m in MEMBERS if m[1] == args.only_group]
        print(f"Filtro: apenas grupo '{args.only_group}' ({len(selected)} pesquisadores)")
    if args.only_slug:
        selected = [m for m in selected if slugify_local(m[0]) == args.only_slug]
        # Quando re-baixando especifico, remove arquivo existente pra forcar
        for ext in ("jpg", "jpeg", "png", "webp"):
            p = MEDIA_DIR / f"{args.only_slug}.{ext}"
            if p.exists():
                p.unlink()
                print(f"Removido para re-download: {p.name}")

    for name, group, institution, city, country, override in selected:
        status, slug, info = process(name, group, institution, city, country, override)
        results.append((status, group, slug, info))
        time.sleep(0.3)  # cortesia com as APIs

    # Relatorio
    by_status: dict[str, list[str]] = {}
    for status, group, slug, info in results:
        by_status.setdefault(status, []).append(f"  - {group}/{slug}  ({info})")

    order = ("OK_WIKIDATA", "OK_WIKIPEDIA_EN", "OK_WIKIPEDIA_PT",
             "OK_WIKI_SEARCH_INST_EN", "OK_WIKI_SEARCH_INST_PT",
             "OK_OVERRIDE", "EXISTS", "FAIL")
    lines = ["COALITVS Photo Download Report", "=" * 50, ""]
    for status in order:
        items = by_status.get(status, [])
        lines.append(f"[{status}] {len(items)}")
        lines.extend(items)
        lines.append("")
    # Catch qualquer status nao listado em `order`
    extras = sorted(set(by_status) - set(order))
    for status in extras:
        items = by_status[status]
        lines.append(f"[{status}] {len(items)}")
        lines.extend(items)
        lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    fail_count = len(by_status.get("FAIL", []))
    ok_count = sum(
        len(items) for st, items in by_status.items()
        if st.startswith("OK_")
    )
    exist_count = len(by_status.get("EXISTS", []))
    total = len(results)
    print("\n" + "=" * 50)
    print(f"Total: {total}  |  Baixados: {ok_count}  |  "
          f"Ja existia: {exist_count}  |  Falhou: {fail_count}")
    print(f"Relatorio: {REPORT}")
    print(f"Fotos:     {MEDIA_DIR}")
    if fail_count:
        print(f"\n!  {fail_count} pesquisadores sem foto. Veja o relatorio e:")
        print("   - Adicione URL no campo `override` do MEMBERS no topo deste script, OU")
        print("   - Faca upload manual pelo admin: /admin/core/coalitvsmember/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
