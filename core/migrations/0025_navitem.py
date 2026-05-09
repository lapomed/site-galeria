from django.db import migrations, models


SEED_ITEMS = [
    ('home', 'Home', 1),
    ('projects', 'Projetos', 2),
    ('about', 'Quem Somos', 3),
    ('publications', 'Publicações', 4),
    ('learning_hub', 'Hub', 5),
    ('collections', 'Coleções', 6),
    ('virtual_tours', 'Visitas 3D', 7),
    ('coalitvs', 'COALITVS', 8),
    ('social', 'Redes', 9),
    ('contact', 'Contato', 10),
]


def seed(apps, schema_editor):
    NavItem = apps.get_model('core', 'NavItem')
    if NavItem.objects.exists():
        return
    for kind, label, order in SEED_ITEMS:
        NavItem.objects.create(kind=kind, label=label, order=order, active=True)


def unseed(apps, schema_editor):
    NavItem = apps.get_model('core', 'NavItem')
    NavItem.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_coalitvs_seed'),
    ]

    operations = [
        migrations.CreateModel(
            name='NavItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=50, verbose_name='Rótulo exibido')),
                ('kind', models.CharField(
                    choices=[
                        ('home', 'Home'),
                        ('projects', 'Projetos'),
                        ('about', 'Quem Somos'),
                        ('publications', 'Publicações'),
                        ('learning_hub', 'Hub de Aprendizado'),
                        ('collections', 'Coleções Digitais (dropdown)'),
                        ('virtual_tours', 'Visitas Virtuais 3D'),
                        ('coalitvs', 'COALITVS'),
                        ('social', 'Notícias / Redes (dropdown)'),
                        ('contact', 'Contato'),
                        ('custom', 'Custom (URL livre)'),
                    ],
                    max_length=20, verbose_name='Tipo',
                )),
                ('custom_url', models.CharField(
                    blank=True, max_length=400,
                    help_text="Use apenas com tipo 'Custom'. Ex: /contato/ ou https://exemplo.com",
                    verbose_name='URL custom',
                )),
                ('open_in_new_tab', models.BooleanField(default=False, verbose_name='Abrir em nova aba')),
                ('active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('order', models.PositiveIntegerField(db_index=True, default=0, verbose_name='Ordem')),
            ],
            options={
                'verbose_name': '🧭 Navegação - Item de Menu',
                'verbose_name_plural': '🧭 Navegação - Menu do Header',
                'ordering': ['order'],
            },
        ),
        migrations.AlterModelOptions(
            name='coalitvsmember',
            options={
                'ordering': ['order', 'name'],
                'verbose_name': '🌐 Coalitvs - Pesquisador',
                'verbose_name_plural': '🌐 Coalitvs - Pesquisadores',
            },
        ),
        migrations.RunPython(seed, unseed),
    ]
