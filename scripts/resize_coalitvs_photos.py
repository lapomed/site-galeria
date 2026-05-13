#!/usr/bin/env python3
"""Redimensiona fotos em media/coalitvs/ pra max 800px de largura, qualidade 85.

Idempotente: se ja esta abaixo do limite e em formato razoavel, pula.
Converte PNG sem transparencia em JPG (economia tipica: 5-10x).

Como rodar:
  uv run python scripts/resize_coalitvs_photos.py [--max-width 800] [--quality 85]
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow nao instalado. Use: uv add pillow ou pip install pillow")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = ROOT / "media" / "coalitvs"


def png_has_alpha(img: Image.Image) -> bool:
    """Detecta se PNG tem transparencia real (alfa < 255 em algum pixel)."""
    if img.mode not in ("RGBA", "LA", "PA"):
        return False
    alpha = img.getchannel("A")
    return alpha.getextrema()[0] < 255


def process_file(path: Path, max_width: int, quality: int) -> tuple[str, int, int]:
    """Retorna (status, bytes_antes, bytes_depois)."""
    before = path.stat().st_size
    try:
        img = Image.open(path)
        img.load()
    except Exception as exc:
        return (f"ERROR: {exc}", before, before)

    w, h = img.size
    target_path = path
    needs_save = False

    # PNG sem alpha -> JPG (economia gigantesca)
    if path.suffix.lower() == ".png" and not png_has_alpha(img):
        target_path = path.with_suffix(".jpg")
        if img.mode != "RGB":
            img = img.convert("RGB")
        needs_save = True

    # Resize se acima do limite
    if w > max_width:
        ratio = max_width / w
        new_size = (max_width, int(h * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        needs_save = True
    elif target_path.suffix.lower() in (".jpg", ".jpeg"):
        # JPG abaixo do limite: ja esta OK, so re-salvar se mudou de formato
        pass

    if not needs_save and target_path == path:
        return ("SKIP", before, before)

    save_kwargs: dict = {}
    if target_path.suffix.lower() in (".jpg", ".jpeg"):
        save_kwargs = {"quality": quality, "optimize": True, "progressive": True}
        if img.mode != "RGB":
            img = img.convert("RGB")
    elif target_path.suffix.lower() == ".png":
        save_kwargs = {"optimize": True}

    img.save(target_path, **save_kwargs)

    # Se mudou extensao, apaga o original
    if target_path != path:
        path.unlink()

    after = target_path.stat().st_size
    return ("OK", before, after)


def fmt_size(n: int) -> str:
    if n > 1024 * 1024:
        return f"{n / 1024 / 1024:.1f}MB"
    return f"{n / 1024:.0f}KB"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-width", type=int, default=800)
    parser.add_argument("--quality", type=int, default=85)
    args = parser.parse_args()

    if not MEDIA_DIR.is_dir():
        print(f"!! Diretorio nao existe: {MEDIA_DIR}")
        return 1

    files = sorted([p for p in MEDIA_DIR.iterdir() if p.is_file()
                    and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")])
    print(f"Processando {len(files)} arquivos em {MEDIA_DIR}")
    print(f"Max width: {args.max_width}px | Quality: {args.quality}")
    print("-" * 60)

    total_before = 0
    total_after = 0
    skip = 0
    ok = 0
    err = 0
    for p in files:
        status, before, after = process_file(p, args.max_width, args.quality)
        total_before += before
        total_after += after
        diff = before - after
        if status == "OK":
            ok += 1
            pct = (1 - after / before) * 100 if before else 0
            print(f"  OK   {p.name:<50} {fmt_size(before):>8} -> {fmt_size(after):>8}  -{pct:.0f}%")
        elif status == "SKIP":
            skip += 1
            print(f"  skip {p.name:<50} {fmt_size(before):>8}")
        else:
            err += 1
            print(f"  ERR  {p.name:<50} {status}")

    print("-" * 60)
    pct = (1 - total_after / total_before) * 100 if total_before else 0
    print(f"Total: {fmt_size(total_before)} -> {fmt_size(total_after)}  (-{pct:.0f}%)")
    print(f"Resized: {ok} | Skip: {skip} | Errors: {err}")
    return 0 if err == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
