from django.contrib import admin
from .models import (
    Slide, Project, Artifact, Collection, CollectionImage,
    AboutSection, TeamMember, Timeline, ResearchArea, Partnership
)

# ===== CONFIGURAÇÃO DO SITE ADMIN =====
admin.site.site_header = "LAPOMED - Administração"
admin.site.site_title = "LAPOMED Admin"
admin.site.index_title = "Painel de Controle"


# ===== INLINES =====
class ArtifactInline(admin.TabularInline):
    model = Artifact
    extra = 1
    fields = ('title', 'description', 'image', 'model_file', 'sketchfab_embed', 'annotations')

class CollectionInline(admin.TabularInline):
    model = Collection.projects.through
    extra = 1
    verbose_name = "Adicionar a Coleção"
    verbose_name_plural = "Adicionar a Coleções"

class CollectionImageInline(admin.TabularInline):
    model = CollectionImage
    extra = 3


# ===== HOME / CAROUSEL =====
@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'active', 'order')
    list_editable = ('active', 'order')
    verbose_name = "Slide do Carousel (Home)"
    verbose_name_plural = "Slides do Carousel (Home)"


# ===== PROJETOS =====
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'created_at')
    search_fields = ('title', 'location')
    inlines = [ArtifactInline, CollectionInline]
    verbose_name = "Projeto Arqueológico"
    verbose_name_plural = "Projetos Arqueológicos"


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    inlines = [CollectionImageInline]
    exclude = ('projects',)
    verbose_name = "Coleção de Projetos"
    verbose_name_plural = "Coleções de Projetos"


# ===== QUEM SOMOS =====
class QuemSomosAdminMixin:
    """Mixin para adicionar agrupamento visual no admin"""
    class Media:
        css = {
            'all': ('admin/css/quem-somos-group.css',)
        }


@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    """📄 Seções 'Sobre o LAPOMED'"""
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
    
    class Meta:
        verbose_name = "📄 Seção Sobre (Quem Somos)"
        verbose_name_plural = "📄 Seções Sobre (Quem Somos)"


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """👥 Membros da Equipe"""
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
    
    class Meta:
        verbose_name = "👥 Membro da Equipe (Quem Somos)"
        verbose_name_plural = "👥 Equipe (Quem Somos)"


@admin.register(Timeline)
class TimelineAdmin(admin.ModelAdmin):
    """📅 Linha do Tempo"""
    list_display = ('year', 'title', 'active', 'created_at')
    list_editable = ('active',)
    list_filter = ('active', 'year')
    search_fields = ('title', 'description')
    ordering = ('-year',)
    
    class Meta:
        verbose_name = "📅 Marco Histórico (Quem Somos)"
        verbose_name_plural = "📅 Linha do Tempo (Quem Somos)"


@admin.register(ResearchArea)
class ResearchAreaAdmin(admin.ModelAdmin):
    """🔬 Áreas de Pesquisa"""
    list_display = ('title', 'icon', 'active', 'order')
    list_editable = ('active', 'order')
    list_filter = ('active',)
    search_fields = ('title', 'description')
    
    class Meta:
        verbose_name = "🔬 Área de Pesquisa (Quem Somos)"
        verbose_name_plural = "🔬 Áreas de Pesquisa (Quem Somos)"


@admin.register(Partnership)
class PartnershipAdmin(admin.ModelAdmin):
    """🤝 Parcerias"""
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
    
    class Meta:
        verbose_name = "🤝 Parceria (Quem Somos)"
        verbose_name_plural = "🤝 Parcerias (Quem Somos)"


# ===== CUSTOMIZAÇÃO DO ADMIN INDEX =====
# Agrupamento personalizado no index
admin.site.index_template = 'admin/custom_index.html'
