import io
import zipfile
from unittest import mock

from django.core.cache import cache as dj_cache
from django.test import TestCase, override_settings
from django.urls import reverse

from acervo.converters import kml_to_geojson, kmz_to_geojson, xlsx_to_rows
from repositorio.models import RepoFile
from repositorio.services import StorageNotConfigured


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


@override_settings(
    B2_ENDPOINT="https://s3.example.com", B2_REGION="r",
    B2_KEY_ID="k", B2_APP_KEY="s", B2_BUCKET="b",
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class PublicViewsTests(TestCase):
    def setUp(self):
        dj_cache.clear()
        self.pub_map = RepoFile.objects.create(
            name="portos.kml", object_key="k/portos.kml", status="ready",
            publico=True, public_slug="portos", regiao="Levante",
        )
        self.pub_data = RepoFile.objects.create(
            name="dados.xlsx", object_key="k/dados.xlsx", status="ready",
            publico=True, public_slug="dados",
        )
        self.privado = RepoFile.objects.create(
            name="secreto.kml", object_key="k/secreto.kml", status="ready",
            publico=False, public_slug="secreto",
        )

    def test_item_nao_publico_404(self):
        r = self.client.get(reverse("acervo:item", args=[self.privado.public_slug]))
        self.assertEqual(r.status_code, 404)

    def test_item_publico_200(self):
        r = self.client.get(reverse("acervo:item", args=[self.pub_map.public_slug]))
        self.assertEqual(r.status_code, 200)

    @mock.patch("repositorio.services.fetch_bytes", return_value=SAMPLE_KML)
    def test_atlas_so_inclui_map_publico(self, _fb):
        data = self.client.get(reverse("acervo:atlas")).json()
        nomes = {f["properties"]["item"] for f in data["features"]}
        self.assertIn(self.pub_map.public_slug, nomes)
        self.assertNotIn(self.privado.public_slug, nomes)

    @mock.patch("repositorio.services.presign_get", return_value="https://b2/signed")
    def test_download_redireciona_presign(self, _pg):
        r = self.client.get(reverse("acervo:item_download", args=[self.pub_map.public_slug]))
        self.assertEqual(r.status_code, 302)

    @mock.patch("repositorio.services.fetch_bytes", side_effect=StorageNotConfigured)
    def test_geo_json_storage_ausente_nao_500(self, _fb):
        r = self.client.get(reverse("acervo:item_geo", args=[self.pub_map.public_slug]))
        self.assertIn(r.status_code, (404, 503))

    def test_grade_paginada_preserva_filtro(self):
        for i in range(15):
            RepoFile.objects.create(
                name=f"m{i}.kml", object_key=f"k/m{i}.kml", status="ready",
                publico=True, public_slug=f"m{i}",
            )
        r = self.client.get(reverse("acervo:index"), {"tipo": "map", "page": 2})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["page_obj"].number, 2)
        # a página 2 só contém itens do tipo mapa
        self.assertTrue(all(f.kind() == "map" for f in r.context["page_obj"]))


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class NavTests(TestCase):
    def test_botao_acervo_no_topo(self):
        r = self.client.get(reverse("home"))
        self.assertContains(r, "Acervo Digital")
        self.assertContains(r, reverse("acervo:index"))
