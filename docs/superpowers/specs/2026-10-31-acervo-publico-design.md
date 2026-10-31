# Acervo Digital Público — Design

**Data:** 2026-10-31
**Branch:** `feat/acervo-publico`
**Status:** aprovado em brainstorm; aguardando revisão do spec

## Objetivo

Transformar os arquivos do **Repositório de Arquivos** (hoje interno, na intranet) em um
**acervo público navegável** no site, com visualização por tipo de arquivo. O conteúdo real é
um atlas arqueológico: ~90% são dados geográficos de portos antigos do Mediterrâneo
(KML/KMZ = pontos e rotas), mais planilhas (XLSX), 1 modelo 3D (GLB) e imagens.

Inventário atual (56 arquivos, prod): 18 `.kml`, 18 `.kmz`, 18 `.xlsx`, 1 `.glb`, 1 `.jpg`,
em 3 pastas ("Portos do Mediterrâneo KMZ", "Arquivos Gerais KMZ", "Modelos3D").

## Decisões tomadas (brainstorm)

1. **Centro de gravidade:** mapa-atlas (todos os itens geográficos em um mapa), + grade de itens.
2. **Visibilidade:** curadoria **por item** — nada é público até ser marcado na intranet.
3. **Item:** **página dedicada** (`/acervo/item/<slug>/`), boa para compartilhar e para SEO.
4. **XLSX:** **preview da tabela** (primeiras linhas) + botão de download.
5. **Visualizadores:** Mapa (KML/KMZ), 3D (GLB, via `model-viewer` já usado nos tours),
   Planilha (XLSX), Imagem (lightbox). Outros tipos → cartão com download.

## Princípios de segurança

- O bucket MinIO/B2 **continua privado**. Nada de tornar objetos públicos no storage.
- Toda view pública exige `publico=True` **e** `status="ready"`; caso contrário **404**.
- O `object_key` nunca é exposto ao cliente. Downloads usam URL assinada temporária
  (`services.presign_get`, já existente). Arquivos renderizados (GLB, imagem) são servidos
  por **proxy** do Django (stream de bytes), evitando configurar CORS no bucket.
- Conversões (KML→GeoJSON, XLSX→linhas) rodam no servidor e são **cacheadas**.

## Modelo de dados

Acrescentar campos de publicação ao `repositorio.RepoFile` (sem modelo novo; o arquivo
é o próprio item do acervo). Migration apenas de adição de colunas com default — sem risco.

| Campo | Tipo | Default | Uso |
|---|---|---|---|
| `publico` | `BooleanField` | `False` | liga/desliga no acervo |
| `public_slug` | `SlugField(unique, null, blank)` | `None` | URL `/acervo/item/<slug>/`; gerado do título ao publicar |
| `titulo_publico` | `CharField(200, blank)` | `""` | título exibido (cai para `name` se vazio) |
| `descricao_publica` | `TextField(blank)` | `""` | descrição na página do item |
| `regiao` | `CharField(100, blank)` | `""` | rótulo de filtro no atlas (ex.: "Levante") |
| `ordem` | `PositiveIntegerField` | `0` | ordenação na grade |
| `capa` | `ImageField(upload_to="acervo/capas/", null, blank)` | `None` | miniatura opcional do card |
| `publicado_em` | `DateTimeField(null, blank)` | `None` | preenchido na 1ª publicação |

Método novo em `RepoFile`:
- `kind()` → `"map" | "3d" | "data" | "image" | "other"` a partir de `extension()`
  (`kml`/`kmz`→map, `glb`/`gltf`→3d, `xlsx`/`xls`/`csv`→data, `jpg`/`jpeg`/`png`/`webp`→image).
- `public_url()` → `reverse("acervo:item", args=[self.public_slug])`.

`public_slug` é gerado no momento de publicar (slug do título; se colidir, sufixa `-2`, `-3`…).

## App novo: `acervo`

App Django novo, **só leitura pública**, lendo os modelos de `repositorio`. Mantém o público
separado do interno. Adicionar a `INSTALLED_APPS` e incluir em `lapomed_gallery/urls.py`
em `path("acervo/", include("acervo.urls"))`.

### Rotas (`acervo/urls.py`, `app_name = "acervo"`)

| Rota | Nome | Função |
|---|---|---|
| `/acervo/` | `index` | landing: hero + mapa-atlas + grade de itens |
| `/acervo/item/<slug:slug>/` | `item` | página dedicada do item com o visualizador certo |
| `/acervo/item/<slug:slug>/geo.json` | `item_geo` | GeoJSON convertido do KML/KMZ (cacheado) |
| `/acervo/item/<slug:slug>/tabela.json` | `item_table` | linhas do XLSX (cacheado), para o preview |
| `/acervo/item/<slug:slug>/raw` | `item_raw` | proxy inline de bytes (GLB, imagem) |
| `/acervo/item/<slug:slug>/download` | `item_download` | redireciona para URL assinada (attachment) |
| `/acervo/atlas.geojson` | `atlas` | FeatureCollection com TODOS os itens geográficos públicos |

Todas resolvem o item por `get_object_or_404(RepoFile, public_slug=slug, publico=True, status="ready")`.
O atlas itera `RepoFile.objects.filter(publico=True, status="ready")` e inclui só os `kind()=="map"`.

### Conversores (`acervo/converters.py`)

- **`kml_to_geojson(bytes)`** / **`kmz_to_geojson(bytes)`**: parser próprio com `xml.etree`
  (+ `zipfile` para descompactar o `.kmz` e achar o `doc.kml`). Cobre `Placemark` com
  `Point`, `LineString`, `Polygon` e `MultiGeometry`, lendo `name` e `description`. Isso cobre
  "pontos de porto" e "sequências de rotas". **Sem dependência nova** (evita risco de libs KML pesadas).
- **`xlsx_to_rows(bytes, max_rows=200)`**: lê a 1ª aba com `openpyxl` (read-only), devolve
  `{columns: [...], rows: [[...]]}` limitado a `max_rows`. **Dependência nova: `openpyxl`.**

### Cache e acesso ao storage

- Novo helper em `repositorio/services.py`: **`fetch_bytes(key)`** → baixa o objeto para a
  memória do servidor via boto3 (`get_object`). Usado só pelo acervo público (os uploads
  continuam indo direto navegador→bucket, sem passar pelo Django).
- Conversões cacheadas com `django.core.cache`, chave = `f"acervo:{kind}:{object_key}:{updated_at}"`,
  timeout longo (ex.: 7 dias). Trocar o arquivo muda `updated_at` e invalida naturalmente.
- `item_raw` usa `StreamingHttpResponse` com o `Body` do `get_object` (não carrega tudo em memória).

## Telas / templates (`acervo/templates/acervo/`)

Design system do site: Cinzel (serifa), Lato, `lapomed-gold` (#f0c300), cards
`rounded-xl border border-gray-200`, mapa escuro.

### `index.html` — landing
- Hero escuro com título, subtítulo e 3 contadores (sítios no mapa / conjuntos de dados / modelos 3D).
- **Mapa-atlas** Leaflet (tiles **Esri Dark Gray**, sem API key — ver PR #21), carregando
  `/acervo/atlas.geojson`; marcadores dourados; popup com nome + link "Abrir item →";
  filtro por `regiao` (botões) e toggle "mostrar rotas" (liga/desliga as geometrias de linha).
- **Grade** de itens (cards) com chip de tipo (🗺️ Mapa / 🧊 3D / 📊 Dados / 🖼️ Imagem),
  título, subtítulo (ex.: "KMZ · 18 sítios"), capa opcional. Filtro de tipo client-side.

### `item.html` — página dedicada
Cabeçalho (chip de tipo + título + região) e, conforme `kind()`:
- **map**: Leaflet carregando `geo.json` do próprio item, com ajuste de `fitBounds`.
- **3d**: `<model-viewer>` apontando para `raw` (reusa config dos tours).
- **data**: tabela HTML montada de `tabela.json` (primeiras linhas) + aviso "prévia das N primeiras linhas".
- **image**: imagem de `raw` em lightbox.
- **other**: cartão com ícone genérico.
Sempre: bloco de **metadados** (`RepoFile.metadata` dinâmico) + botão **Baixar** (`download`).

## Curadoria na intranet

- **`repositorio/file_detail.html`**: acrescentar uma seção "Publicar no acervo" com
  `publico`, `titulo_publico`, `descricao_publica`, `regiao`, `ordem`, `capa`.
- **`repositorio/views.py` `file_update`**: passar a ler e salvar esses campos; ao marcar
  `publico=True` sem `public_slug`, gerar o slug e setar `publicado_em`.
- **Nova tela "Acervo" na intranet** (`repositorio/acervo_list`): lista só os itens com
  `publico=True`, com link "ver no site", reordenar (`ordem`) e despublicar rápido. Entra no
  hub "Conteúdo do site". Protegida por `@menu_required("repositorio")`.

## Botão do topo

`core/templates/core/base.html` (~linha 69): o botão **"Galeria Digital"** hoje tem
`href="#"` (link morto). Trocar o texto para **"Acervo Digital"** e o href para
`{% url 'acervo:index' %}`. (Os dois lugares — botão desktop e menu mobile, se houver.)

## Dependências novas

- `openpyxl` (ler XLSX) — via `uv add openpyxl`.
- Leaflet e `model-viewer`: **já presentes** no projeto.
- Conversão KML/KMZ: **código próprio** (sem lib nova).

## Testes (`acervo/tests.py`)

- Item não publicado → **404** em todas as rotas públicas; publicado + ready → **200**.
- `kind()` mapeia extensões corretamente.
- `kml_to_geojson` / `kmz_to_geojson` com fixtures pequenos (1 Point + 1 LineString) →
  FeatureCollection correta.
- `xlsx_to_rows` com fixture pequeno → colunas e linhas, respeitando `max_rows`.
- `item_download` redireciona (mock de `presign_get`), e só para item público.
- `atlas.geojson` inclui só itens `map` públicos e ignora não-públicos.
- Botão: `base.html` renderiza "Acervo Digital" apontando para `acervo:index`.
- Curadoria: `file_update` publica (gera slug, seta `publicado_em`) e despublica.

## Fora de escopo (v1)

- Busca textual no acervo; paginação (56 itens cabem numa grade).
- Edição de geometria/mapa pelo site; anotação colaborativa.
- Conversão de formatos exóticos além dos que existem hoje (cartão + download cobre o resto).
- Galerias aninhadas de imagem por item (uma imagem por arquivo nesta versão).

## Ordem de implementação (resumo p/ o plano)

1. Model: campos de publicação + `kind()`/`public_url()` + migration.
2. `services.fetch_bytes`; `acervo/converters.py` + `openpyxl`.
3. App `acervo`: urls, views (index, item, geo, tabela, raw, download, atlas), templates.
4. Curadoria na intranet (file_detail + file_update + tela "Acervo").
5. Botão "Acervo Digital" no base.html.
6. Testes.
