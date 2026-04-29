import os
import uuid

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.files.storage import default_storage
from .models import (
    Slide, Project, Collection,
    AboutSection, TeamMember, Timeline, ResearchArea, Partnership
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


ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
}


@csrf_exempt
@staff_member_required
@require_POST
def tinymce_image_upload(request):
    """Upload de imagem via TinyMCE (rich text). Acesso restrito a staff."""
    upload = request.FILES.get("file")
    if not upload:
        return JsonResponse({"error": {"message": "Nenhum arquivo enviado."}}, status=400)
    if upload.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        return JsonResponse(
            {"error": {"message": f"Tipo de arquivo nao suportado: {upload.content_type}"}},
            status=400,
        )
    ext = os.path.splitext(upload.name)[1].lower() or ".jpg"
    name = f"rich_text/{uuid.uuid4().hex}{ext}"
    saved = default_storage.save(name, upload)
    return JsonResponse({"location": default_storage.url(saved)})
