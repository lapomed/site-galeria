"""Papéis e proteção de acesso da intranet.

Dois grupos do Django: "Professor" (acesso total) e "Colaborador" (subconjunto).
Usamos decorators em views baseadas em função (padrão do projeto).
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

GROUP_PROFESSOR = "Professor"
GROUP_COLABORADOR = "Colaborador"
INTRANET_GROUPS = {GROUP_PROFESSOR, GROUP_COLABORADOR}


def is_professor(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=GROUP_PROFESSOR).exists()
    )


def is_intranet_user(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name__in=INTRANET_GROUPS).exists()
    )


def intranet_required(view_func):
    """Exige login + pertencer a um grupo da intranet (Professor ou Colaborador)."""
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_intranet_user(request.user):
            raise PermissionDenied("Acesso restrito à equipe do LAPOMED.")
        return view_func(request, *args, **kwargs)
    return _wrapped


def professor_required(view_func):
    """Exige login + papel Professor (ou superuser)."""
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_professor(request.user):
            raise PermissionDenied("Esta ação é restrita ao Professor.")
        return view_func(request, *args, **kwargs)
    return _wrapped
