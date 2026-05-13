"""Popula CoalitvsMember.photo para membros que tem foto em media/coalitvs/<slug>.<ext>.

Funciona em conjunto com `scripts/download_coalitvs_photos.py`:
  1. Voce roda o script localmente -> baixa fotos pra media/coalitvs/
  2. Faz commit de media/coalitvs/ (ou faz upload manual via storage)
  3. Em deploy, esta migration varre o diretorio e seta o campo `photo` de
     cada membro que tem arquivo correspondente.

Idempotente: rodar varias vezes nao quebra nada. Se o membro ja tem photo
setado, pula sem sobrescrever (preserva uploads manuais via admin).
"""
from django.db import migrations
from django.utils.text import slugify


EXTENSIONS = ("jpg", "jpeg", "png", "webp")


def populate_photos(apps, schema_editor):
    import os
    from django.conf import settings

    Member = apps.get_model("core", "CoalitvsMember")
    media_root = getattr(settings, "MEDIA_ROOT", None)
    if not media_root:
        print("  ! MEDIA_ROOT nao definido, pulando.")
        return

    coalitvs_dir = os.path.join(media_root, "coalitvs")
    if not os.path.isdir(coalitvs_dir):
        print(f"  ! Diretorio nao existe: {coalitvs_dir}, pulando.")
        return

    # Mapa: slug -> nome do arquivo (primeira extensao que encontrar)
    found: dict[str, str] = {}
    for fname in os.listdir(coalitvs_dir):
        base, ext = os.path.splitext(fname)
        if ext.lower().lstrip(".") in EXTENSIONS:
            found[base.lower()] = fname

    if not found:
        print(f"  = Nenhuma foto em {coalitvs_dir}.")
        return

    updated = 0
    skipped_has_photo = 0
    skipped_no_file = 0
    for member in Member.objects.all():
        if member.photo:
            skipped_has_photo += 1
            continue
        # Membro novo, sem foto. Procura por slug.
        slug = (member.slug or slugify(member.name)).lower()
        fname = found.get(slug)
        if not fname:
            skipped_no_file += 1
            continue
        member.photo = f"coalitvs/{fname}"
        member.save(update_fields=["photo"])
        updated += 1

    print(
        f"  + {updated} fotos correlacionadas | "
        f"{skipped_has_photo} ja tinham foto | "
        f"{skipped_no_file} sem arquivo correspondente"
    )


def noop_reverse(apps, schema_editor):
    """Nao desfaz - manter photo setado e seguro."""
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("core", "0027_seed_redes_children_lcp"),
    ]

    operations = [
        migrations.RunPython(populate_photos, noop_reverse),
    ]
