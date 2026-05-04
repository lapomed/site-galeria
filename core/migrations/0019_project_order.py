from django.db import migrations, models


def populate_order(apps, schema_editor):
    Project = apps.get_model("core", "Project")
    for index, project in enumerate(Project.objects.order_by('-created_at'), start=1):
        project.order = index
        project.save(update_fields=["order"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_virtualtour_slug_tagline_hero"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="order",
            field=models.PositiveIntegerField(db_index=True, default=0, verbose_name="Ordem"),
        ),
        migrations.RunPython(populate_order, noop),
        migrations.AlterModelOptions(
            name="project",
            options={
                "ordering": ["order", "-created_at"],
                "verbose_name": "🏛️ Projetos - Projeto",
                "verbose_name_plural": "🏛️ Projetos - Projetos",
            },
        ),
    ]
