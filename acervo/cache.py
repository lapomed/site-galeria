"""Cache das conversões do acervo (converte uma vez por arquivo, reusa depois).

A chave inclui `updated_at`, então trocar o arquivo invalida o cache naturalmente.
"""
from django.core.cache import cache

from repositorio import services

from . import converters

TIMEOUT = 60 * 60 * 24 * 7  # 7 dias


def _key(file, kind):
    stamp = file.updated_at.timestamp() if file.updated_at else 0
    return f"acervo:{kind}:{file.object_key}:{stamp}"


def converted(file, kind):
    """Representação convertida (GeoJSON para map, {columns,rows,...} para data).

    Pode levantar `services.StorageNotConfigured` se o storage não responder —
    a view decide como degradar.
    """
    key = _key(file, kind)
    cached = cache.get(key)
    if cached is not None:
        return cached

    raw = services.fetch_bytes(file.object_key)
    if kind == "map":
        data = (
            converters.kmz_to_geojson(raw)
            if file.extension() == "kmz"
            else converters.kml_to_geojson(raw)
        )
    elif kind == "data":
        data = converters.xlsx_to_rows(raw)
    else:
        data = None

    cache.set(key, data, TIMEOUT)
    return data
