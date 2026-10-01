from django.urls import path
from . import views

app_name = "intranet"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),

    # Eventos
    path("eventos/", views.events_list, name="events_list"),
    path("eventos/novo/", views.event_form, name="event_create"),
    path("eventos/<int:pk>/editar/", views.event_form, name="event_edit"),
    path("eventos/<int:pk>/excluir/", views.event_delete, name="event_delete"),

    # Tarefas
    path("tarefas/", views.tasks_board, name="tasks_board"),
    path("tarefas/nova/", views.task_form, name="task_create"),
    path("tarefas/<int:pk>/editar/", views.task_form, name="task_edit"),
    path("tarefas/<int:pk>/excluir/", views.task_delete, name="task_delete"),
    path("tarefas/mover/", views.task_move, name="task_move"),

    # Calendário
    path("calendario/", views.calendar, name="calendar"),
    path("calendario/feed/", views.calendar_feed, name="calendar_feed"),

    # Equipe / contas
    path("equipe/", views.team_list, name="team_list"),
    path("equipe/conta/nova/", views.user_form, name="user_create"),
    path("equipe/conta/<int:pk>/editar/", views.user_form, name="user_edit"),

    # Conteúdo do site (genérico)
    path("conteudo/", views.content_index, name="content_index"),
    path("conteudo/<slug:slug>/", views.content_list, name="content_list"),
    path("conteudo/<slug:slug>/novo/", views.content_form, name="content_create"),
    path("conteudo/<slug:slug>/<int:pk>/editar/", views.content_form, name="content_edit"),
    path("conteudo/<slug:slug>/<int:pk>/excluir/", views.content_delete, name="content_delete"),
]
