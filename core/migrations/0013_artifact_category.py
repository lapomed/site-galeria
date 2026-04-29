from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_artifact_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="artifact",
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
    ]
