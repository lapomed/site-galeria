from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_aboutsection_values"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="slide",
            options={
                "ordering": ["id"],
                "verbose_name": "🏠 Home - Slide do Carousel",
                "verbose_name_plural": "🏠 Home - Slides do Carousel",
            },
        ),
        migrations.RemoveField(
            model_name="slide",
            name="order",
        ),
    ]
