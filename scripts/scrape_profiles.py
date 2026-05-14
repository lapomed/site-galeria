#!/usr/bin/env python3
"""Scrape fotos de paginas de perfil institucional usando Playwright headless.

Diferente de lattes_photos.py: nao precisa de captcha, nao precisa de UI.
Para cada (slug, url) em PROFILES, renderiza a pagina, extrai foto.

Estrategia de extracao por pagina:
  1. og:image (mais confiavel)
  2. <img> com alt contendo o nome
  3. 1o <img> com class/src contendo "profile|portrait|staff|people|photo|avatar"

Como rodar:
  uv run python scripts/scrape_profiles.py
"""
from __future__ import annotations
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("ERROR: Playwright nao instalado.")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = ROOT / "media" / "coalitvs"

# (slug, profile_url, nome_para_match_em_alt)
PROFILES: list[tuple[str, str, str]] = [
    ("justin-leidwanger",              "https://classics.stanford.edu/people/justin-leidwanger", "Leidwanger"),
    ("andrea-berlin",                  "https://www.bu.edu/archaeology/profile/andrea-berlin/", "Berlin"),
    ("c-michael-barton",               "https://search.asu.edu/profile/1201194", "Barton"),
    ("jas-elsner",                     "https://www.corpus.ox.ac.uk/people/professor-jas-elsner/", "Elsner"),
    ("mark-altaweel",                  "https://www.ucl.ac.uk/archaeology/people/prof-mark-altaweel", "Altaweel"),
    ("carlos-augusto-ribeiro-machado", "https://www.st-andrews.ac.uk/classics/staff/carm/", "Machado"),
    ("gregg-e-gardner",                "https://cners.ubc.ca/profile/gregg-gardner/", "Gardner"),
    ("achim-lichtenberger",            "https://www.uni-muenster.de/ArchaeologyNearEast/en/personen/achim-lichtenberger.shtml", "Lichtenberger"),
    ("florian-janoscha-kreppner",      "https://www.uni-muenster.de/ArchaeologyNearEast/en/personen/florian-kreppner.shtml", "Kreppner"),
    ("naoise-mac-sweeney",             "https://ancientworldmagazine.com/contributors/naoise-mac-sweeney/", "Sweeney"),
    ("aris-ymir-politopoulos",         "https://www.universiteitleiden.nl/en/staffmembers/aris-ymir-politopoulos", "Politopoulos"),
    ("oren-tal",                       "https://en-archaeology.tau.ac.il/profile/orental", "Oren Tal"),
    ("alexander-fantalkin",            "https://en-archaeology.tau.ac.il/profile/alexanderfantalkin", "Fantalkin"),
    ("benjamin-isakhan",               "https://www.deakin.edu.au/about-deakin/people/benjamin-isakhan", "Isakhan"),
]

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def extract_photo_url(page, name_match: str) -> str | None:
    """Tenta achar URL da foto na pagina renderizada."""
    # 1) og:image
    og = page.evaluate(
        """() => {
            const m = document.querySelector('meta[property="og:image"]');
            return m ? m.getAttribute('content') : null;
        }"""
    )
    if og and re.search(r"\.(jpg|jpeg|png|webp)", og, re.I):
        return og

    # 2) <img> com alt contendo nome
    candidate = page.evaluate(
        f"""(needle) => {{
            const needles = needle.toLowerCase().split(/\\s+/);
            const imgs = Array.from(document.querySelectorAll('img'));
            for (const img of imgs) {{
                const alt = (img.alt || '').toLowerCase();
                if (needles.every(n => alt.includes(n))) {{
                    return img.src;
                }}
            }}
            return null;
        }}""",
        name_match,
    )
    if candidate and re.search(r"\.(jpg|jpeg|png|webp)", candidate, re.I):
        return candidate

    # 3) primeira img grande com src "profile|portrait|staff|people|photo|avatar|person"
    candidate = page.evaluate(
        """() => {
            const patterns = /profile|portrait|staff|people|photo|avatar|person|staff_member|biography/i;
            const imgs = Array.from(document.querySelectorAll('img'));
            for (const img of imgs) {
                const src = img.src || '';
                const w = img.naturalWidth || img.width || 0;
                if (patterns.test(src) && w > 80 && !/logo|icon|svg\?/i.test(src)) {
                    return img.src;
                }
            }
            return null;
        }"""
    )
    if candidate and re.search(r"\.(jpg|jpeg|png|webp)", candidate, re.I):
        return candidate

    return None


def download(url: str, dest_no_ext: Path) -> Path | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        if len(data) < 500:
            return None
        # Detect ext
        if data[:3] == b"\xff\xd8\xff":
            ext = "jpg"
        elif data[:8] == b"\x89PNG\r\n\x1a\n":
            ext = "png"
        elif data[:4] == b"RIFF":
            ext = "webp"
        else:
            m = re.search(r"\.(jpg|jpeg|png|webp)", url, re.I)
            ext = m.group(1).lower().replace("jpeg", "jpg") if m else "jpg"
        out = dest_no_ext.with_suffix(f".{ext}")
        out.write_bytes(data)
        return out
    except Exception as exc:
        print(f"     ! download error: {exc}")
        return None


def main() -> int:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, list[str]] = {"OK": [], "NO_PHOTO": [], "ERROR": []}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1200, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()

        for slug, url, name_match in PROFILES:
            # Pula se ja tem
            already = any((MEDIA_DIR / f"{slug}.{ext}").exists() for ext in ("jpg", "jpeg", "png", "webp"))
            if already:
                print(f"[skip] {slug} (ja existe)")
                continue
            print(f"\n[{slug}] {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Aguarda um pouco pra JS render
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except PWTimeout:
                    pass
                photo_url = extract_photo_url(page, name_match)
                if not photo_url:
                    print("   X foto nao encontrada")
                    results["NO_PHOTO"].append(slug)
                    continue
                print(f"   -> {photo_url[:100]}")
                out = download(photo_url, MEDIA_DIR / slug)
                if out:
                    print(f"   OK {out.name} ({out.stat().st_size} bytes)")
                    results["OK"].append(slug)
                else:
                    results["NO_PHOTO"].append(slug)
            except Exception as exc:
                print(f"   ! erro: {exc}")
                results["ERROR"].append(slug)
            time.sleep(0.5)

        print("\n" + "=" * 60)
        for st, lst in results.items():
            print(f"[{st}] {len(lst)}: {', '.join(lst) if lst else '-'}")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
