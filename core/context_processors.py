"""Context processors expostos a todos os templates.

`nav_context` injeta:
- social_links: dict {network: url} com SocialLink ativos (vazio se modelo nao
  existe ainda — durante o primeiro deploy antes da migration rodar).
- has_publications, has_hub_resources, has_virtual_tours: bool para o menu
  decidir se o item leva pra pagina ou cai em '#'.
- digital_collections_categories: as 3 categorias da Coleção (artefatos,
  escavacoes, edificacoes) com flag has_items.
"""
from .models import Collection


SOCIAL_NETWORKS = ('instagram', 'facebook', 'tiktok', 'youtube')


def nav_context(request):
    # Importa lazy para evitar ciclo na inicializacao da app
    try:
        from .models import SocialLink, Publication, LearningResource, VirtualTour
    except Exception:
        return {}

    try:
        social_qs = SocialLink.objects.filter(active=True)
        social_links = {sl.network: sl.url or '#' for sl in social_qs}
    except Exception:
        # Migration pode nao ter rodado ainda
        social_links = {}

    # Garante que os 4 ativos no menu sempre apareçam (com '#' se faltar)
    social_links_resolved = {n: social_links.get(n, '#') for n in SOCIAL_NETWORKS}

    try:
        has_publications = Publication.objects.filter(active=True).exists()
    except Exception:
        has_publications = False
    try:
        has_hub_resources = LearningResource.objects.filter(active=True).exists()
    except Exception:
        has_hub_resources = False
    try:
        has_virtual_tours = VirtualTour.objects.filter(active=True).exists()
    except Exception:
        has_virtual_tours = False

    try:
        existing_categories = set(
            Collection.objects.values_list('category', flat=True).distinct()
        )
    except Exception:
        existing_categories = set()

    digital_categories = []
    for key, label in Collection.CATEGORY_CHOICES:
        digital_categories.append({
            'key': key,
            'label': label,
            'has_items': key in existing_categories,
        })

    return {
        'social_links': social_links_resolved,
        'has_publications': has_publications,
        'has_hub_resources': has_hub_resources,
        'has_virtual_tours': has_virtual_tours,
        'digital_categories': digital_categories,
    }
