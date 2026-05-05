import os
import uuid

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.shortcuts import redirect
from django.http import Http404
from django.db.models import Count
from .models import (
    Slide, Project, Collection,
    AboutSection, TeamMember, Timeline, ResearchArea, Partnership,
    Publication, LearningResource, VirtualTour, TourCategory,
)

def home(request):
    slides = Slide.objects.filter(active=True).order_by('order', 'id')
    return render(request, 'core/home.html', {'slides': slides})

def project_list(request):
    query = request.GET.get('q')
    projects = Project.objects.filter(active=True).order_by('order', '-created_at')
    collections = Collection.objects.all().order_by('-created_at')

    if query:
        projects = projects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )

    return render(request, 'core/project_list.html', {'projects': projects, 'collections': collections, 'query': query})


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug, active=True)
    return render(request, 'core/project_detail.html', {'project': project, 'is_preview': False})


def project_preview(request, token):
    """Acesso direto via token de compartilhamento — funciona mesmo com active=False."""
    project = get_object_or_404(Project, share_token=token)
    return render(request, 'core/project_detail.html', {'project': project, 'is_preview': True})

def about(request):
    """View para página Quem Somos"""
    context = {
        'about_sections': AboutSection.objects.filter(active=True).order_by('order'),
        'team_members': TeamMember.objects.filter(active=True).order_by('order'),
        'timeline': Timeline.objects.filter(active=True).order_by('-year'),
        'research_areas': ResearchArea.objects.filter(active=True).order_by('order'),
        'partnerships': Partnership.objects.filter(active=True).order_by('order'),
    }
    return render(request, 'core/about.html', context)


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"}


def publications(request):
    items = Publication.objects.filter(active=True).order_by('order', '-publication_date', '-created_at')
    return render(request, 'core/publications.html', {'items': items})


def publication_detail(request, slug):
    publication = get_object_or_404(Publication, slug=slug, active=True)
    return render(request, 'core/publication_detail.html', {'publication': publication})


def learning_hub(request):
    items = LearningResource.objects.filter(active=True).order_by('order', '-created_at')
    return render(request, 'core/learning_hub.html', {'items': items})


def digital_collections(request, category):
    valid = {key for key, _ in Collection.CATEGORY_CHOICES}
    if category not in valid:
        raise Http404
    collections = (
        Collection.objects
        .filter(category=category)
        .prefetch_related('images')
        .order_by('-created_at')
    )
    label = dict(Collection.CATEGORY_CHOICES)[category]
    return render(request, 'core/digital_collections.html', {
        'collections': collections,
        'category': category,
        'category_label': label,
    })


def virtual_tours(request):
    query = (request.GET.get('q') or '').strip()
    sort = (request.GET.get('sort') or 'newest').strip()
    category_slug = (request.GET.get('category') or '').strip()
    language_filter = (request.GET.get('language') or '').strip()

    base_qs = VirtualTour.objects.filter(active=True)
    items = base_qs

    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )
    if category_slug:
        items = items.filter(categories__slug=category_slug)
    if language_filter:
        items = items.filter(language=language_filter)

    if sort == 'oldest':
        items = items.order_by('order', 'created_at')
    else:
        items = items.order_by('order', '-created_at')

    items = items.distinct().prefetch_related('categories')

    # Opcoes para os dropdowns
    categories = (
        TourCategory.objects.filter(tours__active=True)
        .annotate(tour_count=Count('tours', filter=Q(tours__active=True)))
        .order_by('order', 'name')
    )
    languages = list(
        base_qs.exclude(language='').values_list('language', flat=True).distinct().order_by('language')
    )

    selected_category = None
    if category_slug:
        selected_category = next((c for c in categories if c.slug == category_slug), None)

    return render(request, 'core/virtual_tours.html', {
        'items': items,
        'query': query,
        'total': base_qs.count(),
        'sort': sort,
        'category_slug': category_slug,
        'selected_category': selected_category,
        'language_filter': language_filter,
        'categories': categories,
        'languages': languages,
        'has_filters': bool(query or category_slug or language_filter or sort != 'newest'),
    })


def virtual_tour_detail(request, slug):
    tour = get_object_or_404(VirtualTour, slug=slug, active=True)
    return render(request, 'core/virtual_tour_detail.html', {'tour': tour})


@csrf_exempt
@require_POST
def tinymce_image_upload(request):
    """Upload de imagem via TinyMCE (rich text). Acesso restrito a staff.

    Aceita imagens enviadas via toolbar OU coladas/arrastadas no meio do
    texto (paste/drag), onde o navegador costuma omitir o content-type
    ou enviar 'application/octet-stream'.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({"error": {"message": "Acesso negado."}}, status=403)
    upload = request.FILES.get("file") or request.FILES.get("image") or next(iter(request.FILES.values()), None)
    if not upload:
        return JsonResponse({"error": {"message": "Nenhum arquivo enviado."}}, status=400)
    ext = os.path.splitext(upload.name or "")[1].lower()
    content_type = (upload.content_type or "").lower()
    is_image = content_type.startswith("image/") or ext in ALLOWED_IMAGE_EXTENSIONS
    if not is_image:
        return JsonResponse(
            {"error": {"message": f"Tipo de arquivo nao suportado: {content_type or 'desconhecido'}"}},
            status=400,
        )
    if not ext:
        ext = "." + (content_type.split("/")[-1] if "/" in content_type else "png")
    name = f"rich_text/{uuid.uuid4().hex}{ext}"
    saved = default_storage.save(name, upload)
    return JsonResponse({"location": default_storage.url(saved)})
