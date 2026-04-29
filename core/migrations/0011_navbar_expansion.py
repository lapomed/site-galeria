from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_alter_project_description"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="collection",
            options={
                "verbose_name": "🗂️ Coleções Digitais - Coleção",
                "verbose_name_plural": "🗂️ Coleções Digitais - Coleções",
            },
        ),
        migrations.AddField(
            model_name="collection",
            name="category",
            field=models.CharField(
                choices=[
                    ("artefatos", "Artefatos"),
                    ("escavacoes", "Escavações"),
                    ("edificacoes", "Edificações / Monumentos"),
                ],
                default="artefatos",
                max_length=20,
                verbose_name="Categoria",
            ),
        ),
        migrations.CreateModel(
            name="Publication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=300, verbose_name="Título")),
                ("authors", models.CharField(blank=True, max_length=500, verbose_name="Autores")),
                ("abstract", tinymce.models.HTMLField(blank=True, verbose_name="Resumo")),
                ("publication_date", models.DateField(blank=True, null=True, verbose_name="Data de Publicação")),
                ("external_url", models.URLField(blank=True, verbose_name="Link Externo (DOI, repositório, etc)")),
                ("pdf_file", models.FileField(blank=True, null=True, upload_to="publications/", verbose_name="Arquivo PDF")),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="publications/covers/", verbose_name="Imagem de Capa")),
                ("active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("order", models.IntegerField(default=0, verbose_name="Ordem")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "📚 Publicações - Publicação",
                "verbose_name_plural": "📚 Publicações - Publicações",
                "ordering": ["order", "-publication_date", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="LearningResource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=300, verbose_name="Título")),
                ("description", tinymce.models.HTMLField(blank=True, verbose_name="Descrição")),
                (
                    "resource_type",
                    models.CharField(
                        choices=[
                            ("article", "Artigo"),
                            ("video", "Vídeo"),
                            ("course", "Curso"),
                            ("podcast", "Podcast"),
                            ("book", "Livro"),
                            ("other", "Outro"),
                        ],
                        default="article",
                        max_length=20,
                        verbose_name="Tipo",
                    ),
                ),
                ("url", models.URLField(blank=True, verbose_name="Link")),
                ("thumbnail", models.ImageField(blank=True, null=True, upload_to="hub/", verbose_name="Thumbnail")),
                ("active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("order", models.IntegerField(default=0, verbose_name="Ordem")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "🎓 Hub - Recurso",
                "verbose_name_plural": "🎓 Hub - Recursos de Aprendizado",
                "ordering": ["order", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="VirtualTour",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=300, verbose_name="Título")),
                ("description", tinymce.models.HTMLField(blank=True, verbose_name="Descrição")),
                ("thumbnail", models.ImageField(blank=True, null=True, upload_to="virtual_tours/", verbose_name="Thumbnail")),
                (
                    "embed_url",
                    models.URLField(blank=True, help_text="Sketchfab, Matterport, Kuula etc.", verbose_name="URL Embed"),
                ),
                (
                    "embed_code",
                    models.TextField(blank=True, help_text="Cole o iframe completo, se preferir", verbose_name="Código Embed (iframe)"),
                ),
                ("model_file", models.FileField(blank=True, null=True, upload_to="virtual_tours/models/", verbose_name="Arquivo 3D")),
                ("active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("order", models.IntegerField(default=0, verbose_name="Ordem")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "🥽 Visitas 3D - Tour",
                "verbose_name_plural": "🥽 Visitas 3D - Tours",
                "ordering": ["order", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SocialLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "network",
                    models.CharField(
                        choices=[
                            ("instagram", "Instagram"),
                            ("facebook", "Facebook"),
                            ("tiktok", "TikTok"),
                            ("youtube", "YouTube / Cortes"),
                            ("twitter", "X / Twitter"),
                            ("linkedin", "LinkedIn"),
                        ],
                        max_length=20,
                        unique=True,
                        verbose_name="Rede",
                    ),
                ),
                ("url", models.URLField(blank=True, verbose_name="URL")),
                ("label", models.CharField(blank=True, max_length=100, verbose_name="Rótulo (opcional)")),
                ("active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("order", models.IntegerField(default=0, verbose_name="Ordem")),
            ],
            options={
                "verbose_name": "🔗 Redes - Link Social",
                "verbose_name_plural": "🔗 Redes - Links Sociais",
                "ordering": ["order"],
            },
        ),
    ]
