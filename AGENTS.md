# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Descrição do Projeto

Site institucional do LAPOMED (Laboratório de Arqueologia da USP) - uma galeria digital para exibição de projetos arqueológicos com suporte a visualização de modelos 3D.

## Comandos de Desenvolvimento

```bash
# Desenvolvimento completo (Tailwind + Django em paralelo)
./dev.sh

# Servidor Django manualmente
uv run python manage.py runserver

# Tailwind CSS watch (recompila ao alterar)
cd lapomed/static_src && npm run dev

# Build do Tailwind para produção
cd lapomed/static_src && npm run build

# Migrações do Django
uv run python manage.py makemigrations
uv run python manage.py migrate

# Coletar arquivos estáticos
uv run python manage.py collectstatic --noinput

# Docker (inclui build do Tailwind)
docker compose up --build
```

## Arquitetura do Projeto

### Estrutura Django

- **`lapomed_gallery/`** - Módulo de configuração principal do Django (settings, urls, wsgi)
- **`core/`** - App principal com todos os models, views, templates e admin
- **`lapomed/`** - App do Tailwind (contém `static_src/` com configuração do Tailwind)
- **`config.py`** - Configurações centralizadas de ambiente (SECRET_KEY, DEBUG, DATABASE_URL)

### Models Principais (`core/models.py`)

- **Slide** - Slides do carousel da home
- **Project** - Projetos arqueológicos (com slug para URL)
- **Artifact** - Artefatos de projetos (suporta imagem, embed Sketchfab ou modelo 3D GLB/GLTF)
- **Collection** - Coleções de projetos
- **AboutSection, TeamMember, Timeline, ResearchArea, Partnership** - Conteúdo da página "Quem Somos"

### URLs e Views

- `/` → home (carousel de slides)
- `/projetos/` → listagem de projetos (com busca)
- `/projetos/<slug>/` → detalhe do projeto com artefatos
- `/quem-somos/` → página institucional
- `/admin/` → painel administrativo (Jazzmin)

### Frontend Stack

- **Tailwind CSS** v3 com plugins **Flowbite** e **DaisyUI**
- **Google Model Viewer** para renderização de modelos 3D nativos
- Templates em `core/templates/core/` (herdam de `base.html`)
- Configuração Tailwind em `lapomed/static_src/tailwind.config.js`

### Banco de Dados

- **Desenvolvimento**: SQLite (`db.sqlite3`)
- **Produção**: PostgreSQL via `DATABASE_URL`
- A detecção é automática no `config.py`

## Convenções

- Gerenciador Python: **UV** (não usar pip diretamente)
- Gerenciador Node: **NPM** (não usar yarn)
- Porta padrão de desenvolvimento: **4008**
- Templates usam `{% load static tailwind_tags %}` para carregar CSS
- Cor customizada: `lapomed-gold` (#f0c300)
- Fontes: Cinzel (serif) e Lato (sans-serif)

## Deploy

- Plataforma alvo: **Railway**
- `entrypoint.sh` gerencia migrações, collectstatic e escolhe entre Gunicorn/runserver
- Variáveis de ambiente necessárias em produção: `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`
