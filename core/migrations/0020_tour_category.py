from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0019_project_order"),
    ]

    operations = [
        migrations.CreateModel(
            name="TourCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="Nome")),
                ("slug", models.SlugField(max_length=120, unique=True, verbose_name="Slug")),
                ("order", models.IntegerField(default=0, verbose_name="Ordem")),
            ],
            options={
                "verbose_name": "🥽 Visitas 3D - Categoria",
                "verbose_name_plural": "🥽 Visitas 3D - Categorias",
                "ordering": ["order", "name"],
            },
        ),
        migrations.AddField(
            model_name="virtualtour",
            name="categories",
            field=models.ManyToManyField(blank=True, related_name="tours", to="core.tourcategory", verbose_name="Categorias"),
        ),
    ]
