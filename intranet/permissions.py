"""Controle de acesso da intranet, por usuário e por menu.

Acesso é dado por um registro ``IntranetAccess`` (1-pra-1 com o usuário).
Superuser sempre tem acesso total. ``is_manager`` pode gerenciar contas e
editar todo o conteúdo do site.
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def _access(user):
    if not user.is_authenticated:
        return None
    return getattr(user, "intranet_access", None)


def is_intranet_user(user):
    return bool(user.is_authenticated and (user.is_superuser or _access(user)))


def is_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    acc = _access(user)
    return bool(acc and acc.is_manager)


def can_access_menu(user, menu_key):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    acc = _access(user)
    return bool(acc and acc.can(menu_key))


def can_edit_content(user, slug):
    """Pode editar um tipo de conteúdo do site (slug do CONTENT_REGISTRY)?"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    acc = _access(user)
    return bool(acc and acc.can_content(slug))


def intranet_required(view_func):
    """Login + ter acesso à intranet (registro IntranetAccess ou superuser)."""
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_intranet_user(request.user):
            raise PermissionDenied("Acesso restrito à equipe do LAPOMED.")
        return view_func(request, *args, **kwargs)
    return _wrapped


def manager_required(view_func):
    """Login + ser gestor (ou superuser)."""
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_manager(request.user):
            raise PermissionDenied("Esta ação é restrita a gestores.")
        return view_func(request, *args, **kwargs)
    return _wrapped


def menu_required(menu_key):
    """Login + permissão para o menu indicado."""
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not is_intranet_user(request.user):
                raise PermissionDenied("Acesso restrito à equipe do LAPOMED.")
            if not can_access_menu(request.user, menu_key):
                raise PermissionDenied("Você não tem acesso a esta área.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
