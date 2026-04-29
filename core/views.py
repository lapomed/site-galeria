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
from .models import (
    Slide, Project, Artifact, Collection,
    AboutSection, TeamMember, Timeline, ResearchArea, Partnership,
    Publication, LearningResource, VirtualTour,
)

def home(request):
    slides = Slide.objects.filter(active=True).order_by('id')
    return render(request, 'core/home.html', {'slides': slides})

def project_list(request):
    query = request.GET.get('q')
    projects = Project.objects.all().order_by('-created_at')
    collections = Collection.objects.all().order_by('-created_at')
    
    if query:
        projects = projects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )
    
    return render(request, 'core/project_list.html', {'projects': projects, 'collections': collections, 'query': query})

def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    return render(request, 'core/project_detail.html', {'project': project})

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


def learning_hub(request):
    items = LearningResource.objects.filter(active=True).order_by('order', '-created_at')
    return render(request, 'core/learning_hub.html', {'items': items})


def digital_collections(request, category):
    valid = {key for key, _ in Collection.CATEGORY_CHOICES}
    if category not in valid:
        raise Http404
    collections = Collection.objects.filter(category=category).order_by('-created_at')
    artifacts = (
        Artifact.objects
        .filter(category=category)
        .select_related('project')
        .prefetch_related('gallery')
        .order_by('-created_at')
    )
    label = dict(Collection.CATEGORY_CHOICES)[category]
    return render(request, 'core/digital_collections.html', {
        'collections': collections,
        'artifacts': artifacts,
        'category': category,
        'category_label': label,
    })


def virtual_tours(request):
    items = VirtualTour.objects.filter(active=True).order_by('order', '-created_at')
    return render(request, 'core/virtual_tours.html', {'items': items})


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
