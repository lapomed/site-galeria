# Spec — Intranet LAPOMED

**Data:** 2026-10-01
**Branch:** `feat/intranet`
**Status:** aprovado em brainstorming; aguardando revisão final antes do plano de implementação.

---

## 1. Objetivo

Construir uma **intranet** para o LAPOMED — uma área interna, **separada do admin do Django (Jazzmin)** e da navegação pública — onde o **professor** e os **colaboradores** possam:

1. Dar manutenção no conteúdo do site (projetos, coleções, equipe, publicações, visitas 3D, slides, eventos).
2. Cadastrar **eventos** do LAPOMED que aparecem no site público.
3. Gerenciar **tarefas** (com atribuição à equipe) e acompanhar um **calendário** (eventos + prazos).

A intranet tem a **identidade visual do site** (Cinzel/Lato, `lapomed-gold`, Tailwind), mas um **layout de painel** próprio (topbar + sidebar), distinto tanto do admin quanto do site público.

### Não-objetivos (v1)
- Não substitui o admin do Django (que continua exclusivo do dono/superuser).
- Sem notificações por e-mail no v1 (ver §9 — Fase 2).
- Sem cadastro público/self-signup (contas criadas pelo admin/professor).
- Sem app mobile nativo (é web responsivo).

---

## 2. Arquitetura

- **Novo app Django `intranet/`** dentro do mesmo projeto (`lapomed_gallery`).
- URL raiz **`/intranet/`** com `app_name = "intranet"` (namespace).
- **Mesma base de dados** e **mesmo deploy** (Railway). Nenhuma alteração no admin do Jazzmin.
- **Mesmo pipeline Tailwind** (`lapomed/static_src`), com classes/estilos do design system existente.
- Modelos **públicos** (ex.: `Event`) ficam em **`core`**; modelos **internos** (ex.: `Task`) ficam em **`intranet`**.

### Estrutura de arquivos (proposta)
```
core/
  models.py            # + Event (público)
  views.py             # + views públicas de eventos
  urls.py              # + /eventos/
  templates/core/
    events_list.html   # vitrine pública
    partials/_home_events.html  # bloco na home
intranet/
  __init__.py
  apps.py
  models.py            # Task (+ enums/choices)
  forms.py             # ModelForms (Event, Task, e dos modelos do site)
  views.py             # dashboard, eventos, tarefas (kanban), calendário, equipe, conteúdo
  urls.py              # namespace "intranet"
  permissions.py       # mixins/decorators de papel (Professor/Colaborador)
  templates/intranet/
    base_intranet.html # shell do painel (topbar + sidebar)
    login.html
    dashboard.html
    events/ tasks/ calendar/ team/ content/  (list/form/kanban etc.)
  static/intranet/     # JS do kanban/calendar (FullCalendar via CDN)
  tests.py
```

---

## 3. Autenticação e papéis

- **Login próprio** em `/intranet/login/` (template no design do site), usando `django.contrib.auth` (modelo `User` padrão).
- **Logout** em `/intranet/logout/`.
- Dois **grupos** do Django: **`Professor`** e **`Colaborador`** (criados por data migration idempotente).
- **Criação de contas:** pelo admin do Django (você). Opcional no v1: tela "Usuários" na intranet para o **Professor** criar/editar colaboradores (CRUD de `User` + atribuição de grupo). *(incluir se aprovado; caso contrário, contas só pelo admin.)*
- **Vínculo com a equipe:** `TeamMember.user = OneToOneField(User, null=True, blank=True)` para que atribuição de tarefas mostre foto/nome da pessoa e ligue o login ao perfil público.
- **Proteção de acesso:**
  - Todas as views da intranet exigem `login_required`.
  - Checagem de papel via **mixin** (`ProfessorRequiredMixin`, `IntranetUserMixin`) e/ou decorator.
  - `/intranet/` nunca acessível a anônimo; redireciona para `/intranet/login/`.
  - Usuário sem grupo Professor/Colaborador não acessa a intranet (mesmo autenticado).

### Matriz de permissões (v1)

| Recurso | Professor | Colaborador |
|---|---|---|
| Painel / Calendário | ✅ ver | ✅ ver |
| Tarefas | ✅ criar/editar/atribuir a qualquer um | ✅ criar; editar as suas e as atribuídas a si |
| Eventos (intranet + publicar no site) | ✅ | ✅ |
| Publicações | ✅ | ✅ |
| Equipe — própria bio | ✅ | ✅ (só a própria) |
| Equipe — todos / gestão de contas | ✅ | ❌ |
| Conteúdo do site: Projetos, Coleções, Visitas 3D, Slides | ✅ | ❌ (ver, sem editar) *(ajustável)* |

> A granularidade por recurso é configurável; estes são os padrões propostos. Ajustar se necessário na revisão.

---

## 4. Modelos de dados

### 4.1 `core.Event` (público)
| Campo | Tipo | Notas |
|---|---|---|
| `title` | CharField(200) | Título |
| `slug` | SlugField | gerado do título |
| `description` | HTMLField (TinyMCE) | Descrição rica |
| `start_at` | DateTimeField | Início |
| `end_at` | DateTimeField (null) | Fim (opcional) |
| `location` | CharField(300, blank) | Local |
| `cover_image` | ImageField (blank/null) | Imagem do card |
| `registration_url` | URLField(blank) | Link de inscrição |
| `category` | CharField/choices (blank) | Ex.: Palestra, Workshop, Defesa, Exposição |
| `published` | BooleanField(default False) | Aparece no site |
| `created_by` | FK(User, null) | Autoria |
| `created_at`/`updated_at` | DateTime | Timestamps |

- Métodos: `is_upcoming()` (start_at >= agora), `get_absolute_url()`.
- Verbose name com prefixo de emoji (padrão do projeto, ex.: "📅 Eventos - Evento") para aparecer bem no admin também.

### 4.2 `intranet.Task` (interno)
| Campo | Tipo | Notas |
|---|---|---|
| `title` | CharField(200) | |
| `description` | TextField(blank) | |
| `assignees` | ManyToMany(User, blank) | Responsáveis |
| `due_date` | DateField(null, blank) | Prazo (entra no calendário) |
| `priority` | choices: baixa/média/alta | |
| `status` | choices: `todo`/`doing`/`done` | colunas do Kanban |
| `related_event` | FK(core.Event, null, blank) | vínculo opcional |
| `related_project` | FK(core.Project, null, blank) | vínculo opcional |
| `order` | IntegerField(default 0) | ordenação na coluna do Kanban |
| `created_by` | FK(User, null) | |
| `created_at`/`updated_at` | DateTime | |

### 4.3 Calendário
- **Sem modelo novo.** Um endpoint JSON (`/intranet/calendar/feed/`) agrega **Eventos** (start/end) + **prazos de Tarefas** (due_date) e alimenta o FullCalendar.

---

## 5. Telas da intranet

1. **Login** (`/intranet/login/`) — card central no design do site.
2. **Painel** (`/intranet/`) — "Minhas tarefas", "Próximos prazos", "Próximos eventos", atalhos rápidos.
3. **Eventos** (`/intranet/eventos/`) — lista + formulário (criar/editar/excluir), toggle "publicar no site".
4. **Tarefas** (`/intranet/tarefas/`) — **quadro Kanban** (A fazer / Fazendo / Concluído) com drag-and-drop (atualiza `status`/`order` via fetch) + filtros (responsável, prioridade, prazo) e uma visão lista.
5. **Calendário** (`/intranet/calendario/`) — FullCalendar (mês/semana) consumindo o feed JSON.
6. **Equipe** (`/intranet/equipe/`) — lista de colaboradores; para Professor, gestão de contas e vínculo `User`↔`TeamMember`.
7. **Conteúdo do site** (`/intranet/conteudo/...`) — CRUDs no design do site para: Projetos, Coleções (+imagens inline), Equipe, Publicações, Visitas 3D, Slides, Eventos. Reuso de `ModelForm`; listagem + formulário padronizados.

### UX/Design
- `base_intranet.html`: topbar (logo LAPOMED + nome do usuário + sair) e **sidebar** com os itens acima; conteúdo à direita.
- Fonte/cor do site; cards de listagem no mesmo padrão; responsivo (sidebar colapsa no mobile).
- Mensagens de sucesso/erro via `django.contrib.messages`.

---

## 6. Vitrine pública (site)

- **Nova página `/eventos/`** (`core`): próximos e passados, cards no design do site (imagem, título, data/hora, local, resumo, botão inscrição). Só mostra `published=True`.
- **Bloco "Próximos eventos" na home** (próximos N eventos publicados).
- **Item no menu** via `NavItem` (novo `kind='events'`), roteado nos partials `_nav_item_desktop/mobile`.
- Detalhe de evento: página `/eventos/<slug>/` (ou modal — decidir no plano; padrão: página).

---

## 7. Segurança

- Namespace `/intranet/` isolado; `login_required` + checagem de papel em todas as views.
- CSRF em todos os formulários e nas chamadas fetch (Kanban/calendar).
- Uploads de imagem tratados como hoje (MEDIA + WhiteNoise/Storage).
- Nada da intranet exposto a anônimo; feeds JSON também protegidos.
- Sem segredos no front; ações destrutivas com confirmação.

---

## 8. Migrations & deploy

- Novos modelos (`Event`, `Task`) + `TeamMember.user` + data migration dos grupos → **migrations novas**.
- **Atenção ao histórico de migrations** para não criar "multiple leaf nodes" (lição do projeto): sempre partir da main atualizada e checar `makemigrations --check` antes de abrir PR; o entrypoint já faz `makemigrations --merge` defensivo no boot.
- Deploy no Railway roda `migrate` automaticamente.

---

## 9. Notificações

- **v1: apenas in-app** (o painel mostra tarefas/prazos/eventos).
- **Fase 2 (e-mail):** aviso de tarefa atribuída e lembrete de evento. Requer configurar backend de e-mail (SMTP/USP ou provedor) em `settings`/Railway. Fora do v1.

---

## 10. Testes

- Projeto **sem suíte** hoje. Incluir **testes de fumaça** no app `intranet`:
  - Gating: anônimo → redirect login; colaborador não acessa áreas de professor.
  - CRUD básico de `Event` e `Task`.
  - Vitrine pública `/eventos/` só mostra publicados.
- `manage.py check` limpo como gate mínimo.

---

## 11. Faseamento da implementação

1. **Base** — app `intranet`, `base_intranet.html` (layout/design), login/logout, grupos+papéis, mixins de permissão, painel com placeholders.
2. **Eventos** — modelo `Event`, CRUD na intranet, vitrine pública (`/eventos/` + bloco home + NavItem).
3. **Tarefas + Calendário** — modelo `Task`, Kanban (drag-and-drop), feed JSON, FullCalendar.
4. **Equipe/contas + Conteúdo do site** — vínculo `User`↔`TeamMember`, gestão de contas (professor), CRUDs dos modelos do site.

Cada fase é um PR próprio (com sua migration, se houver), partindo da main atualizada.

---

## 12. Questões em aberto (resolver na revisão)

1. **Gestão de contas na intranet** pelo Professor entra no v1, ou contas só pelo admin do Django?
2. **Permissões do Colaborador** nos CRUDs de conteúdo do site — manter restrito (padrão proposto) ou liberar mais?
3. **Detalhe de evento**: página dedicada (padrão) ou modal reutilizando o do site?
4. **Kanban com drag-and-drop** (proposto) vs. lista simples com troca de status por botão (mais simples) no v1?
5. **E-mail** mesmo sendo Fase 2 — alguma urgência que justifique antecipar?

---

## 13. Status da implementação (v1 — PR único)

Implementado nesta entrega:
- App `intranet` em `/intranet/` com shell próprio (sidebar + topbar) no design do site.
- Login/logout próprios + grupos **Professor**/**Colaborador** (data migration) + mixins de permissão.
- Painel, **Eventos** (CRUD + vitrine pública `/eventos/` + detalhe + card na home + NavItem `events`), **Tarefas** (Kanban com arrastar + endpoint de mover), **Calendário** (FullCalendar + feed JSON), **Equipe/contas** (gestão de contas pelo Professor, vínculo `User`↔`TeamMember`), e **Conteúdo do site** (CRUD genérico: Projetos, Coleções, Visitas 3D, Slides, Publicações, Equipe).
- Admin do dono também ganhou `Event` e `Task`.
- Suíte de testes de fumaça (7 testes) + `lapomed_gallery/test_settings.py` (roda a suíte em SQLite desativando migrations, contornando o bug da 0016).

**Defaults aplicados nas 5 questões em aberto:** (1) gestão de contas na intranet = sim (Professor); (2) Colaborador restrito conforme matriz; (3) evento com página de detalhe; (4) Kanban com arrastar; (5) e-mail = Fase 2.

**Limitação conhecida (v1):** galerias de imagem aninhadas (ex.: imagens de Coleção, galeria de Artefato) ainda são gerenciadas pelo admin do Django — o CRUD genérico da intranet edita os campos do próprio registro, não os inlines. Fica para uma Fase 2 (formsets).
