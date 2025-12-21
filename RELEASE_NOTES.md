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
