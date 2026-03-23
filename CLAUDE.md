# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

LAPOMED (Laboratório de Arqueologia da USP) institutional site — a digital gallery for archaeological projects with 3D model viewing support. Built with Django 5.2+ and Tailwind CSS.

## Development Commands

```bash
# Full dev environment (Tailwind watcher + Django server in parallel)
./dev.sh

# Django server only (port 4008)
uv run python manage.py runserver

# Tailwind CSS watch mode
cd lapomed/static_src && npm run dev

# Tailwind production build
cd lapomed/static_src && npm run build

# Migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Collect static files
uv run python manage.py collectstatic --noinput

# Docker
docker compose up --build
```

No test suite or linter is configured.

## Architecture

- **`lapomed_gallery/`** — Django project config (settings, urls, wsgi)
- **`core/`** — Main app: all models, views, templates, admin
- **`lapomed/`** — Tailwind CSS app (`static_src/` has Tailwind config, `static/css/dist/` has compiled output)
- **`config.py`** — Centralized env config (SECRET_KEY, DEBUG, DATABASE_URL). Auto-detects PostgreSQL (prod) vs SQLite (dev)

### Models (`core/models.py`)

Two groups: **gallery** (Slide, Project, Artifact, Collection, CollectionImage) and **about page** (AboutSection, TeamMember, Timeline, ResearchArea, Partnership). All models have `active` flag and most have `order` for admin-controlled sequencing. Artifact supports three content types: image, Sketchfab embed URL, or 3D model file (GLB/GLTF/USDZ).

### URL Routes (`core/urls.py`)

- `/` — home carousel
- `/projetos/` — project listing with search
- `/projetos/<slug>/` — project detail with artifacts
- `/quem-somos/` — about page (team, timeline, research areas, partnerships)
- `/admin/` — Jazzmin-themed admin panel

### CSS Pipeline

Tailwind 3 source at `lapomed/static_src/src/styles.css` compiles to `lapomed/static/css/dist/styles.css`. Plugins: Flowbite and DaisyUI. Templates load via `{% load tailwind_tags %}` and `{% tailwind_css %}`.

Custom Tailwind config: `lapomed-gold` (#f0c300) color, Cinzel (serif) and Lato (sans-serif) fonts.

### Docker Build

Multi-stage: Node 20 builds Tailwind CSS, then Python 3.13 stage installs deps with UV and runs the app. `entrypoint.sh` runs migrations, collectstatic, then Gunicorn (prod) or runserver (DEBUG).

## Conventions

- Python deps: **UV** (not pip) — `uv run python manage.py ...`
- Node deps: **NPM** — config in `lapomed/static_src/package.json`
- Port: **4008**
- Language: **pt-br**, Timezone: **America/Sao_Paulo**
- Deploy target: **Railway** (config in `railway.json`)
- Production env vars: `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`
- Static files served via **WhiteNoise** middleware in production
