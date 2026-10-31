# Acervo Digital Público — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expor os arquivos do Repositório (interno) como um acervo público navegável com mapa-atlas, 3D, planilhas e imagens, curado por item.

**Architecture:** Campos de publicação no `repositorio.RepoFile`; app novo `acervo` só-leitura que lê esses modelos, converte/serve conteúdo pelo servidor (bucket segue privado) e cacheia. Mapa Leaflet (tiles Esri sem key) + `model-viewer` + preview de tabela.

**Tech Stack:** Django 6, Leaflet 1.9.4, `<model-viewer>`, `openpyxl`, `xml.etree`+`zipfile` (KML/KMZ próprios), Tailwind (design system existente).

**Spec:** `docs/superpowers/specs/2026-10-31-acervo-publico-design.md`

## Global Constraints

- Python deps via **UV** (`uv add ...`, `uv run python manage.py ...`); Node via NPM. Porta 4008. Idioma pt-br.
- Testes rodam com `uv run python manage.py test <app>`.
- **A home principal (`/`, `core/templates/core/home.html`) NÃO é alterada.** Única mudança em arquivo compartilhado: rótulo/href do botão em `core/templates/core/base.html`.
- Bucket MinIO/B2 continua **privado**: nada de objeto público; `object_key` nunca vai ao cliente.
- Toda rota pública exige `publico=True` **e** `status="ready"`, senão **404**.
- Mapa escuro sem API key: tiles **Esri Dark Gray** `{z}/{y}/{x}` (base + reference), `maxNativeZoom:16` (ver PR #21).
- Sem linha de atribuição em commits.

## Review Focus

- **KML/KMZ malformado ou vazio** (sem `Placemark`, namespace inesperado): converter devolve FeatureCollection vazia, nunca 500. → Task 2.
- **KMZ sem `doc.kml`** (nome interno diferente): usar o primeiro `*.kml` do zip. → Task 2.
- **Storage não configurado / objeto ausente** (`fetch_bytes` falha): rotas `geo.json`/`tabela.json`/`raw` degradam (404/503), não 500. → Task 3.
- **XLSX grande (63 MB) / 1ª aba vazia ou com células mescladas**: preview respeita `max_rows` e não carrega a planilha inteira na resposta. → Task 2.
- **Colisão de slug ao publicar** dois arquivos com mesmo título: sufixo `-2`, `-3`… garante unicidade. → Task 4.

---

### Task 1: Campos de publicação no RepoFile

**Files:**
- Modify: `repositorio/models.py` (classe `RepoFile`)
- Create: `repositorio/migrations/0005_acervo_publico.py` (via makemigrations)
- Test: `repositorio/tests.py` (nova classe `RepoFileAcervoTests`)

**Interfaces:**
- Produces: `RepoFile.publico: bool`, `.public_slug: str|None`, `.titulo_publico: str`, `.descricao_publica: str`, `.regiao: str`, `.ordem: int`, `.capa` (ImageField), `.publicado_em: datetime|None`; métodos `.kind() -> str` (`"map"|"3d"|"data"|"image"|"other"`), `.display_title() -> str` (titulo_publico ou name), `.public_url() -> str`.

- [ ] **Step 1: Escrever testes que falham** em `repositorio/tests.py`:

```python
def test_kind_mapeia_extensoes():
    assert RepoFile(name="a.kml").kind() == "map"
    assert RepoFile(name="a.kmz").kind() == "map"
    assert RepoFile(name="a.glb").kind() == "3d"
    assert RepoFile(name="a.xlsx").kind() == "data"
    assert RepoFile(name="a.jpg").kind() == "image"
    assert RepoFile(name="a.pdf").kind() == "other"

def test_display_title_cai_para_name():
    assert RepoFile(name="orig.kml").display_title() == "orig.kml"
    assert RepoFile(name="orig.kml", titulo_publico="Portos").display_title() == "Portos"
```

- [ ] **Step 2: Rodar e ver falhar** — `uv run python manage.py test repositorio.tests.RepoFileAcervoTests -v 2` → FAIL (campos/métodos inexistentes).
- [ ] **Step 3: Adicionar os campos** na tabela do spec (seção "Modelo de dados") a `RepoFile` e os métodos `kind()`, `display_title()`, `public_url()` (`public_url` usa `reverse("acervo:item", args=[self.public_slug])`). `kind()` deriva de `self.extension()`.
- [ ] **Step 4: Gerar migration** — `uv run python manage.py makemigrations repositorio`.
- [ ] **Step 5: Rodar e ver passar** — `uv run python manage.py test repositorio.tests.RepoFileAcervoTests -v 2` → PASS.
- [ ] **Step 6: Commit** — `git commit -m "feat(acervo): campos de publicacao e kind() no RepoFile"`

---

### Task 2: Conversores + acesso a bytes do storage

**Files:**
- Modify: `repositorio/services.py` (novo `fetch_bytes`)
- Create: `acervo/__init__.py`, `acervo/apps.py`, `acervo/converters.py`
- Modify: `lapomed_gallery/settings.py` (`INSTALLED_APPS += ["acervo"]`)
- Modify: `pyproject.toml` (via `uv add openpyxl`)
- Test: `acervo/tests.py` (`ConvertersTests`), fixtures em `acervo/tests_fixtures/`

**Interfaces:**
- Produces: `services.fetch_bytes(key: str) -> bytes` (via boto3 `get_object`; levanta `StorageNotConfigured` se não configurado); `converters.kml_to_geojson(data: bytes) -> dict`; `converters.kmz_to_geojson(data: bytes) -> dict`; `converters.xlsx_to_rows(data: bytes, max_rows: int = 200) -> dict` com forma `{"columns": [...], "rows": [[...]], "truncated": bool}`.

- [ ] **Step 1: Criar app** `acervo` (`apps.py` com `name="acervo"`, `__init__.py` vazio) e adicionar a `INSTALLED_APPS`. `uv add openpyxl`.
- [ ] **Step 2: Escrever testes que falham** em `acervo/tests.py` (usar fixtures mínimos — gerar KML/KMZ/XLSX pequenos no `setUp` ou arquivos em `tests_fixtures/`):

```python
def test_kml_point_e_linestring():
    gj = kml_to_geojson(SAMPLE_KML)  # 1 Point + 1 LineString nomeados
    assert gj["type"] == "FeatureCollection"
    assert {f["geometry"]["type"] for f in gj["features"]} == {"Point", "LineString"}
    assert gj["features"][0]["properties"]["name"]

def test_kml_vazio_nao_quebra():
    assert kml_to_geojson(b"<kml/>")["features"] == []

def test_kml_malformado_devolve_vazio():
    assert kml_to_geojson(b"nao eh xml")["features"] == []

def test_kmz_usa_primeiro_kml_interno():
    gj = kmz_to_geojson(SAMPLE_KMZ)  # zip com "qualquer.kml" (sem doc.kml)
    assert len(gj["features"]) >= 1

def test_xlsx_respeita_max_rows():
    out = xlsx_to_rows(SAMPLE_XLSX_300_LINHAS, max_rows=10)
    assert out["columns"] and len(out["rows"]) == 10 and out["truncated"] is True

def test_xlsx_primeira_aba_vazia_nao_quebra():
    out = xlsx_to_rows(SAMPLE_XLSX_VAZIO)
    assert out["rows"] == []
```

- [ ] **Step 3: Rodar e ver falhar** — `uv run python manage.py test acervo.tests.ConvertersTests -v 2`.
- [ ] **Step 4: Implementar** `fetch_bytes` em `services.py` e os três conversores em `converters.py`. KML: parse com `xml.etree`, ignorar namespace (match por `localname`), suportar `Point`/`LineString`/`Polygon`/`MultiGeometry`, ler `name`/`description`; qualquer exceção de parse → `{"type":"FeatureCollection","features":[]}`. KMZ: `zipfile`, primeiro `*.kml` (preferir `doc.kml` se existir). XLSX: `openpyxl.load_workbook(read_only=True, data_only=True)`, 1ª aba, 1ª linha = colunas, parar em `max_rows`.
- [ ] **Step 5: Rodar e ver passar** — mesmo comando → PASS.
- [ ] **Step 6: Commit** — `git commit -m "feat(acervo): conversores KML/KMZ/XLSX e fetch_bytes"`

---

### Task 3: App acervo — views, rotas e templates públicos

**Files:**
- Create: `acervo/urls.py`, `acervo/views.py`, `acervo/cache.py` (helper de cache de conversão)
- Create: `acervo/templates/acervo/index.html`, `acervo/templates/acervo/item.html`
- Modify: `lapomed_gallery/urls.py` (`path("acervo/", include("acervo.urls"))`)
- Test: `acervo/tests.py` (`PublicViewsTests`)

**Interfaces:**
- Consumes: Task 1 (`RepoFile.publico/.public_slug/.kind()/.display_title()`), Task 2 (`services.fetch_bytes`, `converters.*`).
- Produces: `app_name="acervo"` com nomes `index`, `item`, `item_geo`, `item_table`, `item_raw`, `item_download`, `atlas`. Helper `cache.converted(file, kind) -> dict` (chave `f"acervo:{kind}:{file.object_key}:{file.updated_at.timestamp()}"`, timeout 7 dias).

- [ ] **Step 1: Escrever testes que falham** em `acervo/tests.py` (criar RepoFile público e não-público; `@override_settings` de storage; mock de `services.fetch_bytes`):

```python
def test_item_nao_publico_404():
    r = self.client.get(reverse("acervo:item", args=[self.privado.public_slug or "x"]))
    assert r.status_code == 404

def test_item_publico_200():
    assert self.client.get(reverse("acervo:item", args=[self.pub_map.public_slug])).status_code == 200

def test_atlas_so_inclui_map_publico():
    data = self.client.get(reverse("acervo:atlas")).json()
    nomes = {f["properties"]["item"] for f in data["features"]}
    assert self.pub_map.public_slug in nomes and self.privado.public_slug not in nomes

def test_download_redireciona_presign(self):  # mock presign_get
    r = self.client.get(reverse("acervo:item_download", args=[self.pub_map.public_slug]))
    assert r.status_code == 302

def test_geo_json_storage_ausente_nao_500(self):  # fetch_bytes levanta StorageNotConfigured
    r = self.client.get(reverse("acervo:item_geo", args=[self.pub_map.public_slug]))
    assert r.status_code in (404, 503)

def test_grade_paginada_preserva_filtro(self):  # 15 itens map publicos, 12 por pagina
    r = self.client.get(reverse("acervo:index"), {"tipo": "map", "page": 2})
    assert r.status_code == 200
    assert r.context["page_obj"].number == 2
```

- [ ] **Step 2: Rodar e ver falhar** — `uv run python manage.py test acervo.tests.PublicViewsTests -v 2`.
- [ ] **Step 3: Implementar views e urls.** `index`: filtra `publico=True, status="ready"`, aplica `?tipo=` e `?regiao=`, pagina 12 (`Paginator`), monta contadores; contexto `page_obj`, filtros, lista de regiões. `item`: `get_object_or_404(RepoFile, public_slug=slug, publico=True, status="ready")`. `item_geo`/`item_table`: chamam `cache.converted(...)` → `JsonResponse`; `StorageNotConfigured`/erro → `HttpResponse(status=503)` ou 404. `item_raw`: `StreamingHttpResponse` do `get_object` (GLB/imagem). `item_download`: `redirect(services.presign_get(obj.object_key, obj.original_filename or obj.name))`. `atlas`: FeatureCollection unindo os GeoJSON dos itens `kind=="map"` públicos; cada feature com `properties.item = slug` e `properties.regiao`.
- [ ] **Step 4: Templates** `index.html` (estende `core/base.html`): hero + `#map` Leaflet (tiles Esri) carregando `atlas`, filtro de região, toggle de rotas, grade de cards com chip de tipo + controles de paginação preservando `request.GET`. `item.html`: cabeçalho + bloco condicional por `file.kind()` (Leaflet de `item_geo` com `fitBounds` / `<model-viewer src=item_raw>` / tabela de `item_table` / `<img src=item_raw>` em lightbox / card genérico) + metadados (`file.metadata`) + botão download.
- [ ] **Step 5: Rodar e ver passar** — mesmo comando → PASS.
- [ ] **Step 6: Commit** — `git commit -m "feat(acervo): app publico com atlas, pagina de item e paginacao"`

---

### Task 4: Curadoria na intranet

**Files:**
- Modify: `repositorio/views.py` (`file_update`; nova view `acervo_list`)
- Modify: `repositorio/urls.py` (rota `acervo/` → `acervo_list`)
- Modify: `repositorio/templates/repositorio/file_detail.html` (seção "Publicar no acervo")
- Create: `repositorio/templates/repositorio/acervo_list.html`
- Modify: `intranet/templates/intranet/content/index.html` (card "Acervo público")
- Test: `repositorio/tests.py` (`CuradoriaTests`)

**Interfaces:**
- Consumes: Task 1 (campos de publicação). 
- Produces: slug único no publish — helper `_unique_public_slug(titulo) -> str` em `repositorio/views.py`.

- [ ] **Step 1: Escrever testes que falham** (`CuradoriaTests`, logado como membro com `menu_repositorio`):

```python
def test_publicar_gera_slug_e_data():
    self.client.post(reverse("repositorio:file_update", args=[f.pk]),
                     {"name": f.name, "publico": "on", "titulo_publico": "Portos"})
    f.refresh_from_db()
    assert f.publico and f.public_slug == "portos" and f.publicado_em

def test_slug_colide_recebe_sufixo():
    # dois arquivos publicados com o mesmo titulo
    assert {a.public_slug, b.public_slug} == {"portos", "portos-2"}

def test_despublicar_mantem_slug():
    # publico=False some do acervo mas public_slug permanece
    ...

def test_acervo_list_so_publicos():
    r = self.client.get(reverse("repositorio:acervo_list"))
    assert pub in r.context["files"] and priv not in r.context["files"]
```

- [ ] **Step 2: Rodar e ver falhar** — `uv run python manage.py test repositorio.tests.CuradoriaTests -v 2`.
- [ ] **Step 3: Implementar.** Em `file_update`: ler `publico` (checkbox), `titulo_publico`, `descricao_publica`, `regiao`, `ordem`, `capa` (FILES); ao virar público sem `public_slug`, chamar `_unique_public_slug(display_title)` e setar `publicado_em=now()`. `acervo_list`: `RepoFile.objects.filter(publico=True).order_by("ordem","-publicado_em")`. Adicionar seção no `file_detail.html` e card no hub de conteúdo.
- [ ] **Step 4: Rodar e ver passar** — mesmo comando → PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(acervo): curadoria na intranet (publicar/despublicar + lista)"`

---

### Task 5: Botão "Acervo Digital" no topo

**Files:**
- Modify: `core/templates/core/base.html` (botão ~linha 69; e link equivalente no menu mobile se existir)
- Test: `acervo/tests.py` (`NavTests`)

- [ ] **Step 1: Teste que falha** — `NavTests.test_botao_acervo_no_topo`: GET em `reverse("home")`, `assertContains(r, "Acervo Digital")` e `assertContains(r, reverse("acervo:index"))`.
- [ ] **Step 2: Rodar e ver falhar** — `uv run python manage.py test acervo.tests.NavTests -v 2`.
- [ ] **Step 3: Implementar** — trocar texto "Galeria Digital" → "Acervo Digital" e `href="#"` → `href="{% url 'acervo:index' %}"` (botão desktop; replicar no mobile se houver o mesmo link).
- [ ] **Step 4: Rodar e ver passar** — mesmo comando → PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(acervo): botao Acervo Digital no cabecalho"`

---

### Task 6: Verificação fim-a-fim com dados reais (manual, read-only)

**Files:** nenhum (validação).

- [ ] **Step 1:** Rodar a suíte toda — `uv run python manage.py test acervo repositorio intranet -v 1` → tudo PASS.
- [ ] **Step 2:** Subir local apontando `DATABASE_URL` para o Postgres de prod (read-only; só GET), publicar 2–3 itens reais (1 KMZ de portos, 1 XLSX, o GLB) pela intranet e abrir `/acervo/` + a página de cada item; conferir mapa, tabela e 3D renderizando. (Ver memória `dev_local_banco_prod`.)
- [ ] **Step 3:** Screenshot do atlas e enviar ao usuário para validação visual antes do deploy.
