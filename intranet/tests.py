import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Event
from .models import Task, IntranetAccess


class IntranetAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user("gestor", password="x")
        IntranetAccess.objects.create(user=cls.manager, is_manager=True)

        # colaborador: só Eventos (menu) + Publicações (conteúdo)
        cls.colab = User.objects.create_user("colab", password="x")
        IntranetAccess.objects.create(
            user=cls.colab,
            menu_eventos=True, menu_tarefas=False, menu_calendario=False, menu_equipe=False,
            content_publicacoes=True,
        )

        # sem acesso nenhum (sem IntranetAccess)
        cls.outsider = User.objects.create_user("fora", password="x")

    # --- gating básico ---
    def test_anonymous_redirected_to_login(self):
        r = self.client.get(reverse("intranet:dashboard"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/intranet/login/", r.url)

    def test_outsider_blocked(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(reverse("intranet:dashboard")).status_code, 403)

    def test_manager_sees_all_pages(self):
        self.client.force_login(self.manager)
        for name in ["dashboard", "events_list", "tasks_board", "calendar",
                     "calendar_feed", "team_list", "content_index",
                     "event_create", "task_create", "user_create"]:
            with self.subTest(view=name):
                self.assertEqual(self.client.get(reverse(f"intranet:{name}")).status_code, 200)

    # --- permissão por menu ---
    def test_collaborator_menu_gating(self):
        self.client.force_login(self.colab)
        self.assertEqual(self.client.get(reverse("intranet:dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("intranet:events_list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("intranet:tasks_board")).status_code, 403)
        self.assertEqual(self.client.get(reverse("intranet:calendar")).status_code, 403)
        self.assertEqual(self.client.get(reverse("intranet:team_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("intranet:user_create")).status_code, 403)

    def test_sidebar_shows_only_allowed_menus(self):
        self.client.force_login(self.colab)
        html = self.client.get(reverse("intranet:dashboard")).content.decode()
        self.assertIn(reverse("intranet:events_list"), html)       # tem Eventos
        self.assertNotIn(reverse("intranet:tasks_board"), html)    # não tem Tarefas
        self.assertNotIn(reverse("intranet:calendar"), html)       # não tem Calendário

    # --- permissão por tipo de conteúdo ---
    def test_content_per_type(self):
        self.client.force_login(self.colab)
        # tem Publicações
        self.assertEqual(self.client.get(reverse("intranet:content_index")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("intranet:content_list", args=["publicacoes"])).status_code, 200)
        # NÃO tem Projetos
        self.assertEqual(
            self.client.get(reverse("intranet:content_list", args=["projetos"])).status_code, 403)

    # --- eventos / vitrine pública ---
    def test_event_create_and_public_surface(self):
        self.client.force_login(self.manager)
        r = self.client.post(reverse("intranet:event_create"), {
            "title": "Palestra Teste", "description": "<p>oi</p>",
            "start_at": "2030-01-01T10:00", "category": "palestra", "published": "on",
        })
        self.assertEqual(r.status_code, 302)
        ev = Event.objects.get(title="Palestra Teste")
        self.assertTrue(ev.published and ev.slug)
        pub = self.client.get(reverse("events_list"))
        self.assertContains(pub, "Palestra Teste")
        self.assertEqual(self.client.get(ev.get_absolute_url()).status_code, 200)

    def test_unpublished_event_hidden(self):
        Event.objects.create(title="Rascunho", start_at=timezone.now(), published=False)
        self.assertNotContains(self.client.get(reverse("events_list")), "Rascunho")

    # --- tarefas ---
    def test_task_create_and_move(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("intranet:task_create"),
                         {"title": "Fazer X", "priority": "media", "status": "todo"})
        t = Task.objects.get(title="Fazer X")
        r = self.client.post(reverse("intranet:task_move"),
                             data=json.dumps({"task_id": t.pk, "status": "doing", "ordered_ids": [t.pk]}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 200)
        t.refresh_from_db()
        self.assertEqual(t.status, "doing")

    # --- atalho de criação pelo calendário (?date=) ---
    def test_event_create_prefills_date_from_calendar(self):
        self.client.force_login(self.manager)
        html = self.client.get(
            reverse("intranet:event_create") + "?date=2030-05-01").content.decode()
        self.assertIn("2030-05-01T09:00", html)

    def test_task_create_prefills_date_from_calendar(self):
        self.client.force_login(self.manager)
        html = self.client.get(
            reverse("intranet:task_create") + "?date=2030-05-01").content.decode()
        self.assertIn('value="2030-05-01"', html)

    # --- gestão de contas cria o acesso ---
    def test_manager_creates_account_with_perms(self):
        self.client.force_login(self.manager)
        r = self.client.post(reverse("intranet:user_create"), {
            "username": "novo", "first_name": "No", "last_name": "Vo",
            "email": "n@x.com", "is_active": "on", "password": "senha123",
            "menu_eventos": "on", "content_publicacoes": "on",
        })
        self.assertEqual(r.status_code, 302)
        u = User.objects.get(username="novo")
        acc = u.intranet_access
        self.assertTrue(acc.menu_eventos)
        self.assertTrue(acc.content_publicacoes)
        self.assertFalse(acc.menu_tarefas)
        self.assertFalse(acc.is_manager)
