from django.conf import settings
from django.db import models


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
