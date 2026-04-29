from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_navbar_expansion"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArtifactImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="artifacts/gallery/")),
                ("caption", models.CharField(blank=True, max_length=300, verbose_name="Legenda")),
                ("order", models.IntegerField(default=0, verbose_name="Ordem")),
                (
                    "artifact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gallery",
                        to="core.artifact",
                    ),
                ),
            ],
            options={
                "verbose_name": "🏛️ Projetos - Imagem do Artefato",
                "verbose_name_plural": "🏛️ Projetos - Galeria do Artefato",
                "ordering": ["order", "id"],
            },
        ),
    ]
