# Release Notes - v1.2.0 (PostgreSQL & Deploy Readiness)
**Data: 21 de Janeiro de 2026**

## Visão Geral
Esta atualização prepara o sistema para deploy em ambientes como Railway, introduzindo suporte a PostgreSQL, variáveis de ambiente centralizadas e automação via entrypoint script.

## Funcionalidades Implementadas

### 1. Suporte a PostgreSQL e Variáveis de Ambiente
- **Configuração Híbrida**: O sistema agora detecta automaticamente se deve usar PostgreSQL (via `DATABASE_URL`) ou SQLite (fallback local).
- **Centralização com `config.py`**: Todas as variáveis sensíveis (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) são agora gerenciadas via variáveis de ambiente com valores default seguros.
- **Limpeza no `settings.py`**: Remoção de configurações hardcoded e duplicatas, tornando o arquivo mais limpo e modular.

### 2. Automação de Deploy
- **Entrypoint Script**: Criado `entrypoint.sh` que gerencia migrações, coleta de arquivos estáticos e escolhe entre Gunicorn (produção) ou runserver (desenvolvimento) de forma inteligente.
- **Compatibilidade com Railway/PaaS**: Ajuste no `Dockerfile` para respeitar a variável `PORT` dinâmica e uso de `ENTRYPOINT`.

### 3. Dependências e Segurança
- **Database Driver**: Inclusão de `psycopg2-binary` no `pyproject.toml`.
- **Hosts Dinâmicos**: `ALLOWED_HOSTS` agora aceita uma lista separada por vírgulas via ambiente.

---

# Release Notes - v1.1.0 (Dockerization & Infrastructure)
**Data: 21 de Janeiro de 2026**

## Visão Geral
Esta atualização foca na modernização da infraestrutura do projeto, garantindo um ambiente de desenvolvimento isolado, reprodutível e performático através da Dockerização e migração para o gerenciador de pacotes `uv`.

## Funcionalidades Implementadas

### 1. Dockerização Completa (BMAD-METHOD)
- **Dockerfile Multi-stage**: Separação do build de frontend (Node.js/Tailwind) e backend (Python/Django) para reduzir o tamanho da imagem final.
- **Docker Compose**: Orquestração simplificada com persistência de dados local (PVC-like) para `db.sqlite3` e pasta `media`.
- **Configuração de Porta**: Sistema padronizado para rodar na porta **4008** (Interno e Externo).
- **Script de Automação**: Criação do `docker-run.sh` para facilitar o build, migração e inicialização rápida do ambiente.

### 2. Gestão de Dependências Python com `uv`
- **Migração para UV**: Substituição de ambientes virtuais manuais pelo `uv`, garantindo builds determinísticos via `uv.lock` e `pyproject.toml`.
- **Velocidade**: Ganho significativo de performance na instalação de dependências e gerenciamento de pacotes.

### 3. Ajustes de Infraestrutura e Segurança
- **.dockerignore**: Implementado para manter a imagem limpa e segura (removendo arquivos sensíveis e desnecessários).
- **Configuração de Ambiente**: Preparação para uso de variáveis de ambiente no container.

## Tecnologias Atualizadas
- **Container**: Docker 20.x+ / Docker Compose
- **Python Manager**: `uv` (Astral)
- **Runtime**: Python 3.13-slim

---

# Release Notes - v1.0.0 (Initial Release)

## Visão Geral
Este é o primeiro commit do projeto **LAPOMED Galeria Digital**, um site institucional com foco em exibição de projetos arqueológicos e galeria de imagens interativa. O projeto foi desenvolvido utilizando Django, Tailwind CSS e Flowbite.

## Funcionalidades Implementadas

### 1. Interface e Design
- **Header Transparente e Responsivo**: Menu superior fixo (`60px`), semi-transparente com efeito `backdrop-blur` e tipografia padronizada.
- **Carrossel Fullscreen Cinematográfico**: 
  - Efeito "Ken Burns" (zoom suave) nas imagens de fundo.
  - Overlay de texto estático com tipografia premium (`Abril Fatface`).
  - Navegação por indicadores minimalistas.
  - Ajuste dinâmico de altura (`100vh`) garantindo visibilidade do footer sem rolagem desnecessária.
- **Design System Centralizado**: Estilos globais definidos no `styles.css` utilizando Tailwind CSS v3 e diretivas `@layer components` para fácil manutenção.

### 2. Estrutura Backend (Django)
- **Apps Core**: 
  - `home`: Página inicial com carrossel dinâmico gerenciável via Admin.
  - `projetos`: Listagem e detalhe de projetos.
  - `blog`: Estrutura base para posts (se aplicável).
- **Admin Otimizado**: Interface administrativa com `Jazzmin` para melhor experiência de gestão de conteúdo.
- **Gestão de Mídia**: Configuração completa para upload e exibição de imagens de projetos e slides.

### 3. Ajustes de Performance e Correções
- Unificação de tags de template Django para evitar `TemplateSyntaxError`.
- Otimização do carregamento de assets estáticos com `django-tailwind`.
- Correção de layout flexível (`flex-col`) para garantir que o footer permaneça na base da tela ("sticky footer") quando necessário.

## Tecnologias Utilizadas
- **Backend**: Python 3.10+, Django 5.x
- **Frontend**: HTML5, Tailwind CSS v3, Flowbite JS
- **Banco de Dados**: SQLite (padrão Django para dev)
- **Gerenciamento de Pacotes**: `uv` (Python), `npm` (Node.js)

## Próximos Passos
- Implementação de testes automatizados.
- Configuração de ambiente de produção.
- Expansão da seção de "Sobre" e "Contato".
