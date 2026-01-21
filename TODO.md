# TODO - Ajustes Visuais e Funcionais

## Fase 1: Ajustes de Renderização e Brand (Agosto/2024)
- [x] Corrigir renderização de tags HTML na intro do "Quem Somos" (`about.html`) <!-- id: 0 -->
- [x] Substituir logo textual por imagem no Header (`base.html`) <!-- id: 1 -->
- [x] Inserir logo no Footer alinhado às redes sociais (`base.html`) <!-- id: 2 -->

## Fase 2: Polimento UI/UX
- [ ] Validar responsividade do novo logo no mobile <!-- id: 3 -->
- [ ] Verificar contraste do logo no footer <!-- id: 4 -->

## Fase 3: Dockerização do Sistema (BMAD-METHOD)
- [x] **Fase 3.1: Preparação Python (UV)** <!-- id: 5 -->
    - [x] Inicializar `uv init` e criar `pyproject.toml`
    - [x] Mapear e instalar dependências atuais
- [x] **Fase 3.2: Dockerfile Multi-stage** <!-- id: 6 -->
    - [x] Criar Build stage para Tailwind (Node)
    - [x] Criar Runtime stage para Django (Python)
- [x] **Fase 3.3: Orquestração (Docker Compose)** <!-- id: 7 -->
    - [x] Criar `docker-compose.yml`
    - [x] Configurar volumes para persistência (SQLite/Media)
- [x] **Fase 3.4: Homologação** <!-- id: 8 -->
    - [x] Testar build e execução completa
