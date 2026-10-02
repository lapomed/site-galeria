from django.conf import settings
from django.db import models


class IntranetAccess(models.Model):
    """Acesso de um usuário à intranet, com permissão por menu e por tipo de conteúdo.

    Quem NÃO tem um registro destes (e não é superuser) não entra na intranet.
    """
    # menus simples (além do Painel, sempre liberado)
    MENU_FIELDS = ["menu_eventos", "menu_tarefas", "menu_calendario", "menu_equipe"]
    # mapa slug do tipo de conteúdo -> campo do modelo
    CONTENT_FIELD = {
        "projetos": "content_projetos",
        "colecoes": "content_colecoes",
        "visitas-3d": "content_visitas3d",
        "slides": "content_slides",
        "publicacoes": "content_publicacoes",
        "equipe": "content_equipe",
    }

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="intranet_access", verbose_name="Usuário",
    )
    is_manager = models.BooleanField(
        default=False, verbose_name="Gestor",
        help_text="Pode gerenciar contas e editar TODO o conteúdo do site. Vê todos os menus.",
    )
    # menus
    menu_eventos = models.BooleanField(default=True, verbose_name="Menu: Eventos")
    menu_tarefas = models.BooleanField(default=True, verbose_name="Menu: Tarefas")
    menu_calendario = models.BooleanField(default=True, verbose_name="Menu: Calendário")
    menu_equipe = models.BooleanField(default=False, verbose_name="Menu: Equipe")
    # conteúdo do site — por tipo
    content_projetos = models.BooleanField(default=False, verbose_name="Conteúdo: Projetos")
    content_colecoes = models.BooleanField(default=False, verbose_name="Conteúdo: Coleções")
    content_visitas3d = models.BooleanField(default=False, verbose_name="Conteúdo: Visitas 3D")
    content_slides = models.BooleanField(default=False, verbose_name="Conteúdo: Slides")
    content_publicacoes = models.BooleanField(default=False, verbose_name="Conteúdo: Publicações")
    content_equipe = models.BooleanField(default=False, verbose_name="Conteúdo: Equipe")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Acesso à intranet"
        verbose_name_plural = "Acessos à intranet"

    def __str__(self):
        return f"Acesso de {self.user}"

    def has_any_content(self):
        return any(getattr(self, f) for f in self.CONTENT_FIELD.values())

    def can(self, menu_key):
        """Pode acessar o menu do topo? Gestor pode tudo; Painel sempre liberado."""
        if self.is_manager or menu_key == "dashboard":
            return True
        if menu_key == "conteudo":
            return self.has_any_content()
        return bool(getattr(self, f"menu_{menu_key}", False))

    def can_content(self, slug):
        """Pode editar este tipo de conteúdo do site?"""
        if self.is_manager:
            return True
        field = self.CONTENT_FIELD.get(slug)
        return bool(field and getattr(self, field, False))


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]
    STATUS_CHOICES = [
        ('todo', 'A fazer'),
        ('doing', 'Fazendo'),
        ('done', 'Concluído'),
    ]

    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descrição")
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='tasks',
        verbose_name="Responsáveis",
    )
    due_date = models.DateField(null=True, blank=True, verbose_name="Prazo")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='media', verbose_name="Prioridade")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='todo', verbose_name="Status")
    related_event = models.ForeignKey(
        'core.Event', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', verbose_name="Evento relacionado",
    )
    related_project = models.ForeignKey(
        'core.Project', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', verbose_name="Projeto relacionado",
    )
    order = models.IntegerField(default=0, verbose_name="Ordem na coluna")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"

    def __str__(self):
        return self.title
