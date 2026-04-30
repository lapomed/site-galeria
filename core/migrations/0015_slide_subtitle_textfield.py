from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_slide_order"),
    ]

    operations = [
        migrations.AlterField(
            model_name="slide",
            name="subtitle",
            field=models.TextField(blank=True, verbose_name="Subtítulo / Descrição"),
        ),
    ]
