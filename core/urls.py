from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('quem-somos/', views.about, name='about'),
    path('projetos/', views.project_list, name='project_list'),
    path('projetos/<slug:slug>/', views.project_detail, name='project_detail'),
    path('publicacoes/', views.publications, name='publications'),
    path('publicacoes/<slug:slug>/', views.publication_detail, name='publication_detail'),
    path('hub-aprendizado/', views.learning_hub, name='learning_hub'),
    path('colecoes/<str:category>/', views.digital_collections, name='digital_collections'),
    path('visitas-3d/', views.virtual_tours, name='virtual_tours'),
    path('visitas-3d/<slug:slug>/', views.virtual_tour_detail, name='virtual_tour_detail'),
    path('rich-text/upload/', views.tinymce_image_upload, name='tinymce_image_upload'),
]
