# Análise e Migração LAPOMED: Django → Drupal

**Data:** Fevereiro de 2026  
**Referência:** [FFLCH Drupal](https://github.com/fflch/drupal)  
**Status:** Documento de Planejamento

---

## 1. Resumo Executivo

Este documento apresenta a análise comparativa entre o sistema atual (Django) e a proposta de migração para Drupal, utilizando como base a plataforma da FFLCH/USP.

### Vantagens da Migração

| Aspecto | Django (Atual) | Drupal (Proposto) |
|---------|----------------|-------------------|
| **CMS Nativo** | Requer desenvolvimento custom | Interface administrativa completa |
| **Multisite** | Não suportado | Suporte nativo |
| **Ecossistema USP** | Isolado | Integração com FFLCH e outros sites USP |
| **Gestão de Conteúdo** | Código para cada feature | Contrib modules prontos |
| **Internacionalização** | Requer desenvolvimento | Nativo (pt-br, en) |

### Riscos e Considerações

- **Modelos 3D (GLB/GLTF):** Drupal não possui módulo nativo para Model Viewer; requer desenvolvimento custom
- **Point Clouds:** Requer integração do Potree como biblioteca externa
- **Curva de Aprendizado:** Equipe precisará se familiarizar com Drupal

### ✅ Simplificação: Tailwind CSS

**O Drupal suporta Tailwind CSS!** Isso significa que os templates podem ser migrados **praticamente 1:1** do Django para o Drupal, mantendo todas as classes Tailwind.

---

## 2. Mapeamento de Estruturas

### 2.1 Models Django → Content Types Drupal

| Django Model | Drupal Content Type | Módulos Recomendados |
|--------------|---------------------|----------------------|
| `Slide` | **Slide** (custom) ou Block Content | `views_slideshow`, `colorbox` |
| `Project` | **Projeto** (node) | `pathauto` (para slugs) |
| `Artifact` | **Artefato** (node) com referência a Projeto | `paragraphs`, `file_entity` |
| `Collection` | **Coleção** (node) + Entity Reference | `entity_reference` |
| `AboutSection` | **Página Básica** ou custom content type | Core |
| `TeamMember` | **Membro da Equipe** (node) | `field_group` |
| `Timeline` | **Marco Histórico** (node) | Views para ordenação |
| `ResearchArea` | **Área de Pesquisa** (node) | Core |
| `Partnership` | **Parceria** (node) | Core |

### 2.2 Campos por Content Type

#### Content Type: Projeto (`project`)

```yaml
fields:
  - field_name: title
    type: string
    drupal: title (core)
    
  - field_name: slug
    type: slug
    drupal: path_alias (pathauto)
    pattern: '/projetos/[node:title]'
    
  - field_name: description
    type: text_long
    drupal: body (core)
    
  - field_name: location
    type: string
    drupal: field_location (text)
    
  - field_name: cover_image
    type: image
    drupal: field_cover_image (image)
```

#### Content Type: Artefato (`artifact`)

```yaml
fields:
  - field_name: title
    type: string
    drupal: title (core)
    
  - field_name: project
    type: foreign_key
    drupal: field_project (entity_reference → project)
    
  - field_name: description
    type: text_long
    drupal: body (core)
    
  - field_name: image
    type: image
    drupal: field_artifact_image (image)
    
  - field_name: sketchfab_embed
    type: text_long
    drupal: field_sketchfab_embed (text_long)
    
  - field_name: model_file
    type: file (GLB/GLTF)
    drupal: field_model_3d (file)
    # NOTA: Requer módulo custom para renderização
    
  - field_name: annotations
    type: text_long
    drupal: field_annotations (text_long)
```

#### Content Type: Slide (`slide`)

```yaml
fields:
  - field_name: title
    type: string
    drupal: title (core)
    
  - field_name: subtitle
    type: string
    drupal: field_subtitle (text)
    
  - field_name: image
    type: image
    drupal: field_slide_image (image)
    
  - field_name: link
    type: url
    drupal: field_link (link)
    
  - field_name: order
    type: integer
    drupal: field_weight (integer)
    
  - field_name: active
    type: boolean
    drupal: status (core - published/unpublished)
```

---

## 3. Arquitetura Drupal Proposta

### 3.1 Estrutura de Diretórios

```
lapomed-drupal/
├── composer.json              # Dependências (baseado em FFLCH)
├── composer.lock
├── web/
│   ├── core/                  # Drupal Core
│   ├── modules/
│   │   ├── contrib/           # Módulos da comunidade
│   │   └── custom/
│   │       └── lapomed_core/  # Módulo custom LAPOMED
│   ├── themes/
│   │   ├── contrib/
│   │   └── custom/
│   │       └── lapomed/       # Tema custom LAPOMED
│   ├── profiles/
│   │   └── contrib/
│   │       └── lapomedprofile/ # Profile de instalação
│   └── sites/
│       └── default/
│           └── files/         # Uploads
├── drush/
├── patches/
└── docs/
```

### 3.2 Profile de Instalação (`lapomedprofile`)

Baseado no `fflchprofile`, criar um profile customizado:

**`lapomedprofile.info.yml`:**
```yaml
name: lapomedprofile
type: profile
description: 'Profile LAPOMED - Galeria Digital de Arqueologia'
version: VERSION
core_version_requirement: ^10 || ^11

install:
  # Core modules
  - block
  - block_content
  - ckeditor5
  - config
  - content_translation
  - datetime
  - editor
  - file
  - image
  - language
  - locale
  - media
  - menu_ui
  - node
  - options
  - path
  - taxonomy
  - views
  - views_ui
  
themes:
  - lapomed
  - claro  # Admin theme
```

---

## 4. Módulos Drupal Necessários

### 4.1 Módulos Contrib Essenciais

```json
{
  "require": {
    "drupal/core-recommended": "^10.0",
    "drupal/admin_toolbar": "^3.0",
    "drupal/pathauto": "^1.11",
    "drupal/metatag": "^2.0",
    "drupal/token": "^1.11",
    "drupal/paragraphs": "^1.15",
    "drupal/entity_reference_revisions": "^1.10",
    "drupal/views_slideshow": "^5.0",
    "drupal/colorbox": "^2.0",
    "drupal/field_group": "^3.4",
    "drupal/webform": "^6.2",
    "drupal/ckeditor5": "^1.0",
    "drupal/imce": "^3.0",
    "drupal/google_analytics": "^4.0",
    "drupal/redirect": "^1.8",
    "drupal/twig_tweak": "^3.2",
    "drupal/fontawesome": "^2.24"
  }
}
```

### 4.2 Módulo Custom: `lapomed_core`

Módulo para funcionalidades específicas do LAPOMED:

**`lapomed_core.info.yml`:**
```yaml
name: 'LAPOMED Core'
type: module
description: 'Funcionalidades core do LAPOMED'
core_version_requirement: ^10 || ^11
package: 'LAPOMED'
dependencies:
  - drupal:node
  - drupal:views
  - drupal:file
```

**Funcionalidades do módulo:**
1. **Model Viewer Integration** - Renderização de arquivos 3D (GLB/GLTF)
2. **Formatters customizados** - Para campos específicos
3. **Preprocess hooks** - Para o tema

---

## 5. Renderização de Modelos 3D e Point Clouds

O LAPOMED suporta dois tipos de visualização 3D:

| Tipo | Formato | Tecnologia | Uso |
|------|---------|------------|-----|
| **Meshes 3D** | GLB, GLTF, USDZ | Google Model Viewer | Artefatos, objetos texturizados |
| **Point Clouds** | LAS, LAZ, Potree | Potree Viewer | Sítios arqueológicos, escaneamentos LIDAR |

### 5.1 Google Model Viewer (GLB/USDZ)

Criar um **Field Formatter** custom para integrar o Google Model Viewer:

**`src/Plugin/Field/FieldFormatter/ModelViewerFormatter.php`:**
```php
<?php

namespace Drupal\lapomed_core\Plugin\Field\FieldFormatter;

use Drupal\Core\Field\FieldItemListInterface;
use Drupal\Core\Field\FormatterBase;
use Drupal\Core\Form\FormStateInterface;

/**
 * Plugin implementation of the 'model_viewer' formatter.
 *
 * @FieldFormatter(
 *   id = "model_viewer",
 *   label = @Translation("Model Viewer (3D)"),
 *   field_types = {
 *     "file"
 *   }
 * )
 */
class ModelViewerFormatter extends FormatterBase {

  public function viewElements(FieldItemListInterface $items, $langcode) {
    $elements = [];

    foreach ($items as $delta => $item) {
      $file = $item->entity;
      if ($file) {
        $elements[$delta] = [
          '#theme' => 'lapomed_model_viewer',
          '#file_url' => $file->createFileUrl(),
          '#alt' => $file->getFilename(),
          '#attached' => [
            'library' => ['lapomed_core/model_viewer'],
          ],
        ];
      }
    }

    return $elements;
  }
}
```

**Template `lapomed-model-viewer.html.twig`:**
```twig
<model-viewer
  src="{{ file_url }}"
  alt="{{ alt }}"
  auto-rotate
  camera-controls
  shadow-intensity="1"
  style="width: 100%; height: 500px;">
</model-viewer>
```

**Library `lapomed_core.libraries.yml`:**
```yaml
model_viewer:
  js:
    https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js: { type: external, attributes: { type: module } }
```

### 5.2 Potree Viewer (Point Clouds)

Para visualização de nuvens de pontos (escaneamentos LIDAR, fotogrametria), integrar o **Potree** (fork LAPOMED: https://github.com/lapomed/potree).

#### Arquitetura de Integração

```
web/
├── libraries/
│   └── potree/                    # Build do Potree
│       ├── build/
│       │   └── potree/
│       │       ├── potree.js
│       │       └── potree.css
│       └── libs/                  # Dependências (Three.js, etc)
└── sites/default/files/
    └── pointclouds/               # Dados convertidos
        └── projeto-x/
            └── metadata.json
```

#### Campo Drupal para Point Clouds

Adicionar ao Content Type **Artefato**:

```yaml
fields:
  - field_name: field_pointcloud_path
    type: string
    drupal: field_pointcloud_path (text)
    description: 'Caminho relativo para o diretório do point cloud convertido'
    example: 'pointclouds/sitio-puca-pucara'
```

#### Field Formatter: Potree Viewer

**`src/Plugin/Field/FieldFormatter/PotreeViewerFormatter.php`:**
```php
<?php

namespace Drupal\lapomed_core\Plugin\Field\FieldFormatter;

use Drupal\Core\Field\FieldItemListInterface;
use Drupal\Core\Field\FormatterBase;

/**
 * Plugin implementation of the 'potree_viewer' formatter.
 *
 * @FieldFormatter(
 *   id = "potree_viewer",
 *   label = @Translation("Potree Viewer (Point Cloud)"),
 *   field_types = {
 *     "string"
 *   }
 * )
 */
class PotreeViewerFormatter extends FormatterBase {

  public function viewElements(FieldItemListInterface $items, $langcode) {
    $elements = [];

    foreach ($items as $delta => $item) {
      $path = $item->value;
      if ($path) {
        $elements[$delta] = [
          '#theme' => 'lapomed_potree_viewer',
          '#pointcloud_path' => '/sites/default/files/' . $path,
          '#viewer_id' => 'potree-viewer-' . $delta,
          '#attached' => [
            'library' => ['lapomed_core/potree'],
          ],
        ];
      }
    }

    return $elements;
  }
}
```

#### Template Potree

**`templates/lapomed-potree-viewer.html.twig`:**
```twig
<div id="{{ viewer_id }}" class="potree-container" style="width: 100%; height: 600px; position: relative;">
  <script>
    (function() {
      window.addEventListener('load', function() {
        const viewer = new Potree.Viewer(document.getElementById('{{ viewer_id }}'));
        viewer.setEDLEnabled(true);
        viewer.setFOV(60);
        viewer.setPointBudget(1_000_000);
        viewer.setBackground('gradient');
        
        Potree.loadPointCloud('{{ pointcloud_path }}/metadata.json', 'pointcloud', function(e) {
          viewer.scene.addPointCloud(e.pointcloud);
          viewer.fitToScreen();
        });
      });
    })();
  </script>
</div>
```

#### Library Definition

**`lapomed_core.libraries.yml`** (adicionar):
```yaml
potree:
  version: 1.8.0
  css:
    theme:
      /libraries/potree/build/potree/potree.css: {}
  js:
    /libraries/potree/libs/jquery/jquery-3.1.1.min.js: {}
    /libraries/potree/libs/spectrum/spectrum.js: {}
    /libraries/potree/libs/jquery-ui/jquery-ui.min.js: {}
    /libraries/potree/libs/three.js/build/three.min.js: {}
    /libraries/potree/libs/other/BinaryHeap.js: {}
    /libraries/potree/libs/tween/tween.min.js: {}
    /libraries/potree/libs/d3/d3.js: {}
    /libraries/potree/libs/proj4/proj4.js: {}
    /libraries/potree/libs/openlayers3/ol.js: {}
    /libraries/potree/libs/i18next/i18next.js: {}
    /libraries/potree/libs/jstree/jstree.js: {}
    /libraries/potree/build/potree/potree.js: {}
  dependencies:
    - core/drupalSettings
```

#### Conversão de Point Clouds

Antes de fazer upload, os dados devem ser convertidos com **PotreeConverter**:

```bash
# Instalar PotreeConverter
# https://github.com/potree/PotreeConverter/releases

# Converter arquivo LAS/LAZ para formato Potree
./PotreeConverter /path/to/scan.las -o /path/to/output --generate-page

# Estrutura gerada:
output/
├── metadata.json
├── octree/
│   └── r/
│       └── ... (dados hierárquicos)
└── hierarchy.bin
```

#### Workflow de Upload

1. Converter point cloud localmente com PotreeConverter
2. Fazer upload do diretório convertido para `/sites/default/files/pointclouds/`
3. No admin Drupal, preencher o campo `field_pointcloud_path` com o caminho relativo

**Nota:** Para facilitar, pode-se criar um módulo de upload que aceite arquivos LAS/LAZ e converta automaticamente (requer PotreeConverter no servidor).

---

## 6. Tema LAPOMED - Tailwind CSS no Drupal

**✅ SIMPLIFICAÇÃO:** O Drupal suporta Tailwind CSS! Os templates podem ser migrados **praticamente 1:1** do Django, mantendo todas as classes Tailwind, Flowbite e DaisyUI.

### 6.1 Estrutura do Tema (com Tailwind)

```
themes/custom/lapomed/
├── lapomed.info.yml
├── lapomed.libraries.yml
├── lapomed.theme               # Preprocess hooks
├── static_src/                  # 👈 IGUAL AO DJANGO!
│   ├── package.json
│   ├── package-lock.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       └── styles.css          # @tailwind directives + custom
├── css/
│   └── dist/
│       └── styles.css          # Build compilado
├── js/
│   ├── carousel.js
│   ├── tabs.js
│   ├── modal.js
│   └── scroll-spy.js
├── templates/
│   ├── layout/
│   │   ├── page.html.twig
│   │   └── page--front.html.twig
│   ├── navigation/
│   │   ├── menu--main.html.twig
│   │   └── menu--mobile.html.twig
│   ├── node/
│   │   ├── node--project--teaser.html.twig
│   │   ├── node--project--full.html.twig
│   │   ├── node--artifact.html.twig
│   │   ├── node--slide.html.twig
│   │   └── node--team-member.html.twig
│   ├── views/
│   │   ├── views-view--carousel.html.twig
│   │   ├── views-view--projects-grid.html.twig
│   │   └── views-view--collections.html.twig
│   └── field/
│       ├── field--field-model-3d.html.twig
│       └── field--field-pointcloud.html.twig
├── images/
├── logo.svg
└── screenshot.png
```

### 6.2 Configuração Tailwind (Copiar do Django)

**`static_src/package.json`:**
```json
{
  "name": "lapomed-drupal",
  "version": "1.0.0",
  "scripts": {
    "dev": "tailwindcss -i ./src/styles.css -o ../css/dist/styles.css --watch",
    "build": "tailwindcss -i ./src/styles.css -o ../css/dist/styles.css --minify"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.17",
    "daisyui": "^4.12.10",
    "flowbite": "^3.1.2",
    "postcss": "^8.4.35",
    "tailwindcss": "^3.4.1"
  }
}
```

**`static_src/tailwind.config.js`:**
```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Templates Drupal (Twig)
    "../templates/**/*.twig",
    "../templates/**/*.html.twig",
    // Módulos custom
    "../../modules/custom/**/*.twig",
    // JavaScript
    "../js/**/*.js",
    // Flowbite
    "./node_modules/flowbite/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ["Cinzel", "serif"],
        sans: ["Lato", "sans-serif"],
      },
      colors: {
        "lapomed-gold": "#f0c300",
      },
      borderColor: {
        DEFAULT: "#3a414f",
      },
    },
  },
  plugins: [
    require("flowbite/plugin"),
    require("daisyui"),
  ],
};
```

**`static_src/src/styles.css`:** (copiar do Django)
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-white text-gray-900;
  }
  body.no-scroll {
    @apply overflow-hidden h-screen flex flex-col !important;
  }
  body.no-scroll main {
    @apply flex-1 w-full relative overflow-hidden;
  }
}

@layer components {
  /* --- HEADER & NAVIGATION --- */
  .main-nav {
    @apply fixed top-0 inset-x-0 z-50 bg-white/70 backdrop-blur-md transition-all duration-300 !important;
    height: 60px !important;
  }

  .nav-link {
    @apply flex items-center px-5 text-[13px] font-extrabold uppercase tracking-widest text-[#383838] no-underline relative transition-all duration-300;
    height: 60px !important;
  }

  .nav-link::after {
    content: "";
    @apply absolute bottom-0 left-5 right-5 h-[2px] bg-black scale-x-0 transition-transform duration-300 ease-in-out;
  }

  .nav-link:hover::after {
    @apply scale-x-100;
  }

  /* --- HOME CAROUSEL --- */
  .carousel-zoom-bg {
    animation: kenBurns 40s linear infinite alternate;
    transform-origin: center;
  }

  @keyframes kenBurns {
    0% { transform: scale(1); }
    100% { transform: scale(1.1); }
  }

  .animate-fade-in-fast {
    animation: fadeInFast 0.5s ease-out forwards;
  }

  @keyframes fadeInFast {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .indicator-bar {
    @apply w-12 h-1 bg-white cursor-pointer transition-all duration-500 !important;
  }
}
```

### 6.3 Migração de Templates: Django → Drupal Twig

A sintaxe é **muito similar**. Principais diferenças:

| Django | Drupal Twig | Exemplo |
|--------|-------------|----------|
| `{% url 'name' %}` | `{{ path('entity.node.canonical', {'node': node.id}) }}` | Links |
| `{% for item in items %}` | `{% for item in items %}` | ✅ Igual |
| `{{ var\|filter }}` | `{{ var\|filter }}` | ✅ Igual |
| `{% load static %}` | Não necessário | Estáticos |
| `{% static 'path' %}` | `{{ base_path ~ directory }}/path` | Arquivos |
| `{% extends 'base.html' %}` | `{% extends "@lapomed/layout/page.html.twig" %}` | Herança |

#### Exemplo: Card de Projeto

**Django (atual):**
```html
{% for project in projects %}
<a href="{% url 'project_detail' project.slug %}" 
   class="relative group block overflow-hidden h-72 bg-[#0b0b0b]">
  <img src="{{ project.cover_image.url }}" 
       alt="{{ project.title }}"
       class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"/>
  <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent"></div>
  <div class="absolute bottom-0 left-0 p-8 w-full">
    <span class="text-xs text-white bg-black/50 px-2 py-1 rounded-sm uppercase tracking-widest mb-2 inline-block">
      {{ project.location }}
    </span>
    <h3 class="text-2xl font-serif text-white tracking-wide">{{ project.title }}</h3>
  </div>
</a>
{% endfor %}
```

**Drupal Twig (migrado):**
```twig
{% for item in rows %}
  {% set node = item.content['#node'] %}
  <a href="{{ path('entity.node.canonical', {'node': node.id}) }}" 
     class="relative group block overflow-hidden h-72 bg-[#0b0b0b]">
    <img src="{{ file_url(node.field_cover_image.entity.fileuri) }}" 
         alt="{{ node.title.value }}"
         class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"/>
    <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent"></div>
    <div class="absolute bottom-0 left-0 p-8 w-full">
      <span class="text-xs text-white bg-black/50 px-2 py-1 rounded-sm uppercase tracking-widest mb-2 inline-block">
        {{ node.field_location.value }}
      </span>
      <h3 class="text-2xl font-serif text-white tracking-wide">{{ node.title.value }}</h3>
    </div>
  </a>
{% endfor %}
```

**Observe:** As classes Tailwind são **100% iguais**!

### 6.4 Library Definition (com Tailwind)

**`lapomed.libraries.yml`:**
```yaml
global:
  version: 1.0.0
  css:
    theme:
      css/dist/styles.css: {}   # Build do Tailwind
  js:
    js/carousel.js: {}
    js/tabs.js: {}
    js/modal.js: {}
    js/scroll-spy.js: {}
  dependencies:
    - core/drupal

flowbite:
  version: 3.1.2
  js:
    https://cdn.jsdelivr.net/npm/flowbite@3.1.2/dist/flowbite.min.js: { type: external }

model-viewer:
  version: 3.4.0
  js:
    https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js: { type: external, attributes: { type: module } }

fonts:
  version: 1.0.0
  css:
    base:
      'https://fonts.googleapis.com/css2?family=Abril+Fatface&family=Cinzel:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700;800;900&family=Lato:wght@300;400;700&family=Lora:ital,wght@0,400;0,700;1,400&display=swap': { type: external }
```

### 6.5 Configuração do Tema

**`lapomed.info.yml`:**
```yaml
name: LAPOMED
type: theme
description: 'Tema LAPOMED - Galeria Digital de Arqueologia USP (Tailwind CSS)'
core_version_requirement: ^10 || ^11
base theme: false
screenshot: screenshot.png

libraries:
  - lapomed/global
  - lapomed/flowbite
  - lapomed/fonts

libraries-override:
  classy/base: false

regions:
  header: 'Header'
  mobile_menu: 'Mobile Menu Drawer'
  primary_menu: 'Primary Menu'
  content: 'Content'
  footer: 'Footer'
```

### 6.6 Comandos de Desenvolvimento

```bash
# Entrar no diretório do tema
cd web/themes/custom/lapomed/static_src

# Instalar dependências
npm install

# Watch mode (desenvolvimento)
npm run dev

# Build para produção
npm run build
```

---

## 7. Migração de Dados

### 7.1 Estratégia de Migração

1. **Exportar dados do Django** via management command ou API
2. **Transformar para formato Drupal** (CSV ou JSON)
3. **Importar via Migrate API** ou módulo `csv_importer`

### 7.2 Script de Exportação Django

Criar em `core/management/commands/export_to_drupal.py`:

```python
import json
from django.core.management.base import BaseCommand
from core.models import Project, Artifact, Slide, TeamMember, AboutSection

class Command(BaseCommand):
    help = 'Exporta dados para migração Drupal'

    def handle(self, *args, **options):
        data = {
            'projects': list(Project.objects.values()),
            'artifacts': list(Artifact.objects.values()),
            'slides': list(Slide.objects.values()),
            'team_members': list(TeamMember.objects.values()),
            'about_sections': list(AboutSection.objects.values()),
        }
        
        with open('export_drupal.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.stdout.write(self.style.SUCCESS('Dados exportados com sucesso!'))
```

### 7.3 Configuração Migrate Drupal

**`migrations/migrate_plus.migration.lapomed_projects.yml`:**
```yaml
id: lapomed_projects
label: 'Importar Projetos do LAPOMED Django'
migration_group: lapomed

source:
  plugin: url
  data_fetcher_plugin: file
  data_parser_plugin: json
  urls: 'private://migrations/export_drupal.json'
  item_selector: projects
  fields:
    - name: id
      selector: id
    - name: title
      selector: title
    - name: slug
      selector: slug
    - name: description
      selector: description
    - name: location
      selector: location
    - name: cover_image
      selector: cover_image
  ids:
    id:
      type: integer

process:
  type:
    plugin: default_value
    default_value: project
  title: title
  body/value: description
  body/format:
    plugin: default_value
    default_value: full_html
  field_location: location
  path/alias:
    plugin: concat
    source:
      - constants/slash
      - 'projetos'
      - constants/slash
      - slug
    
destination:
  plugin: entity:node
  default_bundle: project
```

---

## 8. Cronograma de Migração

### Fase 1: Preparação (1 semana)
- [ ] Setup do ambiente Drupal local (composer install)
- [ ] Criação do profile `lapomedprofile`
- [ ] Instalação de módulos contrib
- [ ] Definição dos Content Types e campos

### Fase 2: Tema com Tailwind (2 semanas) ⭐ SIMPLIFICADO
- [ ] Copiar `static_src/` do Django para o tema Drupal
- [ ] Ajustar `tailwind.config.js` para paths Twig
- [ ] Migrar templates (Django → Twig) - **classes CSS são iguais!**
- [ ] Testar Flowbite e DaisyUI
- [ ] Ajustar JavaScript (carousel, modal, tabs)

### Fase 3: Módulo Custom (2 semanas)
- [ ] Criar módulo `lapomed_core`
- [ ] Field Formatter: Model Viewer (GLB/USDZ)
- [ ] Field Formatter: Potree (Point Clouds)
- [ ] Integrar bibliotecas JS

### Fase 4: Migração de Dados (1 semana)
- [ ] Script de exportação Django (JSON)
- [ ] Configuração do Migrate API
- [ ] Migração de arquivos (imagens, modelos 3D, point clouds)
- [ ] Teste de importação

### Fase 5: Homologação (1 semana)
- [ ] Testes funcionais
- [ ] Comparação visual Django vs Drupal
- [ ] Validação com stakeholders
- [ ] Correção de bugs

### Fase 6: Deploy (1 semana)
- [ ] Configuração de servidor
- [ ] Deploy em produção
- [ ] Monitoramento
- [ ] Documentação final

**Total Estimado: 8 semanas** (↓ 2 semanas com Tailwind!)

---

## 9. Comandos de Referência

### Instalação do Drupal (baseado em FFLCH)

```bash
# Clonar base FFLCH (ou criar do zero)
git clone git@github.com:lapomed/drupal.git
cd drupal

# Instalar dependências
composer install

# Instalar com SQLite (desenvolvimento)
./vendor/bin/drush site-install lapomedprofile \
    --db-url=sqlite://sites/default/files/.ht.sqlite \
    --site-name="LAPOMED" \
    --site-mail="lapomed@usp.br" \
    --account-name="admin" \
    --account-pass="admin" \
    --account-mail="admin@usp.br" --yes

# Instalar com MySQL (produção)
./vendor/bin/drush site-install lapomedprofile \
    --db-url=mysql://user:pass@localhost/lapomed \
    --site-name="LAPOMED" \
    --site-mail="lapomed@usp.br" \
    --account-name="admin" \
    --account-pass="SENHA_SEGURA" \
    --account-mail="admin@usp.br" --yes

# Servidor de desenvolvimento
./vendor/bin/drush rs 127.0.0.1:4008

# Limpar cache
./vendor/bin/drush cr

# Exportar configurações
./vendor/bin/drush config-export

# Importar configurações
./vendor/bin/drush config-import

# Rodar migrações
./vendor/bin/drush migrate:import lapomed_projects
./vendor/bin/drush migrate:import lapomed_artifacts
```

---

## 10. Referências

- **FFLCH Drupal:** https://github.com/fflch/drupal
- **Drupal Migrate API:** https://www.drupal.org/docs/drupal-apis/migrate-api
- **Google Model Viewer:** https://modelviewer.dev/
- **Potree (LAPOMED fork):** https://github.com/lapomed/potree
- **PotreeConverter:** https://github.com/potree/PotreeConverter
- **Drupal 10 Docs:** https://www.drupal.org/docs/10

---

## Apêndice A: Checklist de Funcionalidades

| Funcionalidade Django | Status Drupal | Observação |
|-----------------------|---------------|------------|
| Carousel de Slides | ⚠️ Requer `views_slideshow` | Configurar View |
| Listagem de Projetos | ✅ View nativa | Fácil |
| Detalhe de Projeto | ✅ Node template | Fácil |
| Busca de Projetos | ✅ Search API | Fácil |
| Artefatos com Imagem | ✅ Campo Image | Fácil |
| Artefatos Sketchfab | ✅ Campo Text Long | Fácil |
| Artefatos GLB/GLTF | ⚠️ Custom Formatter | Google Model Viewer |
| Point Clouds (LAS/LAZ) | ⚠️ Custom Formatter | Potree Viewer |
| Página Quem Somos | ✅ Content Type | Fácil |
| Equipe | ✅ Content Type + View | Fácil |
| Linha do Tempo | ✅ Content Type + View | Ordenar por ano |
| Parcerias | ✅ Content Type + View | Fácil |
| Admin Jazzmin | ✅ Admin Toolbar + Gin | Alternativa melhor |

---

**Documento preparado por:** WARP Agent  
**Última atualização:** Fevereiro de 2026
