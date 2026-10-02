from django import forms
from django.contrib.auth.models import User

from core.models import Event
from .models import Task, IntranetAccess

# classe base de estilo (Tailwind) aplicada aos inputs
BASE_INPUT = (
    "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-800 "
    "focus:border-lapomed-gold focus:ring-1 focus:ring-lapomed-gold outline-none"
)


class _StyledModelForm(forms.ModelForm):
    """Aplica classes Tailwind automaticamente a todos os widgets."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, (forms.CheckboxInput,)):
                w.attrs.setdefault("class", "h-4 w-4 rounded border-gray-300 text-lapomed-gold")
            elif isinstance(w, (forms.SelectMultiple,)):
                w.attrs.setdefault("class", BASE_INPUT + " min-h-[120px]")
            else:
                w.attrs["class"] = (w.attrs.get("class", "") + " " + BASE_INPUT).strip()


class _DTInput(forms.DateTimeInput):
    input_type = "datetime-local"
    def __init__(self, **kw):
        super().__init__(format="%Y-%m-%dT%H:%M", **kw)


class EventForm(_StyledModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "start_at", "end_at", "location",
                  "cover_image", "registration_url", "category", "published"]
        widgets = {
            "start_at": _DTInput(),
            "end_at": _DTInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ("start_at", "end_at"):
            self.fields[f].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]


class TaskForm(_StyledModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "assignees", "due_date", "priority",
                  "status", "related_event", "related_project"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["due_date"].input_formats = ["%Y-%m-%d"]
        self.fields["assignees"].queryset = User.objects.filter(is_active=True).order_by("first_name", "username")


class IntranetUserForm(_StyledModelForm):
    """Criação/edição de contas da intranet, com acesso por menu."""
    password = forms.CharField(
        required=False, widget=forms.PasswordInput,
        help_text="Deixe em branco para manter a senha atual (ao editar).",
        label="Senha",
    )
    is_manager = forms.BooleanField(
        required=False, label="Gestor",
        help_text="Gestor vê todos os menus, gerencia contas e edita todo o conteúdo.",
    )
    # menus
    menu_eventos = forms.BooleanField(required=False, label="Menu: Eventos")
    menu_tarefas = forms.BooleanField(required=False, label="Menu: Tarefas")
    menu_calendario = forms.BooleanField(required=False, label="Menu: Calendário")
    menu_equipe = forms.BooleanField(required=False, label="Menu: Equipe")
    # conteúdo do site — por tipo
    content_projetos = forms.BooleanField(required=False, label="Conteúdo: Projetos")
    content_colecoes = forms.BooleanField(required=False, label="Conteúdo: Coleções")
    content_visitas3d = forms.BooleanField(required=False, label="Conteúdo: Visitas 3D")
    content_slides = forms.BooleanField(required=False, label="Conteúdo: Slides")
    content_publicacoes = forms.BooleanField(required=False, label="Conteúdo: Publicações")
    content_equipe = forms.BooleanField(required=False, label="Conteúdo: Equipe")

    ACCESS_FIELDS = [
        "menu_eventos", "menu_tarefas", "menu_calendario", "menu_equipe",
        "content_projetos", "content_colecoes", "content_visitas3d",
        "content_slides", "content_publicacoes", "content_equipe",
    ]

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        acc = getattr(self.instance, "intranet_access", None) if self.instance and self.instance.pk else None
        if acc:
            self.fields["is_manager"].initial = acc.is_manager
            for f in self.ACCESS_FIELDS:
                self.fields[f].initial = getattr(acc, f)
        else:
            for f in ("menu_eventos", "menu_tarefas", "menu_calendario"):
                self.fields[f].initial = True

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        elif not user.pk:
            user.set_unusable_password()
        if commit:
            user.save()
            acc, _ = IntranetAccess.objects.get_or_create(user=user)
            acc.is_manager = self.cleaned_data.get("is_manager", False)
            for f in self.ACCESS_FIELDS:
                setattr(acc, f, self.cleaned_data.get(f, False))
            acc.save()
        return user
