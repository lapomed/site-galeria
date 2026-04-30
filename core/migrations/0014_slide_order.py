from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_artifact_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="slide",
            name="order",
            field=models.IntegerField(default=0, verbose_name="Ordem"),
        ),
        migrations.AlterModelOptions(
            name="slide",
            options={
                "ordering": ["order", "id"],
                "verbose_name": "🏠 Home - Slide do Carousel",
                "verbose_name_plural": "🏠 Home - Slides do Carousel",
            },
        ),
    ]
