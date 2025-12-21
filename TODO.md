# Feature: Implementação de Coleções (Backend e Frontend)

## Objetivo
Criar o modelo de Coleções (Collections) no banco de dados para gerenciar o conteúdo dinamicamente e ajustar o layout da aba "Collections" para ser mais alto e incluir um carrossel/grid de projetos.

## Fases de Implementação

- [x] Backend
    - [x] Criar model `Collection` em `core/models.py` (Titulo, Descrição, Imagem de Capa, Relacionamento ManyToMany com `Project`).
    - [x] Criar e rodar migrações.
    - [x] Registrar `Collection` no `core/admin.py`.
    - [x] Atualizar `core/views.py` para buscar coleções e passar para o template.
- [x] Frontend (`core/templates/core/project_list.html`)
    - [x] Atualizar loop da aba Collections para usar dados do banco.
    - [x] Aumentar altura da linha da coleção (`h-[600px]` ou mais).
    - [x] Implementar Grid 2x2 de projetos na direita com funcionalidade de Carrossel (ou scroll horizontal snap) para suportar mais de 4 projetos.
    - [x] Adicionar setas de navegação (visual) para o carrossel.
