from django import forms
from django.contrib.auth.models import User, Group

from core.models import Event
from .models import Task
from .permissions import GROUP_PROFESSOR, GROUP_COLABORADOR

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
    """Criação/edição de colaboradores pelo Professor."""
    ROLE_CHOICES = [(GROUP_COLABORADOR, "Colaborador"), (GROUP_PROFESSOR, "Professor")]
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Papel")
    password = forms.CharField(
        required=False, widget=forms.PasswordInput,
        help_text="Deixe em branco para manter a senha atual (ao editar).",
        label="Senha",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            g = self.instance.groups.filter(name=GROUP_PROFESSOR).first()
            self.fields["role"].initial = GROUP_PROFESSOR if g else GROUP_COLABORADOR

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        elif not user.pk:
            user.set_unusable_password()
        if commit:
            user.save()
            self._sync_group(user)
        return user

    def _sync_group(self, user):
        prof, _ = Group.objects.get_or_create(name=GROUP_PROFESSOR)
        colab, _ = Group.objects.get_or_create(name=GROUP_COLABORADOR)
        user.groups.remove(prof, colab)
        target = prof if self.cleaned_data["role"] == GROUP_PROFESSOR else colab
        user.groups.add(target)
