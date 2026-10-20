# Repositório de Arquivos — Design (v1)

**Data:** 2026-10-16 · **Branch:** `feat/repositorio-arquivos` (a partir da `main`)
**Contexto:** novo módulo da intranet LAPOMED para subir, organizar e descrever
arquivos grandes (modelos 3D, nuvens de pontos, etc.), com metadados dinâmicos e
upload estilo Google Drive. v1 **interno** (não publica no portal público ainda).

## 1. Decisões (batidas com o usuário)

- **Storage:** Backblaze B2 (API S3-compatível), chaves como env vars no Railway.
- **Upload:** multipart **direto do navegador para o B2** via URLs assinadas. O
  Django nunca recebe o conteúdo do arquivo — só os metadados e a chave do objeto.
  Resolve o limite de 100 MB do Cloudflare, o disco efêmero do Railway e tamanho
  ilimitado (10–20 GB).
- **Metadados:** livres por arquivo (`JSONField`) **+** modelos reutilizáveis
  (`MetadataTemplate`). Sem migration por coluna.
- **Organização:** pastas em árvore (estilo Drive), com breadcrumb.
- **Permissão:** novo menu `repositorio` no `IntranetAccess` (toggle por usuário);
  gestor e superuser veem tudo. Mesmo padrão dos outros menus da intranet.
- **Entrega:** PR único. Dependência nova: `boto3`.

## 2. App e rotas

App novo `repositorio/`, montado em `/intranet/repositorio/`
(`lapomed_gallery/urls.py`: `path("intranet/repositorio/", include("repositorio.urls"))`).
`app_name = "repositorio"`. Todas as views usam `menu_required("repositorio")` de
`intranet.permissions`.

Nomes de rota (contrato — front e back dependem destes):

| nome | caminho | método | o que faz |
|------|---------|--------|-----------|
| `index` | `` | GET | redireciona para a pasta raiz (`browse` sem id) |
| `browse` | `pasta/<int:folder_id>/` e `` | GET | navegador: subpastas + arquivos daquela pasta |
| `folder_create` | `pasta/criar/` | POST | cria subpasta (`name`, `parent_id`) |
| `folder_rename` | `pasta/<int:pk>/renomear/` | POST | renomeia |
| `folder_delete` | `pasta/<int:pk>/excluir/` | POST | exclui pasta vazia |
| `file_detail` | `arquivo/<int:pk>/` | GET | detalhe + painel de metadados |
| `file_update` | `arquivo/<int:pk>/editar/` | POST | renomeia / move / salva metadados (JSON) |
| `file_delete` | `arquivo/<int:pk>/excluir/` | POST | apaga objeto no B2 + registro |
| `file_download` | `arquivo/<int:pk>/baixar/` | GET | 302 para URL assinada de GET |
| `upload_init` | `upload/iniciar/` | POST(JSON) | cria `RepoFile` + multipart no B2 |
| `upload_sign` | `upload/assinar/` | POST(JSON) | URL assinada de UMA parte |
| `upload_complete` | `upload/concluir/` | POST(JSON) | finaliza multipart, marca `ready` |
| `upload_abort` | `upload/abortar/` | POST(JSON) | aborta multipart, remove registro |
| `templates` | `modelos/` | GET | lista de `MetadataTemplate` |
| `template_form` | `modelos/novo/` e `modelos/<int:pk>/editar/` | GET/POST | cria/edita modelo |
| `template_delete` | `modelos/<int:pk>/excluir/` | POST | exclui modelo |

## 3. Modelos (`repositorio/models.py`)

```python
class RepoFolder(models.Model):
    name = CharField(max_length=200)
    parent = ForeignKey("self", null=True, blank=True, related_name="children", on_delete=PROTECT)
    created_by = ForeignKey(User, null=True, on_delete=SET_NULL)
    created_at = DateTimeField(auto_now_add=True)
    # helpers: breadcrumb() -> [root..self]; is_empty()

class MetadataTemplate(models.Model):
    name = CharField(max_length=120, unique=True)
    fields = JSONField(default=list)   # ["Período", "Sítio", "Material", ...]
    created_at = DateTimeField(auto_now_add=True)

class RepoFile(models.Model):
    STATUS = [("uploading","Enviando"),("ready","Pronto"),("error","Erro")]
    folder = ForeignKey(RepoFolder, null=True, blank=True, related_name="files", on_delete=PROTECT)
    name = CharField(max_length=255)                 # nome dado pelo usuário
    original_filename = CharField(max_length=255, blank=True)
    object_key = CharField(max_length=500, unique=True)   # chave no bucket B2
    size = BigIntegerField(default=0)
    content_type = CharField(max_length=150, blank=True)
    status = CharField(max_length=12, choices=STATUS, default="uploading")
    metadata = JSONField(default=dict)               # colunas dinâmicas {coluna: valor}
    template = ForeignKey(MetadataTemplate, null=True, blank=True, on_delete=SET_NULL)
    uploaded_by = ForeignKey(User, null=True, on_delete=SET_NULL)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    # helpers: human_size(); extension()
```

`object_key` = `repo/<uuid4>/<filename-seguro>` (evita colisão e nome previsível).

## 4. Integração com a intranet (feita no scaffold)

- `intranet/models.py`: novo campo `menu_repositorio = BooleanField(default=False,
  "Menu: Repositório")`; adicionar `"menu_repositorio"` em `MENU_FIELDS`. O
  `can("repositorio")` já resolve via `menu_<key>` genérico.
- `intranet/context_processors.py`: `MENU_KEYS` recebe `"repositorio"`.
- `intranet/forms.py` (`IntranetUserForm`): campo `menu_repositorio` + em `ACCESS_FIELDS`.
- `intranet/admin.py`: incluir `menu_repositorio` no `list_display`.
- `base_intranet.html`: link na sidebar
  `{% if perms.repositorio %}... url='repositorio:index' key='repositorio' label='Repositório de Arquivos' icon='🗄' ...{% endif %}`.
- `settings.py`: `"repositorio"` em `INSTALLED_APPS`.
- Migrations: `intranet` (campo novo) + `repositorio/0001_initial`.

## 5. Storage / upload multipart (`repositorio/services.py`)

Cliente boto3 S3 apontando para o endpoint do B2:

```python
import boto3
from django.conf import settings
def b2_client():
    return boto3.client("s3", endpoint_url=settings.B2_ENDPOINT,
        aws_access_key_id=settings.B2_KEY_ID, aws_secret_access_key=settings.B2_APP_KEY,
        region_name=settings.B2_REGION)
```

Funções: `create_multipart(key, content_type) -> upload_id`;
`sign_part(key, upload_id, part_number, expires=3600) -> url` (presign `upload_part`);
`complete_multipart(key, upload_id, parts)`; `abort_multipart(key, upload_id)`;
`presign_get(key, filename, expires=3600) -> url` (presign `get_object` com
`ResponseContentDisposition=attachment; filename=...`); `delete_object(key)`.

`PART_SIZE = 100 * 1024 * 1024` (100 MB). Config no `settings.py`:
`B2_ENDPOINT, B2_REGION, B2_KEY_ID, B2_APP_KEY, B2_BUCKET` lidos de `config.py`.
Se faltar credencial → endpoints de upload retornam 503 com mensagem clara (não
quebrar o resto da intranet).

### Fluxo JS ↔ endpoints (contrato para o frontend)

1. `POST upload_init` `{folder_id, name, filename, content_type, size}`
   → `{file_id, upload_id, key, part_size}`. Cria `RepoFile(status=uploading)`.
2. Para cada parte N (1..): `POST upload_sign` `{file_id, upload_id, key, part_number}`
   → `{url}`. JS faz `PUT url` com o blob da parte **direto no B2**; lê o header
   `ETag` da resposta. (Até 3 partes em paralelo.) Barra de progresso por arquivo.
3. `POST upload_complete` `{file_id, upload_id, key, parts:[{PartNumber, ETag}]}`
   → `{ok:true}`. Marca `ready`, grava `size`.
4. Cancelar/erro → `POST upload_abort` `{file_id, upload_id, key}`.

Todos os POST levam o header `X-CSRFToken`. O `PUT` ao B2 é cross-origin — exige
**CORS no bucket** permitindo `PUT`/`POST`/`GET` de `https://lapomed.com.br` (e
`http://localhost:4008` em dev) e **expondo o header `ETag`**. (Documentado pelo
agente de infra.)

## 6. Telas (`repositorio/templates/repositorio/`) — design do site

- `browse.html`: breadcrumb; botões "Nova pasta" e "Enviar arquivos"; grade de
  subpastas; tabela de arquivos (nome, tipo, tamanho, status, data, ações
  baixar/editar/excluir); **zona de arrastar-e-soltar** com fila de uploads e barra
  de progresso por arquivo (o uploader multipart em JS vive aqui).
- `file_detail.html`: dados do arquivo + **painel de metadados** editável: aplicar
  um `MetadataTemplate` (preenche as colunas), adicionar/remover colunas na hora
  (pares chave/valor dinâmicos em JS), salvar via `file_update` (posta `metadata`
  como JSON). Botão baixar.
- `templates.html` / `template_form.html`: CRUD dos modelos de metadados (nome +
  lista de campos, adicionar/remover campo com JS).
- Contexto que as views passam (contrato): `browse` → `folder`, `breadcrumb`,
  `subfolders`, `files`, `templates`, `part_size`, `nav='repositorio'`.
  `file_detail` → `file`, `templates`, `folders` (para mover), `nav='repositorio'`.

Visual: reusa `base_intranet.html` (Cinzel/Lato/lapomed-gold), cards e tabelas no
mesmo estilo das outras telas da intranet.

## 7. Segurança / cuidados

- Tudo atrás de `menu_required("repositorio")`; download também (nada de objeto
  público — só URL assinada temporária).
- Validar que a `key` enviada nos endpoints de upload pertence ao `RepoFile` do
  `file_id` (não confiar na `key` crua do cliente para assinar/concluir).
- `RepoFolder.parent`/`RepoFile.folder` com `PROTECT`: não apaga pasta com conteúdo.
- Excluir arquivo apaga o objeto no B2 antes do registro (ou marca órfão se falhar).
- Limpeza de multipart abortado é responsabilidade do `upload_abort`; uploads
  `uploading` presos podem ser varridos depois (fase 2).

## 8. Testes (`repositorio/tests.py`, com `test_settings`)

Smoke, com boto3 **mockado** (sem rede): gating de permissão (sem `menu_repositorio`
→ 403; com → 200); criar/renomear/excluir pasta; `upload_init` cria `RepoFile`
uploading e chama `create_multipart`; `upload_complete` marca `ready`; aplicar
template copia campos; `file_update` salva metadados dinâmicos; download chama
`presign_get` e redireciona. Nada testa 20 GB de verdade (isso é teste manual).

## 9. Fora do escopo do v1 (fase 2)

Publicar itens 3D na galeria pública; retomar upload entre sessões do navegador;
varredura de uploads órfãos; pré-visualização 3D inline; versionamento de arquivo.

## 10. Divisão do trabalho (time de agentes)

- **Scaffold (eu):** app, models, urls (nomes acima), wiring da intranet,
  `settings.py`, `config.py` (B2 vars), `pyproject` (boto3), migrations.
- **Backend (eu):** `services.py` (B2 multipart) + corpo das views + admin + tests.
- **Frontend (agente):** todos os templates + uploader multipart JS (contrato §5/§6).
- **Infra (agente):** `docs/repositorio/SETUP_B2_RAILWAY.md` — criar bucket, app
  key, **CORS JSON** (com `ExposeHeaders: ETag`), lista de env vars do Railway,
  checklist de teste e nota de custo.
