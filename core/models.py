from django.db import models

class Slide(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título")
    subtitle = models.CharField(max_length=200, blank=True, verbose_name="Subtítulo")
    image = models.ImageField(upload_to='slides/', verbose_name="Imagem")
    link = models.URLField(blank=True, verbose_name="Link (Opcional)")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        ordering = ['order']
        verbose_name = "Slide (Carousel)"
        verbose_name_plural = "Slides (Carousel)"

    def __str__(self):
        return self.title

class Project(models.Model):
    title = models.CharField(max_length=200, verbose_name="Nome do Projeto")
    slug = models.SlugField(unique=True, verbose_name="Slug (URL)")
    description = models.TextField(verbose_name="Descrição")
    location = models.CharField(max_length=200, verbose_name="Localização")
    cover_image = models.ImageField(upload_to='projects/', verbose_name="Imagem de Capa")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"

    def __str__(self):
        return self.title

class Artifact(models.Model):
    project = models.ForeignKey(Project, related_name='artifacts', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
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
        verbose_name = "Artefato"
        verbose_name_plural = "Artefatos"

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

class Collection(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    cover_image = models.ImageField(upload_to='collections/')
    projects = models.ManyToManyField(Project, related_name='collections', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    active = models.BooleanField(default=True, verbose_name="Ativo")
    order = models.IntegerField(default=0, verbose_name="Ordem")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Seção Sobre"
        verbose_name_plural = "Seções Sobre"

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
        verbose_name = "Membro da Equipe"
        verbose_name_plural = "Membros da Equipe"

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
        ordering = ['-year']  # Mais recente primeiro
        verbose_name = "Marco Histórico"
        verbose_name_plural = "Linha do Tempo"

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
        verbose_name = "Área de Pesquisa"
        verbose_name_plural = "Áreas de Pesquisa"

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
        verbose_name = "Parceria"
        verbose_name_plural = "Parcerias"

    def __str__(self):
        return self.name
