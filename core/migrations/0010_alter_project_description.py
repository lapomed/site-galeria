from django.db import migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_remove_slide_order"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="description",
            field=tinymce.models.HTMLField(verbose_name="Descrição"),
        ),
    ]
