from django.contrib import admin
from .models import (
    Slide, Project, Artifact, Collection, CollectionImage,
    AboutSection, TeamMember, Timeline, ResearchArea, Partnership
)

class ArtifactInline(admin.TabularInline):
    model = Artifact
    extra = 1
    fields = ('title', 'description', 'image', 'model_file', 'sketchfab_embed', 'annotations')

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


# ===== ADMIN PARA PÁGINA "QUEM SOMOS" =====

@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    """Admin para seções 'Sobre o LAPOMED'"""
    list_display = ('title', 'active', 'order', 'updated_at')
    list_editable = ('active', 'order')
    list_filter = ('active',)
    search_fields = ('title', 'content')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'content', 'image')
        }),
        ('Missão e Visão', {
            'fields': ('mission', 'vision'),
            'classes': ('collapse',)
        }),
        ('Configurações', {
            'fields': ('active', 'order')
        }),
    )


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin para membros da equipe"""
    list_display = ('name', 'role', 'active', 'order')
    list_editable = ('active', 'order')
    list_filter = ('active', 'role')
    search_fields = ('name', 'role', 'bio')
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('name', 'role', 'photo', 'bio')
        }),
        ('Contato e Links', {
            'fields': ('email', 'lattes')
        }),
        ('Configurações', {
            'fields': ('active', 'order')
        }),
    )


@admin.register(Timeline)
class TimelineAdmin(admin.ModelAdmin):
    """Admin para linha do tempo"""
    list_display = ('year', 'title', 'active', 'created_at')
    list_editable = ('active',)
    list_filter = ('active', 'year')
    search_fields = ('title', 'description')
    ordering = ('-year',)


@admin.register(ResearchArea)
class ResearchAreaAdmin(admin.ModelAdmin):
    """Admin para áreas de pesquisa"""
    list_display = ('title', 'icon', 'active', 'order')
    list_editable = ('active', 'order')
    list_filter = ('active',)
    search_fields = ('title', 'description')


@admin.register(Partnership)
class PartnershipAdmin(admin.ModelAdmin):
    """Admin para parcerias"""
    list_display = ('name', 'website', 'active', 'order')
    list_editable = ('active', 'order')
    list_filter = ('active',)
    search_fields = ('name', 'description')
    fieldsets = (
        ('Informações da Parceria', {
            'fields': ('name', 'description', 'logo', 'website')
        }),
        ('Configurações', {
            'fields': ('active', 'order')
        }),
    )
