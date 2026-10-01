from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Event
from .models import Task
from .permissions import GROUP_PROFESSOR, GROUP_COLABORADOR


class IntranetSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        prof_group, _ = Group.objects.get_or_create(name=GROUP_PROFESSOR)
        colab_group, _ = Group.objects.get_or_create(name=GROUP_COLABORADOR)
        cls.prof = User.objects.create_user("prof", password="x")
        cls.prof.groups.add(prof_group)
        cls.colab = User.objects.create_user("colab", password="x")
        cls.colab.groups.add(colab_group)
        cls.outsider = User.objects.create_user("fora", password="x")

    # --- acesso / gating ---
    def test_anonymous_redirected_to_login(self):
        r = self.client.get(reverse("intranet:dashboard"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/intranet/login/", r.url)

    def test_outsider_blocked(self):
        self.client.force_login(self.outsider)
        r = self.client.get(reverse("intranet:dashboard"))
        self.assertEqual(r.status_code, 403)

    def test_main_pages_render_for_professor(self):
        self.client.force_login(self.prof)
        for name in ["dashboard", "events_list", "tasks_board", "calendar",
                     "calendar_feed", "team_list", "content_index",
                     "event_create", "task_create", "user_create"]:
            with self.subTest(view=name):
                self.assertEqual(self.client.get(reverse(f"intranet:{name}")).status_code, 200)

    def test_colaborador_pages(self):
        self.client.force_login(self.colab)
        # pode ver painel e conteúdo (index), mas não CRUD professor-only
        self.assertEqual(self.client.get(reverse("intranet:dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("intranet:content_index")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("intranet:content_list", args=["projetos"])).status_code, 403)
        # publicações é liberado para colaborador
        self.assertEqual(
            self.client.get(reverse("intranet:content_list", args=["publicacoes"])).status_code, 200)
        # criar conta é professor-only
        self.assertEqual(self.client.get(reverse("intranet:user_create")).status_code, 403)

    # --- eventos ---
    def test_event_create_and_public_surface(self):
        self.client.force_login(self.prof)
        r = self.client.post(reverse("intranet:event_create"), {
            "title": "Palestra Teste", "description": "<p>oi</p>",
            "start_at": "2030-01-01T10:00", "category": "palestra", "published": "on",
        })
        self.assertEqual(r.status_code, 302)
        ev = Event.objects.get(title="Palestra Teste")
        self.assertTrue(ev.published)
        self.assertTrue(ev.slug)
        # vitrine pública mostra o publicado
        pub = self.client.get(reverse("events_list"))
        self.assertEqual(pub.status_code, 200)
        self.assertContains(pub, "Palestra Teste")
        self.assertEqual(self.client.get(ev.get_absolute_url()).status_code, 200)

    def test_unpublished_event_hidden(self):
        Event.objects.create(title="Rascunho", start_at=timezone.now(), published=False)
        r = self.client.get(reverse("events_list"))
        self.assertNotContains(r, "Rascunho")

    # --- tarefas ---
    def test_task_create_and_move(self):
        self.client.force_login(self.prof)
        self.client.post(reverse("intranet:task_create"), {
            "title": "Fazer X", "priority": "media", "status": "todo",
        })
        t = Task.objects.get(title="Fazer X")
        self.assertEqual(t.status, "todo")
        import json
        r = self.client.post(reverse("intranet:task_move"),
                             data=json.dumps({"task_id": t.pk, "status": "doing", "ordered_ids": [t.pk]}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 200)
        t.refresh_from_db()
        self.assertEqual(t.status, "doing")
