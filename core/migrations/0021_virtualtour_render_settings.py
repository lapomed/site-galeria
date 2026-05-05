from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0020_tour_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="virtualtour",
            name="model_exposure",
            field=models.FloatField(
                default=0.7,
                help_text="0.4 (escuro) – 1.0 (normal) – 1.5 (brilhante). Default 0.7.",
                verbose_name="Exposição",
            ),
        ),
        migrations.AddField(
            model_name="virtualtour",
            name="model_environment",
            field=models.CharField(
                blank=True,
                choices=[
                    ('legacy', 'Legacy (suave, recomendado)'),
                    ('neutral', 'Neutral (brilhante)'),
                    ('', 'Nenhum (sem IBL)'),
                ],
                default='legacy',
                help_text="Iluminação ambiente. Use 'Legacy' para photogrammetry; 'Nenhum' se o modelo já vem com luz baked.",
                max_length=20,
                verbose_name="Ambiente IBL",
            ),
        ),
        migrations.AddField(
            model_name="virtualtour",
            name="model_tone_mapping",
            field=models.CharField(
                choices=[
                    ('commerce', 'Commerce (bom contraste)'),
                    ('aces', 'ACES (cinematic)'),
                    ('agx', 'AgX (natural)'),
                    ('neutral', 'Neutral (sem ajuste)'),
                ],
                default='commerce',
                help_text="Compressão de highlights/sombras. 'Commerce' costuma ser o mais agradável.",
                max_length=20,
                verbose_name="Tone Mapping",
            ),
        ),
        migrations.AddField(
            model_name="virtualtour",
            name="model_shadow_intensity",
            field=models.FloatField(
                default=1.0,
                help_text="0 desliga, 1 normal, 2 sombra forte.",
                verbose_name="Intensidade da Sombra",
            ),
        ),
    ]
