from django.conf import settings
from django.db import models


def human_size(num):
    """Formata bytes em string legível (KB/MB/GB...)."""
    try:
        num = float(num)
    except (TypeError, ValueError):
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}".replace(".0 ", " ")
        num /= 1024.0
    return f"{num:.1f} EB"


class RepoFolder(models.Model):
    """Pasta do repositório (árvore via auto-referência)."""
    name = models.CharField(max_length=200, verbose_name="Nome")
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children",
        on_delete=models.PROTECT, verbose_name="Pasta mãe",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="repo_folders",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Pasta"
        verbose_name_plural = "Pastas"

    def __str__(self):
        return self.name

    def get_browse_url(self):
        from django.urls import reverse
        return reverse("repositorio:browse", args=[self.pk])

    def breadcrumb(self):
        """Lista da raiz até esta pasta (inclusive), para a trilha de navegação."""
        chain, node, seen = [], self, set()
        while node is not None and node.pk not in seen:
            chain.append(node)
            seen.add(node.pk)
            node = node.parent
        return list(reversed(chain))

    def is_empty(self):
        return not self.children.exists() and not self.files.exists()


class MetadataTemplate(models.Model):
    """Conjunto reutilizável de nomes de colunas de metadados."""
    name = models.CharField(max_length=120, unique=True, verbose_name="Nome")
    fields = models.JSONField(default=list, verbose_name="Campos")  # ["Período", "Sítio", ...]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Modelo de metadados"
        verbose_name_plural = "Modelos de metadados"

    def __str__(self):
        return self.name

    def clean_fields_list(self):
        """Normaliza para uma lista de strings não vazias e sem duplicatas."""
        out, seen = [], set()
        for f in self.fields or []:
            label = str(f).strip()
            key = label.lower()
            if label and key not in seen:
                out.append(label)
                seen.add(key)
        return out


class RepoFile(models.Model):
    STATUS_CHOICES = [
        ("uploading", "Enviando"),
        ("ready", "Pronto"),
        ("error", "Erro"),
    ]

    folder = models.ForeignKey(
        RepoFolder, null=True, blank=True, related_name="files",
        on_delete=models.PROTECT, verbose_name="Pasta",
    )
    name = models.CharField(max_length=255, verbose_name="Nome")
    original_filename = models.CharField(max_length=255, blank=True)
    object_key = models.CharField(max_length=500, unique=True, verbose_name="Chave no B2")
    size = models.BigIntegerField(default=0, verbose_name="Tamanho (bytes)")
    content_type = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="uploading")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadados")
    template = models.ForeignKey(
        MetadataTemplate, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name="Modelo aplicado",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="repo_files",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Publicação no acervo público (curadoria por item) ---
    publico = models.BooleanField(default=False, verbose_name="Publicar no acervo")
    public_slug = models.SlugField(
        max_length=300, unique=True, null=True, blank=True, verbose_name="Slug público",
    )
    titulo_publico = models.CharField(max_length=200, blank=True, verbose_name="Título público")
    descricao_publica = models.TextField(blank=True, verbose_name="Descrição pública")
    regiao = models.CharField(max_length=100, blank=True, verbose_name="Região")
    ordem = models.PositiveIntegerField(default=0, verbose_name="Ordem no acervo")
    capa = models.ImageField(
        upload_to="acervo/capas/", null=True, blank=True, verbose_name="Capa (opcional)",
    )
    publicado_em = models.DateTimeField(null=True, blank=True, verbose_name="Publicado em")

    # Extensões reconhecidas por cada visualizador do acervo
    KIND_BY_EXT = {
        "kml": "map", "kmz": "map",
        "glb": "3d", "gltf": "3d",
        "xlsx": "data", "xls": "data", "csv": "data",
        "jpg": "image", "jpeg": "image", "png": "image", "webp": "image", "gif": "image",
    }

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Arquivo"
        verbose_name_plural = "Arquivos"

    def __str__(self):
        return self.name

    def human_size(self):
        return human_size(self.size)

    def extension(self):
        base = self.original_filename or self.name
        return base.rsplit(".", 1)[-1].lower() if "." in base else ""

    def kind(self):
        """Tipo de visualizador do acervo: map | 3d | data | image | other."""
        return self.KIND_BY_EXT.get(self.extension(), "other")

    def display_title(self):
        """Título exibido no acervo (cai para o nome do arquivo se vazio)."""
        return self.titulo_publico or self.name

    def public_url(self):
        from django.urls import reverse
        return reverse("acervo:item", args=[self.public_slug])
