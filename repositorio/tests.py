import json
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from intranet.models import IntranetAccess
from .models import RepoFolder, RepoFile, MetadataTemplate


@override_settings(
    B2_ENDPOINT="https://s3.example.com", B2_REGION="us-west-004",
    B2_KEY_ID="k", B2_APP_KEY="s", B2_BUCKET="bucket",
)
class RepositorioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user("gestor", password="x")
        IntranetAccess.objects.create(user=cls.manager, is_manager=True)

        cls.member = User.objects.create_user("colab", password="x")
        IntranetAccess.objects.create(user=cls.member, menu_repositorio=True)

        cls.outsider = User.objects.create_user("fora", password="x")
        IntranetAccess.objects.create(user=cls.outsider, menu_repositorio=False)

    # --- permissão ---
    def test_requires_menu_permission(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(reverse("repositorio:index")).status_code, 403)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("repositorio:index")).status_code, 200)

    # --- pastas ---
    def test_folder_crud(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("repositorio:folder_create"), {"name": "Cerâmica"})
        f = RepoFolder.objects.get(name="Cerâmica")
        self.client.post(reverse("repositorio:folder_rename", args=[f.pk]), {"name": "Lítico"})
        f.refresh_from_db()
        self.assertEqual(f.name, "Lítico")
        self.client.post(reverse("repositorio:folder_delete", args=[f.pk]))
        self.assertFalse(RepoFolder.objects.filter(pk=f.pk).exists())

    def test_folder_delete_blocked_when_not_empty(self):
        self.client.force_login(self.manager)
        parent = RepoFolder.objects.create(name="pai")
        RepoFolder.objects.create(name="filho", parent=parent)
        self.client.post(reverse("repositorio:folder_delete", args=[parent.pk]))
        self.assertTrue(RepoFolder.objects.filter(pk=parent.pk).exists())

    # --- upload multipart (B2 mockado) ---
    @mock.patch("repositorio.services.create_multipart", return_value="UPID")
    def test_upload_init_creates_file(self, m_create):
        self.client.force_login(self.member)
        r = self.client.post(
            reverse("repositorio:upload_init"),
            data=json.dumps({"filename": "modelo.glb", "name": "Engenho",
                             "content_type": "model/gltf-binary", "size": 12345}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["ok"] and body["upload_id"] == "UPID")
        obj = RepoFile.objects.get(pk=body["file_id"])
        self.assertEqual(obj.status, "uploading")
        m_create.assert_called_once()

    @mock.patch("repositorio.services.sign_part", return_value="https://b2/signed")
    def test_upload_sign(self, m_sign):
        self.client.force_login(self.member)
        obj = RepoFile.objects.create(name="x", object_key="repo/a/x", status="uploading")
        r = self.client.post(
            reverse("repositorio:upload_sign"),
            data=json.dumps({"file_id": obj.pk, "upload_id": "U", "key": "ignored",
                             "part_number": 1}),
            content_type="application/json",
        )
        self.assertEqual(r.json()["url"], "https://b2/signed")
        # deve assinar com a chave guardada, não a enviada pelo cliente
        m_sign.assert_called_once_with("repo/a/x", "U", 1)

    @mock.patch("repositorio.services.head_size", return_value=999)
    @mock.patch("repositorio.services.complete_multipart")
    def test_upload_complete_marks_ready(self, m_complete, m_head):
        self.client.force_login(self.member)
        obj = RepoFile.objects.create(name="x", object_key="repo/a/x", status="uploading")
        r = self.client.post(
            reverse("repositorio:upload_complete"),
            data=json.dumps({"file_id": obj.pk, "upload_id": "U",
                             "parts": [{"PartNumber": 1, "ETag": "etag"}]}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        obj.refresh_from_db()
        self.assertEqual(obj.status, "ready")
        self.assertEqual(obj.size, 999)

    @override_settings(B2_ENDPOINT="", B2_KEY_ID="", B2_APP_KEY="", B2_BUCKET="")
    def test_upload_init_503_when_not_configured(self):
        self.client.force_login(self.member)
        r = self.client.post(
            reverse("repositorio:upload_init"),
            data=json.dumps({"filename": "a.bin", "name": "a", "size": 1}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 503)

    # --- metadados dinâmicos ---
    def test_file_update_saves_dynamic_metadata(self):
        self.client.force_login(self.member)
        obj = RepoFile.objects.create(name="x", object_key="repo/a/x", status="ready")
        self.client.post(reverse("repositorio:file_update", args=[obj.pk]), {
            "name": "Vaso 1",
            "metadata": json.dumps({"Período": "Neolítico", "Sítio": "Çatalhöyük"}),
        })
        obj.refresh_from_db()
        self.assertEqual(obj.name, "Vaso 1")
        self.assertEqual(obj.metadata["Sítio"], "Çatalhöyük")

    # --- download ---
    @mock.patch("repositorio.services.presign_get", return_value="https://b2/get")
    def test_download_redirects_to_signed_url(self, m_get):
        self.client.force_login(self.member)
        obj = RepoFile.objects.create(name="x", object_key="repo/a/x", status="ready")
        r = self.client.get(reverse("repositorio:file_download", args=[obj.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, "https://b2/get")

    # --- render das telas (pega erro de template) ---
    def test_screens_render(self):
        self.client.force_login(self.member)
        obj = RepoFile.objects.create(name="x", object_key="repo/a/x", status="ready",
                                      metadata={"Período": "Neolítico"})
        MetadataTemplate.objects.create(name="Cerâmica", fields=["Período", "Sítio"])
        for url in [reverse("repositorio:index"),
                    reverse("repositorio:file_detail", args=[obj.pk]),
                    reverse("repositorio:templates"),
                    reverse("repositorio:template_create")]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    # --- modelos de metadados ---
    def test_template_create(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("repositorio:template_create"),
                         {"name": "Cerâmica", "fields": ["Período", "Sítio", "Período"]})
        t = MetadataTemplate.objects.get(name="Cerâmica")
        # duplicatas removidas pelo clean_fields_list
        self.assertEqual(t.fields, ["Período", "Sítio"])


class RepoFileAcervoTests(TestCase):
    """Campos/métodos de publicação do acervo público no RepoFile."""

    def test_kind_mapeia_extensoes(self):
        self.assertEqual(RepoFile(name="a.kml").kind(), "map")
        self.assertEqual(RepoFile(name="a.kmz").kind(), "map")
        self.assertEqual(RepoFile(name="a.glb").kind(), "3d")
        self.assertEqual(RepoFile(name="a.gltf").kind(), "3d")
        self.assertEqual(RepoFile(name="a.xlsx").kind(), "data")
        self.assertEqual(RepoFile(name="a.jpg").kind(), "image")
        self.assertEqual(RepoFile(name="a.pdf").kind(), "other")

    def test_display_title_cai_para_name(self):
        self.assertEqual(RepoFile(name="orig.kml").display_title(), "orig.kml")
        self.assertEqual(
            RepoFile(name="orig.kml", titulo_publico="Portos").display_title(),
            "Portos",
        )
