from django.shortcuts import render, get_object_or_404
from .models import Slide, Project

def home(request):
    slides = Slide.objects.filter(active=True).order_by('order')
    return render(request, 'core/home.html', {'slides': slides})

def project_list(request):
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'core/project_list.html', {'projects': projects})

def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    return render(request, 'core/project_detail.html', {'project': project})
