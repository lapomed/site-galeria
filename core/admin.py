from django.contrib import admin
from .models import Slide, Project, Artifact, Collection, CollectionImage

class ArtifactInline(admin.TabularInline):
    model = Artifact
    extra = 1

class CollectionInline(admin.TabularInline):
    model = Collection.projects.through
    extra = 1
    verbose_name = "Adicionar a Coleção"
    verbose_name_plural = "Adicionar a Coleções"

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'created_at')
    search_fields = ('title', 'location')
    inlines = [ArtifactInline, CollectionInline]

@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'active', 'order')
    list_editable = ('active', 'order')

class CollectionImageInline(admin.TabularInline):
    model = CollectionImage
    extra = 3

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    inlines = [CollectionImageInline]
    exclude = ('projects',) # Projetos são adicionados via tela de Projeto
