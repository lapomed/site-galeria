"""Conversores de arquivos do acervo para formatos que o navegador renderiza.

KML/KMZ -> GeoJSON (parser próprio com stdlib, sem dependência extra).
XLSX -> {columns, rows, truncated} para a prévia de tabela.
"""
import io
import zipfile
import xml.etree.ElementTree as ET

EMPTY = {"type": "FeatureCollection", "features": []}

_GEOM_TAGS = ("Point", "LineString", "Polygon")


def _local(tag):
    """Nome local da tag, ignorando o namespace (`{ns}Placemark` -> `Placemark`)."""
    return tag.rsplit("}", 1)[-1]


def _parse_coords(text):
    """KML 'lon,lat[,alt] lon,lat[,alt] ...' -> [[lon, lat], ...] (ordem GeoJSON)."""
    pts = []
    for tok in (text or "").replace("\n", " ").split():
        parts = tok.split(",")
        if len(parts) >= 2:
            try:
                pts.append([float(parts[0]), float(parts[1])])
            except ValueError:
                continue
    return pts


def _coords_text(el):
    c = el.find(".//{*}coordinates")
    return c.text if c is not None else ""


def _geometry(el):
    """GeoJSON geometry a partir de um elemento de geometria KML, ou None."""
    tag = _local(el.tag)
    if tag == "Point":
        pts = _parse_coords(_coords_text(el))
        return {"type": "Point", "coordinates": pts[0]} if pts else None
    if tag == "LineString":
        pts = _parse_coords(_coords_text(el))
        return {"type": "LineString", "coordinates": pts} if len(pts) >= 2 else None
    if tag == "Polygon":
        rings = []
        for ring in el.findall(".//{*}LinearRing"):
            pts = _parse_coords(_coords_text(ring))
            if pts:
                rings.append(pts)
        return {"type": "Polygon", "coordinates": rings} if rings else None
    return None


def kml_to_geojson(data):
    """Converte bytes KML em FeatureCollection. Nunca levanta: erro -> vazio."""
    try:
        root = ET.fromstring(data)
    except Exception:
        return {"type": "FeatureCollection", "features": []}

    features = []
    for pm in root.iter():
        if _local(pm.tag) != "Placemark":
            continue
        name = desc = ""
        for ch in pm:
            lt = _local(ch.tag)
            if lt == "name":
                name = (ch.text or "").strip()
            elif lt == "description":
                desc = (ch.text or "").strip()
        props = {"name": name, "description": desc}
        # cobre geometrias soltas e dentro de <MultiGeometry>
        for gel in pm.iter():
            if _local(gel.tag) in _GEOM_TAGS:
                geom = _geometry(gel)
                if geom:
                    features.append({"type": "Feature", "properties": props, "geometry": geom})
    return {"type": "FeatureCollection", "features": features}


def kmz_to_geojson(data):
    """Descompacta o KMZ e converte o KML interno (prefere doc.kml)."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except Exception:
        return {"type": "FeatureCollection", "features": []}
    kmls = [n for n in zf.namelist() if n.lower().endswith(".kml")]
    if not kmls:
        return {"type": "FeatureCollection", "features": []}
    chosen = next((n for n in kmls if n.lower().endswith("doc.kml")), kmls[0])
    return kml_to_geojson(zf.read(chosen))


def xlsx_to_rows(data, max_rows=200):
    """1ª aba -> {columns, rows, truncated}. 1ª linha vira cabeçalho."""
    import openpyxl
    try:
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception:
        return {"columns": [], "rows": [], "truncated": False}

    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    columns = []
    try:
        header = next(rows_iter)
        columns = ["" if c is None else str(c) for c in header]
    except StopIteration:
        pass

    rows, truncated = [], False
    for i, row in enumerate(rows_iter):
        if i >= max_rows:
            truncated = True
            break
        rows.append(["" if c is None else c for c in row])
    wb.close()
    return {"columns": columns, "rows": rows, "truncated": truncated}
