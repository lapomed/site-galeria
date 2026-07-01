from django.db import migrations


def create_team_navitem(apps, schema_editor):
    """Cria o item de menu 'Equipe' apontando para a nova página /equipe/.

    Idempotente: não duplica se já existir um item do tipo 'team'. Posiciona
    logo após 'Quem Somos' (mesma ordem; o desempate por id o coloca em
    seguida). Se não houver 'Quem Somos', vai para o fim do menu.
    """
    NavItem = apps.get_model('core', 'NavItem')
    if NavItem.objects.filter(kind='team').exists():
        return
    about = NavItem.objects.filter(kind='about', parent__isnull=True).first()
    if about is not None:
        order = about.order
    else:
        last = NavItem.objects.filter(parent__isnull=True).order_by('-order').first()
        order = (last.order + 1) if last else 0
    NavItem.objects.create(label='Equipe', kind='team', order=order, active=True)


def remove_team_navitem(apps, schema_editor):
    NavItem = apps.get_model('core', 'NavItem')
    NavItem.objects.filter(kind='team').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_alter_navitem_kind'),
    ]

    operations = [
        migrations.RunPython(create_team_navitem, remove_team_navitem),
    ]
