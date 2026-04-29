from django.contrib import admin
from django.utils.html import format_html
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
    list_display = ('id', 'title', 'thumbnail', 'active')
    list_editable = ('active',)
    ordering = ('id',)
    readonly_fields = ('thumbnail_preview',)

    @admin.display(description='Imagem')
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:48px;width:auto;border-radius:4px;object-fit:cover;" />',
                obj.image.url,
            )
        return '-'

    @admin.display(description='Preview')
    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:240px;width:auto;border-radius:6px;" />',
                obj.image.url,
            )
        return '-'


# ===== PROJETOS =====
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'created_at')
    search_fields = ('title', 'location')
    inlines = [ArtifactInline, CollectionInline]


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    inlines = [CollectionImageInline]
    exclude = ('projects',)


# ===== QUEM SOMOS =====

@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    """Seções 'Sobre o LAPOMED'"""
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
    """Membros da Equipe"""
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
    """Linha do Tempo"""
    list_display = ('year', 'title', 'active', 'created_at')
    list_editable = ('active',)
    list_filter = ('active', 'year')
    search_fields = ('title', 'description')
    ordering = ('-year',)


@admin.register(ResearchArea)
class ResearchAreaAdmin(admin.ModelAdmin):
    """Áreas de Pesquisa"""
    list_display = ('title', 'icon', 'active', 'order')
    list_editable = ('active', 'order')
    list_filter = ('active',)
    search_fields = ('title', 'description')


@admin.register(Partnership)
class PartnershipAdmin(admin.ModelAdmin):
    """Parcerias"""
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
