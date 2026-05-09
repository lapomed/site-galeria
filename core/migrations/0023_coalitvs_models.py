from django.db import migrations, models
import django.db.models.deletion
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_project_active_share_token"),
    ]

    operations = [
        migrations.CreateModel(
            name="CoalitvsGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="Nome")),
                ("slug", models.SlugField(max_length=120, unique=True, verbose_name="Slug")),
                ("short_label", models.CharField(blank=True, help_text="Ex: INT, NAC, WG1", max_length=20, verbose_name="Label curto")),
                ("description", models.CharField(blank=True, max_length=300, verbose_name="Descrição")),
                ("color", models.CharField(default='#f0c300', help_text="HEX para o marker no mapa", max_length=20, verbose_name="Cor")),
                ("order", models.IntegerField(default=0, verbose_name="Ordem")),
            ],
            options={
                "verbose_name": "🌐 Coalitvs - Grupo",
                "verbose_name_plural": "🌐 Coalitvs - Grupos",
                "ordering": ["order", "name"],
            },
        ),
        migrations.CreateModel(
            name="CoalitvsMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="Nome")),
                ("slug", models.SlugField(blank=True, max_length=220, unique=True, verbose_name="Slug (URL)")),
                ("role", models.CharField(blank=True, help_text="Ex: Professor, Pesquisador Responsável", max_length=200, verbose_name="Cargo / Função")),
                ("institution", models.CharField(max_length=300, verbose_name="Instituição")),
                ("department", models.CharField(blank=True, max_length=200, verbose_name="Departamento / Unidade")),
                ("city", models.CharField(blank=True, max_length=120, verbose_name="Cidade")),
                ("country", models.CharField(max_length=120, verbose_name="País")),
                ("country_code", models.CharField(blank=True, help_text="USA, GBR, BRA…", max_length=3, verbose_name="Código ISO (3 letras)")),
                ("latitude", models.FloatField(blank=True, null=True, verbose_name="Latitude")),
                ("longitude", models.FloatField(blank=True, null=True, verbose_name="Longitude")),
                ("photo", models.ImageField(blank=True, null=True, upload_to="coalitvs/", verbose_name="Foto")),
                ("bio", tinymce.models.HTMLField(blank=True, verbose_name="Biografia")),
                ("expertise", models.CharField(blank=True, help_text="Separadas por vírgula", max_length=400, verbose_name="Áreas de Expertise")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="E-mail")),
                ("website", models.URLField(blank=True, verbose_name="Website")),
                ("lattes", models.URLField(blank=True, verbose_name="Currículo Lattes")),
                ("orcid", models.CharField(blank=True, help_text="Ex: 0000-0001-2345-6789", max_length=30, verbose_name="ORCID")),
                ("featured", models.BooleanField(default=False, help_text="Aparece em primeiro nos cards", verbose_name="Destaque")),
                ("active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("order", models.IntegerField(default=0, verbose_name="Ordem")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("groups", models.ManyToManyField(blank=True, related_name="members", to="core.coalitvsgroup", verbose_name="Grupos")),
                ("related_projects", models.ManyToManyField(blank=True, related_name="coalitvs_members", to="core.project", verbose_name="Projetos relacionados")),
            ],
            options={
                "verbose_name": "🌐 Coalitvs - Pesquisador",
                "verbose_name_plural": "🌐 Coalitvs - Pesquisadores",
                "ordering": ["-featured", "order", "name"],
            },
        ),
    ]
