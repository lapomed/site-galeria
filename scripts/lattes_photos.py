#!/usr/bin/env python3
"""Baixa fotos de pesquisadores via Lattes (CNPq) usando Playwright.

Workflow:
  1. Abre Chromium em modo "headed" (visivel)
  2. Voce resolve o reCAPTCHA UMA VEZ manualmente quando aparecer
  3. Script itera pelos pesquisadores que ainda nao tem foto, busca por nome
     no Lattes, clica no 1o resultado, baixa a foto do CV.

Reaproveita MEMBERS de download_coalitvs_photos.py (mesma fonte da verdade).

Como rodar (de dentro do diretorio do projeto):
  uv run python scripts/lattes_photos.py [--only-group nacional] [--limit N]

Sai com codigo 0 mesmo se algumas fotos falharem. Imprime resumo no final.

NB: o captcha pode reaparecer apos varias buscas. Se isso ocorrer, o script
exibe uma mensagem clara e aguarda voce resolver novamente.
"""
from __future__ import annotations
import argparse
import importlib.util
import re
import sys
import time
import unicodedata
from pathlib import Path

try:
    from playwright.sync_api import (
        sync_playwright, TimeoutError as PWTimeout, Page, BrowserContext
    )
except ImportError:
    print("ERROR: Playwright nao instalado. Rode: uv add --dev playwright && uv run playwright install chromium")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = ROOT / "media" / "coalitvs"
LATTES_BASE = "http://buscatextual.cnpq.br/buscatextual/busca.do?metodo=apresentar"

# ============================================================
# Carrega MEMBERS de download_coalitvs_photos.py (DRY)
# ============================================================
def load_members() -> list[tuple]:
    spec = importlib.util.spec_from_file_location(
        "dl", Path(__file__).parent / "download_coalitvs_photos.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MEMBERS  # (name, group, institution, city, country, override)


def slugify_local(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[-\s]+", "-", s)
    return s


def already_has_photo(slug: str) -> bool:
    for ext in ("jpg", "jpeg", "png", "webp"):
        if (MEDIA_DIR / f"{slug}.{ext}").exists():
            return True
    return False


# ============================================================
# Lattes interactions
# ============================================================
def wait_for_results_in_browser(page: Page, message: str, timeout_s: int = 600) -> None:
    """Espera o usuario interagir no browser (resolver captcha + ver
    resultados de uma busca). Detecta via DOM, sem precisar de stdin.
    Faz polling ate aparecer a lista de resultados OU timeout."""
    print()
    print("=" * 60)
    print(f">>> {message}")
    print(">>> Detectando automaticamente quando voce concluir (via DOM).")
    print("=" * 60)
    deadline = time.time() + timeout_s
    selectors_ok = (
        "ol.resultado-da-busca li",
        ".resultado-da-busca li",
        "a[href*='visualizacv']",
    )
    while time.time() < deadline:
        for sel in selectors_ok:
            try:
                if page.locator(sel).count() > 0:
                    print(">>> Resultados detectados, prosseguindo.")
                    return
            except Exception:
                pass
        time.sleep(2)
    print(f"!! Timeout de {timeout_s}s aguardando resultados. Prosseguindo mesmo assim.")


def search_lattes(page: Page, name: str) -> bool:
    """Faz uma busca por nome. Retorna True se conseguiu listar resultados.
    Lida com captcha se necessario (espera intervenção humana)."""
    page.goto(LATTES_BASE, wait_until="domcontentloaded")
    page.fill("#textoBusca", name)

    # Garante que checkbox "buscar nome do pesquisador" esta marcado (padrao)
    # e clica em buscar
    try:
        page.click("#botaoBuscaFiltros", timeout=5000)
    except PWTimeout:
        page.press("#textoBusca", "Enter")

    # Aguarda resultados ou captcha
    page.wait_for_load_state("networkidle", timeout=20000)

    # Detecta presenca de captcha (iframe do reCAPTCHA visivel)
    if page.locator("iframe[src*='recaptcha']").count() > 0:
        page_text = page.content().lower()
        if "captcha" in page_text and "respond" not in page_text:
            wait_for_results_in_browser(
                page,
                f"CAPTCHA detectado durante busca por '{name}'. "
                "Resolva no browser e clique em Buscar de novo.",
            )

    # Verifica se ha resultados
    has_results = page.locator("ol.resultado-da-busca li, .resultado li, .resultado-da-busca").count() > 0
    if not has_results:
        # Tenta seletor mais generico — Lattes tem markup antigo, pode variar
        page_text = page.content()
        if "Nenhum resultado" in page_text:
            return False
    return True


def open_first_cv(page: Page) -> Page | None:
    """Clica no 1o resultado da busca. Retorna a Page do CV (popup) ou None."""
    # Lattes abre CVs em popup (window.open). Capturamos com expect_popup.
    selectors = [
        "ol.resultado-da-busca li a",
        ".resultado-da-busca a",
        ".resultado li a",
        "a[href*='visualizacv']",
    ]
    target = None
    for sel in selectors:
        if page.locator(sel).count() > 0:
            target = page.locator(sel).first
            break
    if target is None:
        return None
    try:
        with page.context.expect_page(timeout=15000) as new_page_info:
            target.click()
        return new_page_info.value
    except PWTimeout:
        # Talvez nao abriu em popup; tenta seguir na mesma aba
        return page


def grab_photo_url(cv_page: Page) -> str | None:
    """Extrai URL da foto do CV. Lattes coloca foto em <img class="foto">
    ou similar."""
    cv_page.wait_for_load_state("domcontentloaded", timeout=15000)
    candidates = [
        "img.foto",
        "img[src*='foto']",
        ".cabecalho img",
        ".curriculum img:first-of-type",
    ]
    for sel in candidates:
        loc = cv_page.locator(sel)
        if loc.count() > 0:
            src = loc.first.get_attribute("src")
            if src:
                if src.startswith("/"):
                    return f"http://buscatextual.cnpq.br{src}"
                return src
    return None


def download_via_context(context: BrowserContext, url: str, dest: Path) -> bool:
    """Baixa imagem reusando cookies da sessao (importante: foto.jsp valida
    referer/session)."""
    try:
        resp = context.request.get(
            url,
            headers={"Referer": "http://buscatextual.cnpq.br/buscatextual/"},
            timeout=20000,
        )
    except Exception as exc:
        print(f"     ! download exception: {exc}")
        return False
    if resp.status != 200:
        print(f"     ! HTTP {resp.status}")
        return False
    body = resp.body()
    if not body or len(body) < 1000:
        print(f"     ! resposta muito pequena: {len(body)} bytes")
        return False
    if body[:200].lower().startswith(b"<html"):
        print("     ! resposta eh HTML, nao imagem")
        return False
    # Detecta extensao por magic bytes
    if body[:3] == b"\xff\xd8\xff":
        ext = "jpg"
    elif body[:8] == b"\x89PNG\r\n\x1a\n":
        ext = "png"
    elif body[:4] in (b"GIF8",):
        ext = "gif"
    else:
        ext = "jpg"  # default
    out = dest.with_suffix(f".{ext}")
    out.write_bytes(body)
    return True


# ============================================================
# Main
# ============================================================
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-group", choices=("internacional", "nacional"),
                    help="Limita a um grupo")
    ap.add_argument("--limit", type=int, default=None,
                    help="Maximo de pesquisadores a processar")
    ap.add_argument("--headless", action="store_true",
                    help="Roda sem UI visivel (NAO recomendado — captcha exige humano)")
    args = ap.parse_args()

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    all_members = load_members()
    pending: list[tuple] = []
    for m in all_members:
        name, group, *_ = m
        slug = slugify_local(name)
        if already_has_photo(slug):
            continue
        if args.only_group and group != args.only_group:
            continue
        pending.append(m)
    if args.limit:
        pending = pending[:args.limit]

    print(f"Pesquisadores a processar: {len(pending)}")
    for m in pending:
        print(f"  - {m[1]}/{slugify_local(m[0])}  ({m[0]})")
    if not pending:
        print("Nada a fazer.")
        return 0

    results: dict[str, list[str]] = {"OK": [], "NO_RESULT": [], "NO_PHOTO": [], "DL_FAIL": [], "ERROR": []}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=args.headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1200, "height": 900},
        )
        page = context.new_page()

        # Primeiro acesso: usuario faz uma busca manual pra resolver o captcha.
        # O script detecta automaticamente quando aparecem resultados.
        page.goto(LATTES_BASE, wait_until="domcontentloaded")
        wait_for_results_in_browser(
            page,
            "Lattes aberto no browser. Digite QUALQUER nome (ex: seu proprio), "
            "clique em Buscar, resolva o captcha. Vou detectar automaticamente.",
        )

        for idx, (name, group, institution, city, country, override) in enumerate(pending, 1):
            slug = slugify_local(name)
            print(f"\n[{idx}/{len(pending)}] {group}/{slug} — {name}")
            try:
                if not search_lattes(page, name):
                    print("   X sem resultados")
                    results["NO_RESULT"].append(slug)
                    continue
                cv_page = open_first_cv(page)
                if cv_page is None:
                    print("   X nao abriu o CV")
                    results["NO_RESULT"].append(slug)
                    continue
                photo_url = grab_photo_url(cv_page)
                if not photo_url:
                    print("   X CV sem foto")
                    cv_page.close() if cv_page != page else None
                    results["NO_PHOTO"].append(slug)
                    continue
                print(f"   -> foto URL: {photo_url}")
                ok = download_via_context(context, photo_url, MEDIA_DIR / slug)
                if cv_page != page:
                    cv_page.close()
                if ok:
                    print("   OK")
                    results["OK"].append(slug)
                else:
                    results["DL_FAIL"].append(slug)
            except Exception as exc:
                print(f"   ! erro: {exc}")
                results["ERROR"].append(slug)
                # Fecha popups eventualmente abertos
                for p in list(context.pages):
                    if p != page:
                        try: p.close()
                        except Exception: pass
            time.sleep(1.0)  # respeito ao servidor

        print("\n" + "=" * 60)
        for status, lst in results.items():
            print(f"[{status}] {len(lst)}: {', '.join(lst) if lst else '-'}")
        print("=" * 60)
        # Em modo background nao temos stdin. Fecha apos 60s pra dar tempo
        # do usuario olhar / salvar coisas se quiser.
        print("\nFechando browser em 60s...")
        time.sleep(60)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
