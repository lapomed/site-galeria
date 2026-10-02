from .permissions import can_access_menu, is_manager, is_intranet_user

MENU_KEYS = ["dashboard", "eventos", "tarefas", "calendario", "conteudo", "equipe"]


def intranet_perms(request):
    """Expõe `perms` (acesso por menu) para os templates da intranet."""
    user = getattr(request, "user", None)
    if not user or not is_intranet_user(user):
        return {}
    perms = {k: can_access_menu(user, k) for k in MENU_KEYS}
    perms["is_manager"] = is_manager(user)
    return {"perms": perms}
