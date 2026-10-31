"""Views públicas do Acervo Digital (somente leitura).

Toda rota exige `publico=True` e `status="ready"`; caso contrário, 404.
O bucket continua privado: conteúdo é convertido/transmitido pelo servidor.
"""
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from repositorio import services
from repositorio.models import RepoFile

from . import cache

PER_PAGE = 12
TIPOS = ["map", "3d", "data", "image"]
TIPO_LABELS = [("map", "🗺️ Mapa"), ("3d", "🧊 3D"), ("data", "📊 Dados"), ("image", "🖼️ Imagem")]


def _public_qs():
    return RepoFile.objects.filter(publico=True, status="ready")


def _get_item(slug):
    return get_object_or_404(_public_qs(), public_slug=slug)


def index(request):
    tipo = request.GET.get("tipo") or ""
    regiao = request.GET.get("regiao") or ""

    itens = list(_public_qs().order_by("ordem", "-publicado_em"))
    if tipo:
        itens = [f for f in itens if f.kind() == tipo]
    if regiao:
        itens = [f for f in itens if f.regiao == regiao]

    paginator = Paginator(itens, PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    todos = list(_public_qs())
    counts = {t: sum(1 for f in todos if f.kind() == t) for t in TIPOS}
    regioes = sorted({f.regiao for f in todos if f.regiao})

    return render(request, "acervo/index.html", {
        "page_obj": page_obj,
        "tipo": tipo,
        "regiao": regiao,
        "counts": counts,
        "total": len(todos),
        "regioes": regioes,
        "tipo_labels": TIPO_LABELS,
    })


def item(request, slug):
    return render(request, "acervo/item.html", {"file": _get_item(slug)})


def atlas(request):
    """FeatureCollection com todos os itens geográficos públicos (para o mapa-atlas)."""
    fc = {"type": "FeatureCollection", "features": []}
    for f in _public_qs():
        if f.kind() != "map":
            continue
        try:
            gj = cache.converted(f, "map")
        except services.STORAGE_ERRORS:
            continue
        for feat in (gj or {}).get("features", []):
            props = dict(feat.get("properties") or {})
            props.update({"item": f.public_slug, "regiao": f.regiao, "titulo": f.display_title()})
            fc["features"].append({**feat, "properties": props})
    return JsonResponse(fc)


def item_geo(request, slug):
    f = _get_item(slug)
    if f.kind() != "map":
        raise Http404
    try:
        return JsonResponse(cache.converted(f, "map"))
    except services.STORAGE_ERRORS:
        return HttpResponse(status=503)


def item_table(request, slug):
    f = _get_item(slug)
    if f.kind() != "data":
        raise Http404
    try:
        return JsonResponse(cache.converted(f, "data"))
    except services.STORAGE_ERRORS:
        return HttpResponse(status=503)


def item_raw(request, slug):
    """Transmite os bytes do objeto (GLB/imagem) pela origem do site — sem CORS no bucket."""
    f = _get_item(slug)
    try:
        body, ctype = services.open_object(f.object_key)
    except services.STORAGE_ERRORS:
        raise Http404
    resp = StreamingHttpResponse(body.iter_chunks(), content_type=f.content_type or ctype)
    resp["Content-Disposition"] = "inline"
    return resp


def item_download(request, slug):
    f = _get_item(slug)
    try:
        url = services.presign_get(f.object_key, f.original_filename or f.name)
    except services.STORAGE_ERRORS:
        raise Http404
    return redirect(url)
