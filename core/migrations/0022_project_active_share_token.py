import uuid

from django.db import migrations, models


def populate_tokens(apps, schema_editor):
    Project = apps.get_model("core", "Project")
    for project in Project.objects.all():
        project.share_token = uuid.uuid4()
        project.save(update_fields=["share_token"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("core", "0021_virtualtour_render_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="active",
            field=models.BooleanField(
                db_index=True,
                default=True,
                help_text="Quando desativado, o projeto fica oculto da página pública. Continua acessível via link de compartilhamento.",
                verbose_name="Ativo",
            ),
        ),
        # share_token: adiciona como nullable, popula linha-a-linha, depois aplica unique
        migrations.AddField(
            model_name="project",
            name="share_token",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(populate_tokens, noop),
        migrations.AlterField(
            model_name="project",
            name="share_token",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Token de compartilhamento",
            ),
        ),
    ]
