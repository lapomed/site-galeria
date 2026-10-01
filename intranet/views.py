import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.forms import modelform_factory
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import (
    Event, Project, Collection, VirtualTour, Slide, Publication, TeamMember,
)
from .forms import EventForm, TaskForm, IntranetUserForm, _StyledModelForm
from .models import Task
from .permissions import (
    intranet_required, professor_required, is_professor, is_intranet_user,
    GROUP_PROFESSOR, GROUP_COLABORADOR,
)

# ---------------------------------------------------------------------------
# Registro de CRUD de conteúdo do site (genérico)
# role: "professor" (só professor) ou "intranet" (professor + colaborador)
# ---------------------------------------------------------------------------
CONTENT_REGISTRY = {
    "projetos":    {"model": Project,     "label": "Projetos",     "role": "professor", "icon": "🏛️"},
    "colecoes":    {"model": Collection,  "label": "Coleções Digitais", "role": "professor", "icon": "🗂️"},
    "visitas-3d":  {"model": VirtualTour, "label": "Visitas 3D",   "role": "professor", "icon": "🥽"},
    "slides":      {"model": Slide,       "label": "Slides da Home", "role": "professor", "icon": "🏠"},
    "publicacoes": {"model": Publication, "label": "Publicações",  "role": "intranet",  "icon": "📚"},
    "equipe":      {"model": TeamMember,  "label": "Equipe",       "role": "professor", "icon": "👥"},
}


def _can_access_content(user, cfg):
    return is_professor(user) if cfg["role"] == "professor" else is_intranet_user(user)


def _content_form_class(model):
    return modelform_factory(model, form=_StyledModelForm, exclude=["created_at", "updated_at"])


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated and is_intranet_user(request.user):
        return redirect("intranet:dashboard")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if not is_intranet_user(user):
            messages.error(request, "Sua conta não tem acesso à intranet. Fale com o administrador.")
        else:
            login(request, user)
            return redirect(request.GET.get("next") or "intranet:dashboard")
    return render(request, "intranet/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("intranet:login")


# ---------------------------------------------------------------------------
# Painel
# ---------------------------------------------------------------------------
@intranet_required
def dashboard(request):
    now = timezone.now()
    my_tasks = (Task.objects.filter(assignees=request.user)
                .exclude(status="done").order_by("due_date", "-created_at")[:8])
    upcoming_deadlines = (Task.objects.exclude(status="done")
                          .filter(due_date__gte=now.date()).order_by("due_date")[:6])
    upcoming_events = Event.objects.filter(start_at__gte=now).order_by("start_at")[:5]
    counts = {
        "todo": Task.objects.filter(status="todo").count(),
        "doing": Task.objects.filter(status="doing").count(),
        "done": Task.objects.filter(status="done").count(),
        "events": Event.objects.count(),
    }
    return render(request, "intranet/dashboard.html", {
        "my_tasks": my_tasks, "upcoming_deadlines": upcoming_deadlines,
        "upcoming_events": upcoming_events, "counts": counts, "nav": "dashboard",
    })


# ---------------------------------------------------------------------------
# Eventos (intranet)
# ---------------------------------------------------------------------------
@intranet_required
def events_list(request):
    events = Event.objects.all()
    return render(request, "intranet/events/list.html", {"events": events, "nav": "eventos"})


@intranet_required
def event_form(request, pk=None):
    instance = get_object_or_404(Event, pk=pk) if pk else None
    form = EventForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if not obj.created_by_id:
            obj.created_by = request.user
        obj.save()
        messages.success(request, "Evento salvo com sucesso.")
        return redirect("intranet:events_list")
    return render(request, "intranet/events/form.html",
                  {"form": form, "instance": instance, "nav": "eventos"})


@intranet_required
@require_POST
def event_delete(request, pk):
    get_object_or_404(Event, pk=pk).delete()
    messages.success(request, "Evento excluído.")
    return redirect("intranet:events_list")


# ---------------------------------------------------------------------------
# Tarefas (Kanban)
# ---------------------------------------------------------------------------
@intranet_required
def tasks_board(request):
    columns = []
    for key, label in Task.STATUS_CHOICES:
        columns.append({
            "key": key, "label": label,
            "tasks": Task.objects.filter(status=key).prefetch_related("assignees").order_by("order", "-created_at"),
        })
    return render(request, "intranet/tasks/board.html", {"columns": columns, "nav": "tarefas"})


@intranet_required
def task_form(request, pk=None):
    instance = get_object_or_404(Task, pk=pk) if pk else None
    form = TaskForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if not obj.created_by_id:
            obj.created_by = request.user
        obj.save()
        form.save_m2m()
        messages.success(request, "Tarefa salva.")
        return redirect("intranet:tasks_board")
    return render(request, "intranet/tasks/form.html",
                  {"form": form, "instance": instance, "nav": "tarefas"})


@intranet_required
@require_POST
def task_delete(request, pk):
    get_object_or_404(Task, pk=pk).delete()
    messages.success(request, "Tarefa excluída.")
    return redirect("intranet:tasks_board")


@intranet_required
@require_POST
def task_move(request):
    """Recebe JSON {task_id, status, ordered_ids:[...]} e reordena a coluna destino."""
    try:
        data = json.loads(request.body or "{}")
        task_id = int(data["task_id"])
        status = data["status"]
        ordered_ids = [int(i) for i in data.get("ordered_ids", [])]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"ok": False, "error": "payload inválido"}, status=400)
    if status not in dict(Task.STATUS_CHOICES):
        return JsonResponse({"ok": False, "error": "status inválido"}, status=400)
    with transaction.atomic():
        Task.objects.filter(pk=task_id).update(status=status)
        for i, tid in enumerate(ordered_ids):
            Task.objects.filter(pk=tid).update(order=i)
    return JsonResponse({"ok": True})


# ---------------------------------------------------------------------------
# Calendário
# ---------------------------------------------------------------------------
@intranet_required
def calendar(request):
    return render(request, "intranet/calendar/index.html", {"nav": "calendario"})


@intranet_required
def calendar_feed(request):
    items = []
    for e in Event.objects.all():
        items.append({
            "title": "📅 " + e.title,
            "start": e.start_at.isoformat(),
            "end": e.end_at.isoformat() if e.end_at else None,
            "url": f"/intranet/eventos/{e.pk}/editar/",
            "color": "#1e3a5f",
        })
    for t in Task.objects.exclude(status="done").exclude(due_date__isnull=True):
        items.append({
            "title": "✓ " + t.title,
            "start": t.due_date.isoformat(),
            "allDay": True,
            "url": f"/intranet/tarefas/{t.pk}/editar/",
            "color": "#f0c300",
            "textColor": "#1a1a1a",
        })
    return JsonResponse(items, safe=False)


# ---------------------------------------------------------------------------
# Equipe / contas
# ---------------------------------------------------------------------------
@intranet_required
def team_list(request):
    members = TeamMember.objects.all()
    users = User.objects.filter(is_active=True).order_by("first_name", "username") if is_professor(request.user) else None
    return render(request, "intranet/team/list.html", {
        "members": members, "users": users,
        "can_manage": is_professor(request.user), "nav": "equipe",
    })


@professor_required
def user_form(request, pk=None):
    instance = get_object_or_404(User, pk=pk) if pk else None
    form = IntranetUserForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Conta salva.")
        return redirect("intranet:team_list")
    return render(request, "intranet/team/user_form.html",
                  {"form": form, "instance": instance, "nav": "equipe"})


# ---------------------------------------------------------------------------
# Conteúdo do site (CRUD genérico)
# ---------------------------------------------------------------------------
@intranet_required
def content_index(request):
    items = []
    for slug, cfg in CONTENT_REGISTRY.items():
        if _can_access_content(request.user, cfg):
            items.append({"slug": slug, **cfg,
                          "count": cfg["model"].objects.count()})
    return render(request, "intranet/content/index.html", {"items": items, "nav": "conteudo"})


def _get_cfg_or_404(request, slug):
    cfg = CONTENT_REGISTRY.get(slug)
    if not cfg:
        raise Http404
    if not _can_access_content(request.user, cfg):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    return cfg


@intranet_required
def content_list(request, slug):
    cfg = _get_cfg_or_404(request, slug)
    objects = cfg["model"].objects.all()
    return render(request, "intranet/content/list.html",
                  {"cfg": cfg, "slug": slug, "objects": objects, "nav": "conteudo"})


@intranet_required
def content_form(request, slug, pk=None):
    cfg = _get_cfg_or_404(request, slug)
    model = cfg["model"]
    instance = get_object_or_404(model, pk=pk) if pk else None
    FormClass = _content_form_class(model)
    form = FormClass(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{cfg['label']}: registro salvo.")
        return redirect("intranet:content_list", slug=slug)
    return render(request, "intranet/content/form.html",
                  {"cfg": cfg, "slug": slug, "form": form, "instance": instance, "nav": "conteudo"})


@intranet_required
@require_POST
def content_delete(request, slug, pk):
    cfg = _get_cfg_or_404(request, slug)
    get_object_or_404(cfg["model"], pk=pk).delete()
    messages.success(request, f"{cfg['label']}: registro excluído.")
    return redirect("intranet:content_list", slug=slug)
