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
