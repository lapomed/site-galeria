import uuid

from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html
from adminsortable2.admin import SortableAdminMixin, SortableTabularInline
from .models import (
    Slide, Project, Artifact, ArtifactImage, Collection, CollectionImage,
    AboutSection, TeamMember, Timeline, ResearchArea, Partnership,
    Publication, LearningResource, VirtualTour, TourCategory, SocialLink,
    CoalitvsGroup, CoalitvsMember, NavItem, LcpPage,
)

# ===== CONFIGURAÇÃO DO SITE ADMIN =====
admin.site.site_header = "LAPOMED - Administração"
admin.site.site_title = "LAPOMED Admin"
admin.site.index_title = "Painel de Controle"


# ===== INLINES =====
class ArtifactInline(admin.TabularInline):
    model = Artifact
    extra = 1
    fields = ('title', 'category', 'description', 'image', 'model_file', 'sketchfab_embed', 'annotations')

class CollectionInline(admin.TabularInline):
    model = Collection.projects.through
    extra = 1
    verbose_name = "Adicionar a Coleção"
    verbose_name_plural = "Adicionar a Coleções"

class CollectionImageInline(admin.TabularInline):
    model = CollectionImage
    extra = 3


class ArtifactImageInline(admin.TabularInline):
    model = ArtifactImage
    extra = 3
    fields = ('image', 'caption', 'order')


# ===== HOME / CAROUSEL =====
@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'order', 'thumbnail', 'active')
    list_editable = ('order', 'active')
    ordering = ('order', 'id')
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
class ProjectAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'location', 'active', 'share_link_button', 'created_at')
    list_editable = ('active',)
    list_filter = ('active',)
    search_fields = ('title', 'location')
    inlines = [ArtifactInline, CollectionInline]
    readonly_fields = ('share_link_full',)
    actions = ['regenerate_share_token']
    fieldsets = (
        ('Identificação', {
            'fields': ('title', 'slug', 'location', 'cover_image', 'description')
        }),
        ('Compartilhamento privado', {
            'fields': ('active', 'share_link_full'),
            'description': "Desative para ocultar da página pública. O link abaixo permite acesso direto mesmo quando o projeto está inativo — repasse para quem deve ter acesso.",
        }),
    )

    @admin.display(description='Link de compartilhamento', ordering=None)
    def share_link_button(self, obj):
        if not obj.pk:
            return '-'
        url = obj.share_path()
        return format_html(
            '<a href="{0}" target="_blank" class="button" style="font-size:11px;padding:3px 8px;">🔗 Abrir preview</a>',
            url,
        )

    @admin.display(description='URL de compartilhamento')
    def share_link_full(self, obj):
        if not obj.pk:
            return '-'
        url = obj.share_path()
        return format_html(
            '<input type="text" value="{0}" readonly '
            'style="width:100%;padding:6px 10px;font-family:monospace;background:#fff;color:#000;border:1px solid #ccc;border-radius:4px;" '
            'onclick="this.select();" />'
            '<p style="margin-top:6px;font-size:12px;color:#666;">Clique no campo para selecionar e copie (Ctrl+C). '
            'Use a ação "Regenerar token" no menu de ações para invalidar este link.</p>',
            url,
        )

    @admin.action(description='Regenerar token de compartilhamento (invalida o link atual)')
    def regenerate_share_token(self, request, queryset):
        count = 0
        for project in queryset:
            project.share_token = uuid.uuid4()
            project.save(update_fields=['share_token'])
            count += 1
        self.message_user(
            request,
            f"Token regenerado em {count} projeto{'s' if count != 1 else ''}. Os links anteriores foram invalidados.",
            messages.SUCCESS,
        )


@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'category', 'created_at')
    list_filter = ('category', 'project')
    search_fields = ('title', 'description')
    inlines = [ArtifactImageInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('project', 'title', 'category', 'description')
        }),
        ('Mídia', {
            'fields': ('image', 'sketchfab_embed', 'model_file', 'annotations')
        }),
    )


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category',)
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


# ===== PUBLICAÇÕES =====
@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'authors', 'publication_date', 'active', 'order')
    list_editable = ('active', 'order')
    list_filter = ('active', 'publication_date')
    search_fields = ('title', 'authors', 'abstract', 'keywords', 'doi')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Identificação', {
            'fields': ('title', 'slug', 'authors', 'publication_date', 'cover_image')
        }),
        ('Autores detalhados', {
            'fields': ('authors_detailed',),
            'description': "Use este campo para listar autores com afiliação e ORCID. Aceita HTML / rich text.",
            'classes': ('collapse',),
        }),
        ('Conteúdo', {
            'fields': ('abstract', 'pdf_file', 'external_url', 'doi')
        }),
        ('Metadados', {
            'fields': ('keywords', 'categories'),
        }),
        ('Citações', {
            'fields': ('citation_abnt', 'citation_apa'),
            'classes': ('collapse',),
        }),
        ('Configurações', {
            'fields': ('active', 'order')
        }),
    )


# ===== HUB DE APRENDIZADO =====
@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource_type', 'active', 'order')
    list_editable = ('active', 'order')
    list_filter = ('active', 'resource_type')
    search_fields = ('title', 'description')
    fieldsets = (
        ('Identificação', {
            'fields': ('title', 'resource_type', 'thumbnail')
        }),
        ('Conteúdo', {
            'fields': ('description', 'url')
        }),
        ('Configurações', {
            'fields': ('active', 'order')
        }),
    )


# ===== VISITAS VIRTUAIS 3D =====
@admin.register(TourCategory)
class TourCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(VirtualTour)
class VirtualTourAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'language', 'active', 'order', 'created_at')
    list_editable = ('active', 'order')
    list_filter = ('active', 'language', 'categories')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('categories',)
    fieldsets = (
        ('Identificação', {
            'fields': ('title', 'slug', 'tagline', 'location', 'language', 'categories')
        }),
        ('Mídia', {
            'fields': ('thumbnail', 'hero_image')
        }),
        ('Conteúdo', {
            'fields': ('description', 'embed_url', 'embed_code', 'model_file')
        }),
        ('Renderização 3D (.glb / .gltf)', {
            'fields': ('model_exposure', 'model_environment', 'model_tone_mapping', 'model_shadow_intensity'),
            'classes': ('collapse',),
            'description': "Ajuste a iluminação do <model-viewer> para arquivos 3D próprios. Não afeta tours em embed (Sketchfab/Matterport).",
        }),
        ('Configurações', {
            'fields': ('active', 'order')
        }),
    )


# ===== REDES SOCIAIS =====
@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('network', 'url', 'active', 'order')
    list_editable = ('url', 'active', 'order')
    list_filter = ('active',)


# ===== COALITVS =====
@admin.register(CoalitvsGroup)
class CoalitvsGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_label', 'color', 'order')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}


class CoalitvsMemberAdminForm(forms.ModelForm):
    """Substitui o widget M2M de grupos por um dropdown único.
    Internamente o model continua sendo ManyToMany — salvamos como lista de 1 elemento."""
    group = forms.ModelChoiceField(
        queryset=CoalitvsGroup.objects.order_by('order', 'name'),
        required=False,
        label="Grupo",
        empty_label="— Sem grupo —",
        help_text="Selecione o grupo do pesquisador (Internacional, Nacional etc).",
    )

    class Meta:
        model = CoalitvsMember
        exclude = ('groups',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['group'].initial = self.instance.groups.first()

    def _save_m2m(self):
        super()._save_m2m()
        selected = self.cleaned_data.get('group')
        self.instance.groups.set([selected] if selected else [])


@admin.register(CoalitvsMember)
class CoalitvsMemberAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = CoalitvsMemberAdminForm
    list_display = ('name', 'institution', 'country', 'group_display', 'featured', 'active')
    list_editable = ('featured', 'active')
    list_filter = ('active', 'featured', 'groups', 'country')
    search_fields = ('name', 'institution', 'country', 'city', 'expertise', 'role')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('related_projects',)
    fieldsets = (
        ('Identificação', {
            'fields': ('name', 'slug', 'role', 'photo', 'featured')
        }),
        ('Afiliação', {
            'fields': ('institution', 'department', 'city', 'country', 'country_code', 'latitude', 'longitude'),
            'description': "Latitude/longitude usadas no mapa. Você pode obter no Google Maps clicando com botão direito → 'O que há aqui?'.",
        }),
        ('Grupo & Projetos', {
            'fields': ('group', 'related_projects')
        }),
        ('Biografia & Expertise', {
            'fields': ('bio', 'expertise')
        }),
        ('Links', {
            'fields': ('email', 'website', 'lattes', 'orcid'),
            'classes': ('collapse',),
        }),
        ('Configurações', {
            'fields': ('active',)
        }),
    )

    @admin.display(description='Grupo')
    def group_display(self, obj):
        g = obj.groups.first()
        return g.name if g else '—'


# ===== NAVEGAÇÃO — Menu reordenável =====
class NavSubItemInline(SortableTabularInline):
    """Sub-itens (filhos) de um item de dropdown — ex: links dentro de 'Redes'."""
    model = NavItem
    fk_name = 'parent'
    extra = 0
    fields = ('label', 'custom_url', 'open_in_new_tab', 'active', 'order')
    verbose_name = "Sub-item"
    verbose_name_plural = "Sub-itens (aparecem dentro deste dropdown)"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(kind='sublink')

    def save_model(self, request, obj, form, change):
        # Garante kind='sublink' ao salvar via inline
        obj.kind = 'sublink'
        super().save_model(request, obj, form, change)


@admin.register(NavItem)
class NavItemAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('label', 'kind', 'parent', 'custom_url', 'open_in_new_tab', 'active')
    list_editable = ('active',)
    list_filter = ('active', 'kind', 'parent')
    fieldsets = (
        ('Configuração', {
            'fields': ('label', 'kind', 'active', 'open_in_new_tab')
        }),
        ('Sub-item de dropdown (use apenas com Tipo = Sub-item)', {
            'fields': ('parent', 'custom_url'),
            'classes': ('collapse',),
            'description': "Para criar um sub-item dentro de Redes: selecione Tipo = Sub-item, escolha o pai e preencha a URL.",
        }),
    )

    def get_inline_instances(self, request, obj=None):
        # Mostra inline de children só quando estamos editando um dropdown (kind='social')
        if obj and obj.kind == 'social':
            return [NavSubItemInline(self.model, self.admin_site)]
        return []

    def get_queryset(self, request):
        # Lista admin mostra todos (top-level e sub-itens); admin pode reordenar ambos
        return super().get_queryset(request).select_related('parent')


# ===== LCP — Página da parceria =====
@admin.register(LcpPage)
class LcpPageAdmin(admin.ModelAdmin):
    list_display = ('hero_title', 'active', 'external_url', 'updated_at')
    list_editable = ('active',)
    fieldsets = (
        ('Conteúdo', {
            'fields': ('hero_title', 'hero_subtitle', 'logo_lcp', 'content'),
        }),
        ('Botão / Link externo', {
            'fields': ('external_url', 'button_label'),
        }),
        ('Visibilidade', {
            'fields': ('active',),
            'description': "Quando inativo, a página retorna 404 e o item LCP some do menu.",
        }),
    )

    def has_add_permission(self, request):
        # Singleton: só permite criar se não existe
        if LcpPage.objects.exists():
            return False
        return super().has_add_permission(request)
