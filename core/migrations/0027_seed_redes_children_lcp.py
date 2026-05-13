"""Seed:
- Sub-itens do dropdown Redes (Instagram, Facebook, TikTok, Canal de Cortes)
- Move 'learning_hub' (Hub) para dentro de Redes como sub-item
- Cria NavItem do LCP na posição onde o Hub estava
- Cria LcpPage com active=False e texto placeholder

Idempotente: roda múltiplas vezes sem duplicar.
"""
from django.db import migrations


REDES_DEFAULTS = [
    # (label, social_network_key, fallback_url, order)
    ('Instagram', 'instagram', 'https://www.instagram.com/lapomedusp', 10),
    ('Facebook', 'facebook', '#', 20),
    ('TikTok', 'tiktok', '#', 30),
    ('Canal de Cortes', 'youtube', '#', 40),
]

LCP_PLACEHOLDER_CONTENT = (
    "<p>O <strong>Levantine Ceramics Project (LCP)</strong> é uma plataforma "
    "colaborativa internacional dedicada ao estudo da cerâmica do Levante "
    "antigo. Pesquisadores de diversas instituições contribuem com dados, "
    "imagens e análises de conjuntos cerâmicos provenientes de escavações "
    "arqueológicas na região.</p>"
    "<p>O LAPOMED mantém parceria oficial com o LCP, integrando à plataforma "
    "registros e estudos desenvolvidos por nossa equipe em projetos no "
    "Mediterrâneo Oriental. Essa colaboração amplia o alcance científico do "
    "laboratório e fortalece o diálogo entre a pesquisa arqueológica "
    "brasileira e a comunidade internacional.</p>"
    "<p>Acesse a plataforma do LCP para explorar a base completa de tipos "
    "cerâmicos, sítios e bibliografia especializada.</p>"
)


def seed(apps, schema_editor):
    NavItem = apps.get_model('core', 'NavItem')
    LcpPage = apps.get_model('core', 'LcpPage')
    SocialLink = apps.get_model('core', 'SocialLink')

    # 1. URLs de SocialLink (se preenchidas no admin), com fallback hardcoded
    sl_urls = {sl.network: sl.url for sl in SocialLink.objects.filter(active=True) if sl.url}

    # 2. Encontra o dropdown Redes (pode não existir se usuário apagou)
    redes = NavItem.objects.filter(kind='social', parent__isnull=True).first()

    if redes:
        # 3. Cria sub-itens default (Instagram, Facebook, TikTok, Cortes)
        for label, network, fallback, order in REDES_DEFAULTS:
            url = sl_urls.get(network) or fallback
            NavItem.objects.get_or_create(
                kind='sublink',
                parent=redes,
                label=label,
                defaults={
                    'custom_url': url,
                    'open_in_new_tab': True,
                    'order': order,
                    'active': True,
                },
            )

        # 4. Move o NavItem 'learning_hub' (top-level) para dentro de Redes
        hub = NavItem.objects.filter(kind='learning_hub', parent__isnull=True).first()
        if hub:
            hub.kind = 'sublink'
            hub.parent = redes
            hub.custom_url = '/hub-aprendizado/'
            hub.open_in_new_tab = False
            hub.order = 50  # depois dos 4 sociais
            hub.label = hub.label or 'Hub'
            hub.save()

    # 5. Cria NavItem do LCP (top-level) na posição onde o Hub estava (order=5)
    NavItem.objects.get_or_create(
        kind='lcp',
        parent=None,
        defaults={
            'label': 'LCP',
            'custom_url': '',
            'open_in_new_tab': False,
            'order': 5,
            'active': True,
        },
    )

    # 6. Cria LcpPage (singleton) com active=False + placeholder
    if not LcpPage.objects.exists():
        LcpPage.objects.create(
            hero_title="LCP — Levantine Ceramics Project",
            hero_subtitle="Parceria internacional",
            content=LCP_PLACEHOLDER_CONTENT,
            external_url="https://www.levantineceramics.org",
            button_label="Acessar a plataforma LCP",
            active=False,
        )


def unseed(apps, schema_editor):
    NavItem = apps.get_model('core', 'NavItem')
    LcpPage = apps.get_model('core', 'LcpPage')

    # Reverte: apaga sub-itens criados, restaura Hub para top-level
    NavItem.objects.filter(kind='sublink', label__in=[r[0] for r in REDES_DEFAULTS]).delete()

    hub = NavItem.objects.filter(kind='sublink', custom_url='/hub-aprendizado/').first()
    if hub:
        hub.kind = 'learning_hub'
        hub.parent = None
        hub.custom_url = ''
        hub.order = 5
        hub.save()

    NavItem.objects.filter(kind='lcp').delete()
    LcpPage.objects.all().delete()


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('core', '0026_navitem_parent_lcpkind_lcppage'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
