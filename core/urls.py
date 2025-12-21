from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('projetos/', views.project_list, name='project_list'),
    path('projetos/<slug:slug>/', views.project_detail, name='project_detail'),
]
