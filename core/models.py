from django.db import models
from tinymce.models import HTMLField

class Slide(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título")
    subtitle = models.TextField(blank=True, verbose_name="Subtítulo / Descrição")
    image = models.ImageField(upload_to='slides/', verbose_name="Imagem")
    link = models.URLField(blank=True, verbose_name="Link (Opcional)")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.IntegerField(default=0, verbose_name="Ordem")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "🏠 Home - Slide do Carousel"
        verbose_name_plural = "🏠 Home - Slides do Carousel"

    def __str__(self):
        return self.title

class Project(models.Model):
    title = models.CharField(max_length=200, verbose_name="Nome do Projeto")
    slug = models.SlugField(unique=True, verbose_name="Slug (URL)")
    description = HTMLField(verbose_name="Descrição")
    location = models.CharField(max_length=200, verbose_name="Localização")
    cover_image = models.ImageField(upload_to='projects/', verbose_name="Imagem de Capa")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "🏛️ Projetos - Projeto"
        verbose_name_plural = "🏛️ Projetos - Projetos"

    def __str__(self):
        return self.title

class Artifact(models.Model):
    CATEGORY_CHOICES = [
        ('artefatos', 'Artefatos'),
        ('escavacoes', 'Escavações'),
        ('edificacoes', 'Edificações / Monumentos'),
    ]
    project = models.ForeignKey(Project, related_name='artifacts', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='artefatos',
        verbose_name="Categoria",
    )
    image = models.ImageField(upload_to='artifacts/', blank=True, null=True)
    sketchfab_embed = models.TextField(blank=True, help_text="Cole o código do iframe do Sketchfab aqui")
    model_file = models.FileField(
        upload_to='artifacts/models/', 
        blank=True, 
        null=True,
        help_text="Upload de arquivo 3D (GLB, GLTF, USDZ)"
    )
    annotations = models.TextField(
        blank=True,
        help_text="Anotações sobre o modelo 3D (opcional) - informações técnicas, descobertas, etc."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "🏛️ Projetos - Artefato"
        verbose_name_plural = "🏛️ Projetos - Artefatos"

    def __str__(self):
        return f"{self.project.title} - {self.title}"
    
    def get_content_type(self):
        """Retorna o tipo de conteúdo do artefato"""
        if self.model_file:
            return '3d_model'
        elif self.sketchfab_embed:
            return 'sketchfab_embed'
        elif self.image:
            return 'image'
        return None

class ArtifactImage(models.Model):
    """Galeria de imagens adicionais de um artefato (alem do `image` principal)."""
    artifact = models.ForeignKey(Artifact, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='artifacts/gallery/')
    caption = models.CharField(max_length=300, blank=True, verbose_name="Legenda")
    order = models.IntegerField(default=0, verbose_name="Ordem")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "🏛️ Projetos - Imagem do Artefato"
        verbose_name_plural = "🏛️ Projetos - Galeria do Artefato"

    def __str__(self):
        return self.caption or f"Imagem #{self.id}"


class Collection(models.Model):
    CATEGORY_CHOICES = [
        ('artefatos', 'Artefatos'),
        ('escavacoes', 'Escavações'),
        ('edificacoes', 'Edificações / Monumentos'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='artefatos',
        verbose_name="Categoria",
    )
    cover_image = models.ImageField(upload_to='collections/')
    projects = models.ManyToManyField(Project, related_name='collections', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "🗂️ Coleções Digitais - Coleção"
        verbose_name_plural = "🗂️ Coleções Digitais - Coleções"

    def __str__(self):
        return self.title

class CollectionImage(models.Model):
    collection = models.ForeignKey(Collection, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='collections/gallery/')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


# ===== MODELOS PARA PÁGINA "QUEM SOMOS" =====

class AboutSection(models.Model):
    """Seção 'Sobre o LAPOMED' - História, Missão, Visão"""
    title = models.CharField(max_length=200, verbose_name="Título", default="Sobre o LAPOMED")
    content = models.TextField(verbose_name="Conteúdo", help_text="Texto sobre o laboratório")
    image = models.ImageField(upload_to='about/', blank=True, null=True, verbose_name="Imagem")
    mission = models.TextField(blank=True, verbose_name="Missão")
    vision = models.TextField(blank=True, verbose_name="Visão")
    values = models.TextField(blank=True, verbose_name="Valores")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "👥 Quem Somos - Seção Sobre"
        verbose_name_plural = "👥 Quem Somos - Seções Sobre"

    def __str__(self):
        return self.title


class TeamMember(models.Model):
    """Membros da equipe do LAPOMED"""
    name = models.CharField(max_length=200, verbose_name="Nome")
    role = models.CharField(max_length=200, verbose_name="Cargo/Função")
    bio = models.TextField(verbose_name="Biografia")
    photo = models.ImageField(upload_to='team/', verbose_name="Foto")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    lattes = models.URLField(blank=True, verbose_name="Currículo Lattes")
    order = models.IntegerField(default=0, verbose_name="Ordem de Exibição")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "👥 Quem Somos - Membro da Equipe"
        verbose_name_plural = "👥 Quem Somos - Equipe"

    def __str__(self):
        return f"{self.name} - {self.role}"


class Timeline(models.Model):
    """Linha do tempo - Marcos importantes do LAPOMED"""
    year = models.IntegerField(verbose_name="Ano")
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descrição")
    image = models.ImageField(upload_to='timeline/', blank=True, null=True, verbose_name="Imagem")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year']
        verbose_name = "👥 Quem Somos - Marco Histórico"
        verbose_name_plural = "👥 Quem Somos - Linha do Tempo"

    def __str__(self):
        return f"{self.year} - {self.title}"


class ResearchArea(models.Model):
    """Áreas de pesquisa do LAPOMED"""
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descrição")
    icon = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Ícone (emoji ou classe CSS)",
        help_text="Ex: 🏺 ou fa-flask"
    )
    order = models.IntegerField(default=0, verbose_name="Ordem")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = "👥 Quem Somos - Área de Pesquisa"
        verbose_name_plural = "👥 Quem Somos - Áreas de Pesquisa"

    def __str__(self):
        return self.title


class Partnership(models.Model):
    """Parcerias e colaborações do LAPOMED"""
    name = models.CharField(max_length=200, verbose_name="Nome da Instituição")
    description = models.TextField(blank=True, verbose_name="Descrição da Parceria")
    logo = models.ImageField(upload_to='partnerships/', verbose_name="Logo")
    website = models.URLField(blank=True, verbose_name="Website")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "👥 Quem Somos - Parceria"
        verbose_name_plural = "👥 Quem Somos - Parcerias"

    def __str__(self):
        return self.name


# ===== PUBLICAÇÕES =====

class Publication(models.Model):
    title = models.CharField(max_length=300, verbose_name="Título")
    authors = models.CharField(max_length=500, blank=True, verbose_name="Autores")
    abstract = HTMLField(blank=True, verbose_name="Resumo")
    publication_date = models.DateField(blank=True, null=True, verbose_name="Data de Publicação")
    external_url = models.URLField(blank=True, verbose_name="Link Externo (DOI, repositório, etc)")
    pdf_file = models.FileField(upload_to='publications/', blank=True, null=True, verbose_name="Arquivo PDF")
    cover_image = models.ImageField(upload_to='publications/covers/', blank=True, null=True, verbose_name="Imagem de Capa")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-publication_date', '-created_at']
        verbose_name = "📚 Publicações - Publicação"
        verbose_name_plural = "📚 Publicações - Publicações"

    def __str__(self):
        return self.title


# ===== HUB DE APRENDIZADO =====

class LearningResource(models.Model):
    RESOURCE_TYPES = [
        ('article', 'Artigo'),
        ('video', 'Vídeo'),
        ('course', 'Curso'),
        ('podcast', 'Podcast'),
        ('book', 'Livro'),
        ('other', 'Outro'),
    ]
    title = models.CharField(max_length=300, verbose_name="Título")
    description = HTMLField(blank=True, verbose_name="Descrição")
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='article', verbose_name="Tipo")
    url = models.URLField(blank=True, verbose_name="Link")
    thumbnail = models.ImageField(upload_to='hub/', blank=True, null=True, verbose_name="Thumbnail")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "🎓 Hub - Recurso"
        verbose_name_plural = "🎓 Hub - Recursos de Aprendizado"

    def __str__(self):
        return self.title


# ===== VISITAS VIRTUAIS 3D =====

class VirtualTour(models.Model):
    title = models.CharField(max_length=300, verbose_name="Título")
    description = HTMLField(blank=True, verbose_name="Descrição")
    thumbnail = models.ImageField(upload_to='virtual_tours/', blank=True, null=True, verbose_name="Thumbnail")
    embed_url = models.URLField(blank=True, verbose_name="URL Embed", help_text="Sketchfab, Matterport, Kuula etc.")
    embed_code = models.TextField(blank=True, verbose_name="Código Embed (iframe)", help_text="Cole o iframe completo, se preferir")
    model_file = models.FileField(upload_to='virtual_tours/models/', blank=True, null=True, verbose_name="Arquivo 3D")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "🥽 Visitas 3D - Tour"
        verbose_name_plural = "🥽 Visitas 3D - Tours"

    def __str__(self):
        return self.title


# ===== REDES SOCIAIS =====

class SocialLink(models.Model):
    NETWORKS = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube / Cortes'),
        ('twitter', 'X / Twitter'),
        ('linkedin', 'LinkedIn'),
    ]
    network = models.CharField(max_length=20, choices=NETWORKS, unique=True, verbose_name="Rede")
    url = models.URLField(blank=True, verbose_name="URL")
    label = models.CharField(max_length=100, blank=True, verbose_name="Rótulo (opcional)")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.IntegerField(default=0, verbose_name="Ordem")

    class Meta:
        ordering = ['order']
        verbose_name = "🔗 Redes - Link Social"
        verbose_name_plural = "🔗 Redes - Links Sociais"

    def __str__(self):
        return self.label or self.get_network_display()
