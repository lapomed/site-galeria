from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_publication_detail_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="virtualtour",
            name="location",
            field=models.CharField(blank=True, help_text="Ex: Beit She'an, Israel", max_length=200, verbose_name="Localização"),
        ),
        migrations.AddField(
            model_name="virtualtour",
            name="language",
            field=models.CharField(blank=True, default="Português", max_length=50, verbose_name="Idioma"),
        ),
    ]
