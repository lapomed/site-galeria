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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Artefato"
        verbose_name_plural = "Artefatos"

    def __str__(self):
        return f"{self.project.title} - {self.title}"

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

