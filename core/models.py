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
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='artifacts', verbose_name="Projeto")
    title = models.CharField(max_length=200, verbose_name="Nome do Artefato")
    description = models.TextField(verbose_name="Descrição do Artefato")
    image = models.ImageField(upload_to='artifacts/', verbose_name="Imagem do Artefato")
    sketchfab_embed = models.TextField(blank=True, verbose_name="Embed 3D (Sketchfab)", help_text="Cole o código iframe do Sketchfab aqui.")

    class Meta:
        verbose_name = "Artefato"
        verbose_name_plural = "Artefatos"

    def __str__(self):
        return self.title
