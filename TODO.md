# Feature: Ajuste de Posicionamento do Footer (Sticky Footer)

## Objetivo
Garantir que o footer da aplicação fique sempre posicionado na parte inferior da tela (rodapé), independentemente da quantidade de conteúdo na página, e corrigir o problema visual na lista de projetos.

## Fases de Implementação

- [x] Modificar `core/templates/core/base.html`
    - [x] Adicionar classes Flexbox ao `body` (`flex flex-col min-h-screen`) para estrutura de Sticky Footer.
    - [x] Adicionar `flex-grow` (ou `flex-1`) e `flex flex-col` ao elemento `<main>` para ocupar o espaço disponível.
- [x] Modificar `core/templates/core/project_list.html`
    - [x] Adicionar `flex-grow` à div container principal para que o fundo cinza (`bg-[#d1d1d1]`) preencha todo o espaço até o footer.
- [x] Validar visual na lista de projetos.
