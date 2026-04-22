from django.shortcuts import render, get_object_or_404
from django.db.models import Q
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
