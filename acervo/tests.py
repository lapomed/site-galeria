import io
import zipfile

from django.test import TestCase

from acervo.converters import kml_to_geojson, kmz_to_geojson, xlsx_to_rows


SAMPLE_KML = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
  <Placemark><name>Cartago</name><description>Porto punico</description>
    <Point><coordinates>10.323,36.858,0</coordinates></Point>
  </Placemark>
  <Placemark><name>Rota</name>
    <LineString><coordinates>10.3,36.8 29.9,31.2 23.6,37.9</coordinates></LineString>
  </Placemark>
</Document></kml>"""


def _make_kmz(inner_name, kml_bytes):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(inner_name, kml_bytes)
    return buf.getvalue()


def _make_xlsx(n_rows):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Sitio", "Lat", "Lng"])
    for i in range(n_rows):
        ws.append([f"Porto {i}", 30 + i, 10 + i])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _make_empty_xlsx():
    import openpyxl
    buf = io.BytesIO()
    openpyxl.Workbook().save(buf)
    return buf.getvalue()


class ConvertersTests(TestCase):
    def test_kml_point_e_linestring(self):
        gj = kml_to_geojson(SAMPLE_KML)
        self.assertEqual(gj["type"], "FeatureCollection")
        tipos = {f["geometry"]["type"] for f in gj["features"]}
        self.assertEqual(tipos, {"Point", "LineString"})
        self.assertEqual(gj["features"][0]["properties"]["name"], "Cartago")

    def test_kml_vazio_nao_quebra(self):
        self.assertEqual(kml_to_geojson(b"<kml/>")["features"], [])

    def test_kml_malformado_devolve_vazio(self):
        self.assertEqual(kml_to_geojson(b"nao eh xml")["features"], [])

    def test_kmz_usa_primeiro_kml_interno(self):
        gj = kmz_to_geojson(_make_kmz("qualquer.kml", SAMPLE_KML))
        self.assertGreaterEqual(len(gj["features"]), 1)

    def test_kmz_prefere_doc_kml(self):
        kmz = _make_kmz("doc.kml", SAMPLE_KML)
        self.assertEqual(len(kmz_to_geojson(kmz)["features"]), 2)

    def test_xlsx_respeita_max_rows(self):
        out = xlsx_to_rows(_make_xlsx(300), max_rows=10)
        self.assertEqual(out["columns"], ["Sitio", "Lat", "Lng"])
        self.assertEqual(len(out["rows"]), 10)
        self.assertTrue(out["truncated"])

    def test_xlsx_primeira_aba_vazia_nao_quebra(self):
        out = xlsx_to_rows(_make_empty_xlsx())
        self.assertEqual(out["rows"], [])
