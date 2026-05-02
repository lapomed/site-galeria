from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_slide_subtitle_textfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="slug",
            field=models.SlugField(blank=True, max_length=300, unique=True, verbose_name="Slug (URL)"),
        ),
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
