import json

from django.contrib import messages
from django.db.models import ProtectedError
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from intranet.permissions import menu_required

from . import services
from .models import RepoFolder, RepoFile, MetadataTemplate

MENU = "repositorio"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except (ValueError, TypeError):
        return {}


def _browse(request, folder):
    subfolders = RepoFolder.objects.filter(parent=folder)
    files = RepoFile.objects.filter(folder=folder)
    return render(request, "repositorio/browse.html", {
        "folder": folder,
        "breadcrumb": folder.breadcrumb() if folder else [],
        "subfolders": subfolders,
        "files": files,
        "templates": MetadataTemplate.objects.all(),
        "part_size": services.settings.B2_PART_SIZE,
        "storage_ok": services.is_configured(),
        "nav": MENU,
    })


# ---------------------------------------------------------------------------
# Navegação
# ---------------------------------------------------------------------------
@menu_required(MENU)
def index(request):
    return _browse(request, None)


@menu_required(MENU)
def browse(request, folder_id):
    folder = get_object_or_404(RepoFolder, pk=folder_id)
    return _browse(request, folder)


# ---------------------------------------------------------------------------
# Pastas
# ---------------------------------------------------------------------------
@menu_required(MENU)
@require_POST
def folder_create(request):
    name = (request.POST.get("name") or "").strip()
    parent_id = request.POST.get("parent_id") or None
    parent = get_object_or_404(RepoFolder, pk=parent_id) if parent_id else None
    if name:
        RepoFolder.objects.create(name=name, parent=parent, created_by=request.user)
        messages.success(request, "Pasta criada.")
    else:
        messages.error(request, "Informe um nome para a pasta.")
    return redirect(parent.get_browse_url() if parent else "repositorio:index")


@menu_required(MENU)
@require_POST
def folder_rename(request, pk):
    folder = get_object_or_404(RepoFolder, pk=pk)
    name = (request.POST.get("name") or "").strip()
    if name:
        folder.name = name
        folder.save(update_fields=["name"])
        messages.success(request, "Pasta renomeada.")
    return redirect(folder.get_browse_url())


@menu_required(MENU)
@require_POST
def folder_delete(request, pk):
    folder = get_object_or_404(RepoFolder, pk=pk)
    parent = folder.parent
    if not folder.is_empty():
        messages.error(request, "A pasta não está vazia. Esvazie-a antes de excluir.")
    else:
        folder.delete()
        messages.success(request, "Pasta excluída.")
    return redirect(parent.get_browse_url() if parent else "repositorio:index")


# ---------------------------------------------------------------------------
# Arquivos
# ---------------------------------------------------------------------------
@menu_required(MENU)
def file_detail(request, pk):
    obj = get_object_or_404(RepoFile, pk=pk)
    return render(request, "repositorio/file_detail.html", {
        "file": obj,
        "templates": MetadataTemplate.objects.all(),
        "folders": RepoFolder.objects.all(),
        "nav": MENU,
    })


@menu_required(MENU)
@require_POST
def file_update(request, pk):
    obj = get_object_or_404(RepoFile, pk=pk)
    name = (request.POST.get("name") or "").strip()
    if name:
        obj.name = name

    # mover de pasta
    if "folder_id" in request.POST:
        fid = request.POST.get("folder_id") or None
        obj.folder = get_object_or_404(RepoFolder, pk=fid) if fid else None

    # modelo de metadados aplicado (opcional)
    if "template_id" in request.POST:
        tid = request.POST.get("template_id") or None
        obj.template = get_object_or_404(MetadataTemplate, pk=tid) if tid else None

    # metadados dinâmicos: JSON {coluna: valor}
    raw = request.POST.get("metadata")
    if raw is not None:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                obj.metadata = {str(k): v for k, v in data.items()}
        except (ValueError, TypeError):
            messages.error(request, "Metadados inválidos; nada foi alterado neles.")

    obj.save()
    messages.success(request, "Arquivo atualizado.")
    return redirect("repositorio:file_detail", pk=obj.pk)


@menu_required(MENU)
@require_POST
def file_delete(request, pk):
    obj = get_object_or_404(RepoFile, pk=pk)
    folder = obj.folder
    services.delete_object(obj.object_key)
    obj.delete()
    messages.success(request, "Arquivo excluído.")
    return redirect(folder.get_browse_url() if folder else "repositorio:index")


@menu_required(MENU)
def file_download(request, pk):
    obj = get_object_or_404(RepoFile, pk=pk)
    if obj.status != "ready":
        messages.error(request, "Este arquivo ainda não terminou de subir.")
        return redirect("repositorio:file_detail", pk=obj.pk)
    try:
        url = services.presign_get(obj.object_key, obj.original_filename or obj.name)
    except services.StorageNotConfigured:
        messages.error(request, "Armazenamento não configurado.")
        return redirect("repositorio:file_detail", pk=obj.pk)
    return redirect(url)


# ---------------------------------------------------------------------------
# Upload multipart (JSON) — o conteúdo vai direto do navegador para o B2
# ---------------------------------------------------------------------------
def _storage_guard():
    if not services.is_configured():
        return JsonResponse(
            {"ok": False, "error": "Armazenamento B2 não configurado no servidor."},
            status=503,
        )
    return None


@menu_required(MENU)
@require_POST
def upload_init(request):
    guard = _storage_guard()
    if guard:
        return guard
    data = _json_body(request)
    filename = (data.get("filename") or "").strip()
    name = (data.get("name") or filename or "").strip()
    if not filename or not name:
        return JsonResponse({"ok": False, "error": "nome/arquivo ausente"}, status=400)

    folder = None
    fid = data.get("folder_id")
    if fid:
        try:
            folder = RepoFolder.objects.get(pk=fid)
        except RepoFolder.DoesNotExist:
            return JsonResponse({"ok": False, "error": "pasta inexistente"}, status=400)

    content_type = data.get("content_type") or "application/octet-stream"
    key = services.build_object_key(filename)
    try:
        upload_id = services.create_multipart(key, content_type)
    except services.StorageNotConfigured:
        return _storage_guard()

    obj = RepoFile.objects.create(
        folder=folder, name=name, original_filename=filename,
        object_key=key, content_type=content_type,
        size=int(data.get("size") or 0), status="uploading",
        uploaded_by=request.user,
    )
    return JsonResponse({
        "ok": True, "file_id": obj.pk, "upload_id": upload_id,
        "key": key, "part_size": services.settings.B2_PART_SIZE,
    })


@menu_required(MENU)
@require_POST
def upload_sign(request):
    guard = _storage_guard()
    if guard:
        return guard
    data = _json_body(request)
    try:
        obj = RepoFile.objects.get(pk=data.get("file_id"))
    except (RepoFile.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "arquivo inexistente"}, status=404)
    upload_id = data.get("upload_id")
    part_number = data.get("part_number")
    if not upload_id or not part_number:
        return JsonResponse({"ok": False, "error": "parâmetros ausentes"}, status=400)
    # usa SEMPRE a chave guardada no servidor (não confia na chave do cliente)
    url = services.sign_part(obj.object_key, upload_id, part_number)
    return JsonResponse({"ok": True, "url": url})


@menu_required(MENU)
@require_POST
def upload_complete(request):
    guard = _storage_guard()
    if guard:
        return guard
    data = _json_body(request)
    try:
        obj = RepoFile.objects.get(pk=data.get("file_id"))
    except (RepoFile.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "arquivo inexistente"}, status=404)
    upload_id = data.get("upload_id")
    parts = data.get("parts") or []
    if not upload_id or not parts:
        return JsonResponse({"ok": False, "error": "parâmetros ausentes"}, status=400)
    try:
        services.complete_multipart(obj.object_key, upload_id, parts)
    except Exception as exc:  # falha no B2 → marca erro, não derruba a intranet
        obj.status = "error"
        obj.save(update_fields=["status"])
        return JsonResponse({"ok": False, "error": f"falha ao concluir: {exc}"}, status=502)
    real = services.head_size(obj.object_key)
    if real:
        obj.size = real
    obj.status = "ready"
    obj.save(update_fields=["size", "status", "updated_at"])
    return JsonResponse({"ok": True, "file_id": obj.pk})


@menu_required(MENU)
@require_POST
def upload_abort(request):
    data = _json_body(request)
    try:
        obj = RepoFile.objects.get(pk=data.get("file_id"))
    except (RepoFile.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"ok": True})  # nada a fazer
    upload_id = data.get("upload_id")
    if upload_id:
        services.abort_multipart(obj.object_key, upload_id)
    if obj.status == "uploading":
        obj.delete()
    return JsonResponse({"ok": True})


# ---------------------------------------------------------------------------
# Modelos de metadados
# ---------------------------------------------------------------------------
@menu_required(MENU)
def templates_list(request):
    return render(request, "repositorio/templates.html", {
        "templates": MetadataTemplate.objects.all(), "nav": MENU,
    })


@menu_required(MENU)
def template_form(request, pk=None):
    instance = get_object_or_404(MetadataTemplate, pk=pk) if pk else None
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        fields = request.POST.getlist("fields")
        fields = [f.strip() for f in fields if f.strip()]
        if not name:
            messages.error(request, "Informe um nome para o modelo.")
        else:
            obj = instance or MetadataTemplate()
            obj.name = name
            obj.fields = fields
            obj.save()
            obj.fields = obj.clean_fields_list()
            obj.save(update_fields=["fields"])
            messages.success(request, "Modelo salvo.")
            return redirect("repositorio:templates")
    return render(request, "repositorio/template_form.html", {
        "template": instance, "nav": MENU,
    })


@menu_required(MENU)
@require_POST
def template_delete(request, pk):
    get_object_or_404(MetadataTemplate, pk=pk).delete()
    messages.success(request, "Modelo excluído.")
    return redirect("repositorio:templates")
