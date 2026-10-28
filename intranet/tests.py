import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Event, EventRegistration, NavItem
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

    def test_event_with_program(self):
        self.client.force_login(self.manager)
        r = self.client.post(reverse("intranet:event_create"), {
            "title": "Simpósio X", "subtitle": "Pesquisas em andamento",
            "start_at": "2030-02-01T09:00", "category": "congresso", "published": "on",
            "event_format": "Online (Teams)",
            "prog_time": ["9:45", "10:00"],
            "prog_speakers": ["Fulano (USP)", ""],
            "prog_title": ["Abertura", "BREAK"],
        })
        self.assertEqual(r.status_code, 302)
        ev = Event.objects.get(title="Simpósio X")
        self.assertEqual(ev.program_items.count(), 2)
        self.assertEqual(ev.subtitle, "Pesquisas em andamento")
        pub = self.client.get(ev.get_absolute_url())
        self.assertContains(pub, "Programa")
        self.assertContains(pub, "Fulano (USP)")
        self.assertContains(pub, "Online (Teams)")

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


class EventRegistrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user("gestor2", password="x")
        IntranetAccess.objects.create(user=cls.manager, is_manager=True)
        cls.event = Event.objects.create(
            title="Simpósio Inscrição", start_at=timezone.now(),
            published=True, registration_open=True)

    def _data(self, **over):
        d = {"name": "Maria Silva", "email": "maria@ex.com",
             "institution": "USP", "consent": "on"}
        d.update(over)
        return d

    def test_register_success(self):
        url = reverse("event_register", args=[self.event.slug])
        r = self.client.post(url, self._data())
        self.assertContains(r, "confirmada")
        self.assertEqual(self.event.registrations.count(), 1)

    def test_consent_required(self):
        url = reverse("event_register", args=[self.event.slug])
        data = self._data()
        data.pop("consent")
        self.client.post(url, data)
        self.assertEqual(self.event.registrations.count(), 0)

    def test_duplicate_email_blocked(self):
        url = reverse("event_register", args=[self.event.slug])
        self.client.post(url, self._data())
        r = self.client.post(url, self._data(name="Outro Nome"))
        self.assertContains(r, "já está inscrito")
        self.assertEqual(self.event.registrations.count(), 1)

    def test_closed_registration_404(self):
        self.event.registration_open = False
        self.event.save()
        r = self.client.get(reverse("event_register", args=[self.event.slug]))
        self.assertEqual(r.status_code, 404)

    def test_invalid_cpf(self):
        url = reverse("event_register", args=[self.event.slug])
        self.client.post(url, self._data(document_type="cpf", document_number="111.111.111-11"))
        self.assertEqual(self.event.registrations.count(), 0)

    def test_valid_cpf_ok(self):
        url = reverse("event_register", args=[self.event.slug])
        # CPF válido de teste
        self.client.post(url, self._data(document_type="cpf", document_number="529.982.247-25"))
        self.assertEqual(self.event.registrations.count(), 1)

    def test_honeypot_drops_silently(self):
        url = reverse("event_register", args=[self.event.slug])
        r = self.client.post(url, self._data(website="http://spam"))
        self.assertContains(r, "confirmada")
        self.assertEqual(self.event.registrations.count(), 0)

    def test_csv_export_requires_login_and_lists(self):
        EventRegistration.objects.create(event=self.event, name="Ana", email="a@x.com", institution="UFRJ")
        csv_url = reverse("intranet:event_registrations_csv", args=[self.event.pk])
        self.assertEqual(self.client.get(csv_url).status_code, 302)  # anônimo -> login
        self.client.force_login(self.manager)
        r = self.client.get(csv_url)
        self.assertEqual(r.status_code, 200)
        self.assertIn("Ana", r.content.decode("utf-8"))


class MenuManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user("gestor3", password="x")
        IntranetAccess.objects.create(user=cls.manager, is_manager=True)
        cls.outsider = User.objects.create_user("fora3", password="x")

    def setUp(self):
        self.client.force_login(self.manager)

    def test_list_page_ok(self):
        NavItem.objects.create(label="Home", kind="home", order=0)
        r = self.client.get(reverse("intranet:menu_list"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Home")

    def test_outsider_blocked(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(reverse("intranet:menu_list")).status_code, 403)

    def test_create_custom_link_assigns_order(self):
        NavItem.objects.create(label="Home", kind="home", order=3)
        r = self.client.post(reverse("intranet:menu_create"), {
            "label": "Contato", "kind": "custom", "custom_url": "/contato/", "active": "on",
        })
        self.assertEqual(r.status_code, 302)
        item = NavItem.objects.get(label="Contato")
        self.assertTrue(item.active)
        self.assertEqual(item.order, 4)  # após o maior order existente

    def test_sublink_without_parent_rejected(self):
        r = self.client.post(reverse("intranet:menu_create"), {
            "label": "Instagram", "kind": "sublink", "custom_url": "https://insta",
        })
        self.assertEqual(r.status_code, 200)  # re-renderiza com erro
        self.assertFalse(NavItem.objects.filter(label="Instagram").exists())

    def test_sublink_with_social_parent_ok(self):
        parent = NavItem.objects.create(label="Redes", kind="social", order=0)
        r = self.client.post(reverse("intranet:menu_create"), {
            "label": "Instagram", "kind": "sublink", "custom_url": "https://insta",
            "parent": parent.pk,
        })
        self.assertEqual(r.status_code, 302)
        child = NavItem.objects.get(label="Instagram")
        self.assertEqual(child.parent_id, parent.pk)

    def test_toggle_flips_active(self):
        item = NavItem.objects.create(label="Eventos", kind="events", active=True, order=0)
        r = self.client.post(reverse("intranet:menu_toggle", args=[item.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["active"])
        item.refresh_from_db()
        self.assertFalse(item.active)

    def test_reorder_persists(self):
        a = NavItem.objects.create(label="A", kind="custom", custom_url="/a/", order=0)
        b = NavItem.objects.create(label="B", kind="custom", custom_url="/b/", order=1)
        r = self.client.post(reverse("intranet:menu_reorder"),
                             data=json.dumps({"ordered_ids": [b.pk, a.pk]}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 200)
        a.refresh_from_db(); b.refresh_from_db()
        self.assertEqual(b.order, 0)
        self.assertEqual(a.order, 1)

    def test_delete_removes(self):
        item = NavItem.objects.create(label="X", kind="custom", custom_url="/x/", order=0)
        r = self.client.post(reverse("intranet:menu_delete", args=[item.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(NavItem.objects.filter(pk=item.pk).exists())
