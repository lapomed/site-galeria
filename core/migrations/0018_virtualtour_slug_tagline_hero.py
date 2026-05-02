from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    VirtualTour = apps.get_model("core", "VirtualTour")
    used = set()
    for tour in VirtualTour.objects.all():
        base = slugify(tour.title or "")[:280] or f"tour-{tour.pk}"
        slug = base
        i = 2
        while slug in used or VirtualTour.objects.exclude(pk=tour.pk).filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        used.add(slug)
        tour.slug = slug
        tour.save(update_fields=["slug"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("core", "0017_virtualtour_location_language"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE core_virtualtour ADD COLUMN IF NOT EXISTS slug varchar(300) NOT NULL DEFAULT '';",
            ],
            reverse_sql="ALTER TABLE core_virtualtour DROP COLUMN IF EXISTS slug;",
            state_operations=[
                migrations.AddField(
                    model_name="virtualtour",
                    name="slug",
                    field=models.SlugField(blank=True, max_length=300, verbose_name="Slug (URL)"),
                ),
            ],
        ),
        migrations.RunPython(populate_slugs, noop),
        migrations.AddField(
            model_name="virtualtour",
            name="tagline",
            field=models.CharField(
                blank=True,
                help_text="Frase curta exibida abaixo do título no hero (uma linha)",
                max_length=300,
                verbose_name="Tagline",
            ),
        ),
        migrations.AddField(
            model_name="virtualtour",
            name="hero_image",
            field=models.ImageField(
                blank=True,
                help_text="Opcional. Usa a thumbnail como fallback.",
                null=True,
                upload_to="virtual_tours/heroes/",
                verbose_name="Imagem Hero (alta resolução)",
            ),
        ),
    ]
