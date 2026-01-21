# Feature: Refinamento da Página "Quem Somos"

## Objetivo
Refinar a interface da página "Quem Somos" (About) para alinhar perfeitamente com a estética do site CyArk, garantindo espaçamentos precisos, carregamento dinâmico via Django Admin e correções de layout.

## Fases de Implementação

- [x] **Fase 1: Estrutura e Estética Hero**
    - [x] Título "QUEM SOMOS" com 7.5rem.
    - [x] Espaçamento de 10vh entre Título e Texto de Missão.
    - [x] Ícone de scroll (seta) branco animado e posicionado na base.
    - [x] Overlay de gradiente para legibilidade sobre a imagem de fundo.

- [x] **Fase 2: Sub-Navegação Sticky**
    - [x] Implementação da barra de menu secundária (#ededed).
    - [x] Links: Mission, About, People, History.
    - [x] Estado ativo com borda âmbar (#ffcc00).

- [x] **Fase 3: Tríade Institucional (Missão, Visão e Valores)**
    - [x] Grade de 3 colunas (grid-cols-3) para os boxes.
    - [x] Ícones estilizados e boxes minimalistas.
    - [x] Carregamento dinâmico do banco de dados (AboutSection).

- [x] **Fase 4: Equipe e Histórico**
    - [x] Grid de membros da equipe (People) com fotos circulares e hover colorido.
    - [x] Linha do tempo (History) com anos em destaque e imagens laterais.
    - [x] Ajustes de tipografia Inter e Lora.

- [x] **Fase 5: Estabilidade e Syntax**
    - [x] Correção de erro de sintaxe Django (nested tags).
    - [x] Correção de erro de renderização (tags Django sendo exibidas como texto puro).
    - [x] Verificação final de layout e responsividade.
