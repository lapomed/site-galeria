import uuid

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
    order = models.PositiveIntegerField(default=0, db_index=True, verbose_name="Ordem")
    active = models.BooleanField(
        default=True, db_index=True, verbose_name="Ativo",
        help_text="Quando desativado, o projeto fica oculto da página pública. Continua acessível via link de compartilhamento.",
    )
    share_token = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False,
        verbose_name="Token de compartilhamento",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "🏛️ Projetos - Projeto"
        verbose_name_plural = "🏛️ Projetos - Projetos"

    def __str__(self):
        return self.title

    def share_path(self):
        return f"/projetos/preview/{self.share_token}/"

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
    description = HTMLField(verbose_name="Descrição")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='artefatos',
        verbose_name="Categoria",
    )
    cover_image = models.ImageField(upload_to='collections/')
    explore_url = models.URLField(
        blank=True,
        verbose_name="Link do botão Explorar",
        help_text="URL de destino do botão 'Explorar' no modal (ex: modelo 3D, página do projeto, tour 3D das Visitas 3D). Se vazio, o botão Explorar não aparece.",
    )
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
    slug = models.SlugField(max_length=300, blank=True, verbose_name="Slug (URL)")
    authors = models.CharField(max_length=500, blank=True, verbose_name="Autores (resumo)")
    authors_detailed = HTMLField(blank=True, verbose_name="Autores (detalhado)", help_text="Liste autores com afiliação e ORCID, um por bloco. HTML permitido.")
    abstract = HTMLField(blank=True, verbose_name="Resumo / Sinopse")
    publication_date = models.DateField(blank=True, null=True, verbose_name="Data de Publicação")
    doi = models.CharField(max_length=200, blank=True, verbose_name="DOI", help_text="Ex: 10.11606/9788566241266")
    external_url = models.URLField(blank=True, verbose_name="Link Externo (repositório, etc)")
    pdf_file = models.FileField(upload_to='publications/', blank=True, null=True, verbose_name="Arquivo PDF")
    cover_image = models.ImageField(upload_to='publications/covers/', blank=True, null=True, verbose_name="Imagem de Capa")
    keywords = models.CharField(max_length=500, blank=True, verbose_name="Palavras-chave", help_text="Separadas por vírgula")
    categories = models.CharField(max_length=300, blank=True, verbose_name="Categorias", help_text="Separadas por vírgula. Ex: Ciências Humanas, Arqueologia")
    citation_abnt = models.TextField(blank=True, verbose_name="Citação ABNT")
    citation_apa = models.TextField(blank=True, verbose_name="Citação APA")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-publication_date', '-created_at']
        verbose_name = "📚 Publicações - Publicação"
        verbose_name_plural = "📚 Publicações - Publicações"

    def __str__(self):
        return self.title

    def doi_url(self):
        if not self.doi:
            return ""
        return self.doi if self.doi.startswith('http') else f"https://doi.org/{self.doi}"

    def keyword_list(self):
        return [k.strip() for k in self.keywords.split(',') if k.strip()]

    def category_list(self):
        return [c.strip() for c in self.categories.split(',') if c.strip()]


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

class TourCategory(models.Model):
    """Categoria temática de Visitas Virtuais (ex: Antigo Oriente Médio, Brasil Colonial)."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    slug = models.SlugField(max_length=120, unique=True, verbose_name="Slug")
    order = models.IntegerField(default=0, verbose_name="Ordem")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "🥽 Visitas 3D - Categoria"
        verbose_name_plural = "🥽 Visitas 3D - Categorias"

    def __str__(self):
        return self.name


class VirtualTour(models.Model):
    title = models.CharField(max_length=300, verbose_name="Título")
    slug = models.SlugField(max_length=300, blank=True, verbose_name="Slug (URL)")
    tagline = models.CharField(max_length=300, blank=True, verbose_name="Tagline", help_text="Frase curta exibida abaixo do título no hero (uma linha)")
    location = models.CharField(max_length=200, blank=True, verbose_name="Localização", help_text="Ex: Beit She'an, Israel")
    language = models.CharField(max_length=50, blank=True, default="Português", verbose_name="Idioma")
    categories = models.ManyToManyField(TourCategory, related_name='tours', blank=True, verbose_name="Categorias")
    description = HTMLField(blank=True, verbose_name="Descrição")
    thumbnail = models.ImageField(upload_to='virtual_tours/', blank=True, null=True, verbose_name="Thumbnail")
    hero_image = models.ImageField(upload_to='virtual_tours/heroes/', blank=True, null=True, verbose_name="Imagem Hero (alta resolução)", help_text="Opcional. Usa a thumbnail como fallback.")
    embed_url = models.URLField(
        blank=True,
        verbose_name="URL Embed",
        help_text=(
            "Cole a URL do tour (Sketchfab, Matterport, Kuula etc.). "
            "Para Sketchfab, tanto a URL da página do modelo "
            "(https://sketchfab.com/3d-models/...) quanto a URL de embed "
            "(.../embed) funcionam — convertemos automaticamente."
        ),
    )
    embed_code = models.TextField(blank=True, verbose_name="Código Embed (iframe)", help_text="Cole o iframe completo, se preferir")
    model_file = models.FileField(upload_to='virtual_tours/models/', blank=True, null=True, verbose_name="Arquivo 3D")

    # Configuracoes de renderizacao do <model-viewer> — afetam apenas tours com model_file
    ENV_CHOICES = [
        ('legacy', 'Legacy (suave, recomendado)'),
        ('neutral', 'Neutral (brilhante)'),
        ('', 'Nenhum (sem IBL)'),
    ]
    TONE_CHOICES = [
        ('commerce', 'Commerce (bom contraste)'),
        ('aces', 'ACES (cinematic)'),
        ('agx', 'AgX (natural)'),
        ('neutral', 'Neutral (sem ajuste)'),
    ]
    model_exposure = models.FloatField(
        default=0.7,
        verbose_name="Exposição",
        help_text="0.4 (escuro) – 1.0 (normal) – 1.5 (brilhante). Default 0.7.",
    )
    model_environment = models.CharField(
        max_length=20, choices=ENV_CHOICES, blank=True, default='legacy',
        verbose_name="Ambiente IBL",
        help_text="Iluminação ambiente. Use 'Legacy' para photogrammetry; 'Nenhum' se o modelo já vem com luz baked.",
    )
    model_tone_mapping = models.CharField(
        max_length=20, choices=TONE_CHOICES, default='commerce',
        verbose_name="Tone Mapping",
        help_text="Compressão de highlights/sombras. 'Commerce' costuma ser o mais agradável.",
    )
    model_shadow_intensity = models.FloatField(
        default=1.0,
        verbose_name="Intensidade da Sombra",
        help_text="0 desliga, 1 normal, 2 sombra forte.",
    )

    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    created_at = models.DateTimeField(auto_now_add=True)

    def get_embed_src(self):
        """Normaliza o embed_url para uma URL que carrega corretamente em iframe.

        Sketchfab e Matterport bloqueiam o carregamento da pagina publica em
        iframes (X-Frame-Options). Aqui transformamos a URL publica na URL
        de embed equivalente.
        """
        url = (self.embed_url or "").strip()
        if not url:
            return ""
        # Sketchfab: /3d-models/<slug>-<id> -> /models/<id>/embed
        if "sketchfab.com/3d-models/" in url and "/embed" not in url:
            tail = url.split("sketchfab.com/3d-models/", 1)[1].rstrip("/")
            tail = tail.split("?", 1)[0].split("#", 1)[0]
            segs = tail.split("-")
            if segs:
                model_id = segs[-1]
                return f"https://sketchfab.com/models/{model_id}/embed?autostart=1&ui_theme=dark"
        # Matterport: my.matterport.com/show/?m=<id> ja funciona; nada a fazer
        # Kuula: kuula.co/share/... ja funciona
        return url

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "🥽 Visitas 3D - Tour"
        verbose_name_plural = "🥽 Visitas 3D - Tours"

    def __str__(self):
        return self.title


# ===== NAVEGAÇÃO — Menu reordenável =====

class NavItem(models.Model):
    """Item de menu do header. Reordenável via drag-and-drop no admin.

    Itens com `kind='social'` (dropdown Redes) podem ter filhos: sub-itens
    com `kind='sublink'` referenciando `parent`. Filhos não podem ter filhos.
    """
    KIND_CHOICES = [
        ('home', 'Home'),
        ('projects', 'Projetos'),
        ('about', 'Quem Somos'),
        ('team', 'Equipe'),
        ('publications', 'Publicações'),
        ('learning_hub', 'Hub de Aprendizado'),
        ('collections', 'Coleções Digitais (dropdown)'),
        ('virtual_tours', 'Visitas Virtuais 3D'),
        ('coalitvs', 'COALITVS'),
        ('lcp', 'LCP — Levantine Ceramics Project'),
        ('social', 'Notícias / Redes (dropdown)'),
        ('sublink', 'Sub-item de dropdown'),
        ('contact', 'Contato'),
        ('custom', 'Custom (URL livre)'),
    ]
    label = models.CharField(max_length=50, verbose_name="Rótulo exibido")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, verbose_name="Tipo")
    custom_url = models.CharField(
        max_length=400, blank=True,
        verbose_name="URL custom",
        help_text="Use apenas com tipo 'Custom' ou 'Sub-item'. Ex: /contato/ ou https://exemplo.com",
    )
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE,
        related_name='children',
        limit_choices_to={'kind': 'social'},
        verbose_name="Pai (apenas para Sub-itens)",
        help_text="Defina apenas para itens do tipo 'Sub-item de dropdown'.",
    )
    open_in_new_tab = models.BooleanField(default=False, verbose_name="Abrir em nova aba")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.PositiveIntegerField(default=0, db_index=True, verbose_name="Ordem")

    class Meta:
        ordering = ['order']
        verbose_name = "🧭 Navegação - Item de Menu"
        verbose_name_plural = "🧭 Navegação - Menu do Header"

    def __str__(self):
        return f"{self.label} ({self.get_kind_display()})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.kind == 'sublink':
            if not self.parent_id:
                raise ValidationError({'parent': "Sub-itens precisam de um pai (item de dropdown)."})
            if not self.custom_url:
                raise ValidationError({'custom_url': "Sub-itens precisam de uma URL."})
        else:
            if self.parent_id:
                raise ValidationError({'parent': "Apenas Sub-itens podem ter pai."})
        if self.parent_id and self.parent.kind == 'sublink':
            raise ValidationError({'parent': "Pai não pode ser um Sub-item (sem aninhamento)."})


# ===== COALITVS — Rede de Pesquisadores =====

class CoalitvsGroup(models.Model):
    """Grupo de trabalho da rede COALITVS (Internacional / Nacional / etc.)."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    slug = models.SlugField(max_length=120, unique=True, verbose_name="Slug")
    short_label = models.CharField(max_length=20, blank=True, verbose_name="Label curto", help_text="Ex: INT, NAC, WG1")
    description = models.CharField(max_length=300, blank=True, verbose_name="Descrição")
    color = models.CharField(max_length=20, default='#f0c300', verbose_name="Cor", help_text="HEX para o marker no mapa")
    order = models.IntegerField(default=0, verbose_name="Ordem")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "🌐 Coalitvs - Grupo"
        verbose_name_plural = "🌐 Coalitvs - Grupos"

    def __str__(self):
        return self.name


class CoalitvsMember(models.Model):
    """Membro da rede internacional COALITVS."""
    name = models.CharField(max_length=200, verbose_name="Nome")
    slug = models.SlugField(max_length=220, unique=True, blank=True, verbose_name="Slug (URL)")
    role = models.CharField(max_length=200, blank=True, verbose_name="Cargo / Função", help_text="Ex: Professor, Pesquisador Responsável")
    institution = models.CharField(max_length=300, verbose_name="Instituição")
    department = models.CharField(max_length=200, blank=True, verbose_name="Departamento / Unidade")
    city = models.CharField(max_length=120, blank=True, verbose_name="Cidade")
    country = models.CharField(max_length=120, verbose_name="País")
    country_code = models.CharField(max_length=3, blank=True, verbose_name="Código ISO (3 letras)", help_text="USA, GBR, BRA…")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Latitude")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Longitude")
    photo = models.ImageField(upload_to='coalitvs/', blank=True, null=True, verbose_name="Foto")
    bio = HTMLField(blank=True, verbose_name="Biografia")
    expertise = models.CharField(max_length=400, blank=True, verbose_name="Áreas de Expertise", help_text="Separadas por vírgula")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    website = models.URLField(blank=True, verbose_name="Website")
    lattes = models.URLField(blank=True, verbose_name="Currículo Lattes")
    orcid = models.CharField(max_length=30, blank=True, verbose_name="ORCID", help_text="Ex: 0000-0001-2345-6789")
    groups = models.ManyToManyField(CoalitvsGroup, related_name='members', blank=True, verbose_name="Grupos")
    related_projects = models.ManyToManyField('Project', related_name='coalitvs_members', blank=True, verbose_name="Projetos relacionados")
    featured = models.BooleanField(default=False, verbose_name="Destaque", help_text="Aparece em primeiro nos cards")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "🌐 Coalitvs - Pesquisador"
        verbose_name_plural = "🌐 Coalitvs - Pesquisadores"

    def __str__(self):
        return self.name

    def expertise_list(self):
        return [t.strip() for t in (self.expertise or '').split(',') if t.strip()]


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


# ===== LCP — Levantine Ceramics Project =====

class LcpPage(models.Model):
    """Página institucional da parceria com o LCP.

    Singleton-ish: o admin permite só uma instância ativa. Quando inativa
    ou inexistente, o NavItem 'lcp' some do menu (sem 404).
    """
    hero_title = models.CharField(
        max_length=200,
        default="LCP — Levantine Ceramics Project",
        verbose_name="Título do Hero",
    )
    hero_subtitle = models.CharField(
        max_length=300, blank=True,
        default="Parceria internacional",
        verbose_name="Subtítulo do Hero",
    )
    logo_lcp = models.ImageField(
        upload_to='lcp/', blank=True, null=True,
        verbose_name="Logo do LCP",
        help_text="Opcional. Se vazio, um placeholder será exibido.",
    )
    hero_bg_image = models.ImageField(
        upload_to='lcp/', blank=True, null=True,
        verbose_name="Imagem de fundo do Hero",
        help_text="Opcional. Imagem de fundo atrás do título. Se vazio, usa o gradiente escuro padrão.",
    )
    content = HTMLField(
        blank=True,
        verbose_name="Conteúdo da página",
        help_text="2-3 parágrafos sobre a parceria com o LCP.",
    )
    external_url = models.URLField(
        default="https://www.levantineceramics.org",
        verbose_name="URL da plataforma LCP",
    )
    button_label = models.CharField(
        max_length=80,
        default="Acessar a plataforma LCP",
        verbose_name="Texto do botão",
    )
    active = models.BooleanField(
        default=False,
        verbose_name="Ativo",
        help_text="Quando desativado, a página retorna 404 e o item LCP some do menu.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "🏺 LCP - Página"
        verbose_name_plural = "🏺 LCP - Página"

    def __str__(self):
        return self.hero_title
