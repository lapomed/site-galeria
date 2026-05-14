#!/usr/bin/env python3
"""Baixa 1a thumbnail do Google Imagens para cada pesquisador pendente.

USO PROVISORIO/EXPLORATORIO: pode pegar pessoa errada (homonimo). Voce DEVE
revisar visualmente cada foto antes de commitar.

Como rodar:
  uv run python scripts/google_images.py [--only-group nacional|internacional]
"""
from __future__ import annotations
import argparse
import importlib.util
import re
import sys
import time
import unicodedata
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
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def slugify_local(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[-\s]+", "-", s)
    return s


def load_members():
    spec = importlib.util.spec_from_file_location(
        "dl", Path(__file__).parent / "download_coalitvs_photos.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MEMBERS


def already_has(slug: str) -> bool:
    return any((MEDIA_DIR / f"{slug}.{ext}").exists() for ext in ("jpg", "jpeg", "png", "webp"))


def fetch_first_image(page, query: str) -> str | None:
    """Navega pra Google Imagens com query e retorna URL da 1a thumbnail real."""
    url = f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(query)}&hl=en"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)  # deixar thumbnails carregarem
    except PWTimeout:
        return None
    # Aceita cookies banner se aparecer
    try:
        page.click("button:has-text('Accept all'), button:has-text('Aceitar tudo')", timeout=3000)
        time.sleep(1)
    except PWTimeout:
        pass
    # Pega imgs com src que parece thumbnail real
    imgs = page.evaluate(
        """() => Array.from(document.querySelectorAll('img'))
            .filter(i => (i.naturalWidth || 0) > 80 && (i.naturalHeight || 0) > 80)
            .filter(i => i.src && (i.src.startsWith('https://') || i.src.startsWith('http://')))
            .filter(i => !/google\\.com\\/images\\/branding/i.test(i.src))
            .map(i => i.src)
            .slice(0, 5)
        """
    )
    if not imgs:
        return None
    return imgs[0]


def download(url: str, dest: Path) -> Path | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=20).read()
        if len(data) < 1000:
            return None
        if data[:3] == b"\xff\xd8\xff":
            ext = "jpg"
        elif data[:8] == b"\x89PNG\r\n\x1a\n":
            ext = "png"
        elif data[:4] == b"RIFF":
            ext = "webp"
        else:
            ext = "jpg"
        out = dest.with_suffix(f".{ext}")
        out.write_bytes(data)
        return out
    except Exception as exc:
        print(f"     ! download error: {exc}")
        return None


def build_query(name: str, institution: str, group: str) -> str:
    """Constroi query agressiva pra Google. Inclui instituicao pra desambiguar."""
    return f"{name} {institution}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-group", choices=("internacional", "nacional"))
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    members = load_members()
    pending: list[tuple] = []
    for m in members:
        name, group, institution, city, country, _override = m
        slug = slugify_local(name)
        if already_has(slug):
            continue
        if args.only_group and group != args.only_group:
            continue
        pending.append(m)
    if args.limit:
        pending = pending[: args.limit]

    print(f"Pesquisadores a processar: {len(pending)}")
    if not pending:
        return 0

    results: dict[str, list[str]] = {"OK": [], "NO_IMG": [], "ERROR": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1200, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()

        for idx, (name, group, institution, city, country, _) in enumerate(pending, 1):
            slug = slugify_local(name)
            print(f"\n[{idx}/{len(pending)}] {group}/{slug} — {name}")
            try:
                img_url = fetch_first_image(page, build_query(name, institution, group))
                if not img_url:
                    print("   X nenhuma img encontrada")
                    results["NO_IMG"].append(slug)
                    continue
                print(f"   -> {img_url[:100]}")
                out = download(img_url, MEDIA_DIR / slug)
                if out:
                    print(f"   OK {out.name} ({out.stat().st_size} bytes)")
                    results["OK"].append(slug)
                else:
                    results["NO_IMG"].append(slug)
            except Exception as exc:
                print(f"   ! erro: {exc}")
                results["ERROR"].append(slug)
            time.sleep(1.0)

        print("\n" + "=" * 60)
        for st, lst in results.items():
            print(f"[{st}] {len(lst)}: {', '.join(lst) if lst else '-'}")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
