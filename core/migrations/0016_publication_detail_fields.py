from django.db import migrations, models
from django.utils.text import slugify
import tinymce.models


def populate_slugs(apps, schema_editor):
    Publication = apps.get_model("core", "Publication")
    used = set()
    for pub in Publication.objects.all():
        base = slugify(pub.title or "")[:280] or f"publicacao-{pub.pk}"
        slug = base
        i = 2
        while slug in used or Publication.objects.exclude(pk=pub.pk).filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        used.add(slug)
        pub.slug = slug
        pub.save(update_fields=["slug"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    # atomic=False permite que cada operacao seja commitada antes da proxima,
    # evitando que uma falha no UNIQUE INDEX desfaca a populacao do slug.
    atomic = False

    dependencies = [
        ("core", "0015_slide_subtitle_textfield"),
    ]

    operations = [
        # 1) Limpa qualquer constraint UNIQUE residual de tentativas anteriores
        migrations.RunSQL(
            sql=[
                "ALTER TABLE core_publication DROP CONSTRAINT IF EXISTS core_publication_slug_key;",
                "DROP INDEX IF EXISTS core_publication_slug_key;",
                "DROP INDEX IF EXISTS core_publication_slug_22a8e2db_like;",
            ],
            reverse_sql=migrations.RunSQL.noop,
            state_operations=[],
        ),
        # 2) Garante que a coluna slug exista (sem unique) — usa IF NOT EXISTS
        #    para sobreviver a estados parciais de migrations anteriores.
        migrations.RunSQL(
            sql=[
                "ALTER TABLE core_publication ADD COLUMN IF NOT EXISTS slug varchar(300) NOT NULL DEFAULT '';",
            ],
            reverse_sql="ALTER TABLE core_publication DROP COLUMN IF EXISTS slug;",
            state_operations=[
                migrations.AddField(
                    model_name="publication",
                    name="slug",
                    field=models.SlugField(blank=True, max_length=300, verbose_name="Slug (URL)"),
                ),
            ],
        ),
        # 3) Popula slugs vazios via slugify(title)
        migrations.RunPython(populate_slugs, noop),
        # 4) Demais campos novos (sem complicacoes)
        migrations.AddField(
            model_name="publication",
            name="authors_detailed",
            field=tinymce.models.HTMLField(
                blank=True,
                help_text="Liste autores com afiliação e ORCID, um por bloco. HTML permitido.",
                verbose_name="Autores (detalhado)",
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="doi",
            field=models.CharField(blank=True, help_text="Ex: 10.11606/9788566241266", max_length=200, verbose_name="DOI"),
        ),
        migrations.AddField(
            model_name="publication",
            name="keywords",
            field=models.CharField(blank=True, help_text="Separadas por vírgula", max_length=500, verbose_name="Palavras-chave"),
        ),
        migrations.AddField(
            model_name="publication",
            name="categories",
            field=models.CharField(
                blank=True,
                help_text="Separadas por vírgula. Ex: Ciências Humanas, Arqueologia",
                max_length=300,
                verbose_name="Categorias",
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="citation_abnt",
            field=models.TextField(blank=True, verbose_name="Citação ABNT"),
        ),
        migrations.AddField(
            model_name="publication",
            name="citation_apa",
            field=models.TextField(blank=True, verbose_name="Citação APA"),
        ),
        migrations.AlterField(
            model_name="publication",
            name="abstract",
            field=tinymce.models.HTMLField(blank=True, verbose_name="Resumo / Sinopse"),
        ),
        migrations.AlterField(
            model_name="publication",
            name="authors",
            field=models.CharField(blank=True, max_length=500, verbose_name="Autores (resumo)"),
        ),
        migrations.AlterField(
            model_name="publication",
            name="external_url",
            field=models.URLField(blank=True, verbose_name="Link Externo (repositório, etc)"),
        ),
    ]
