# Setup do Backblaze B2 + Railway — Repositório de Arquivos

Este guia descreve, passo a passo, como configurar o armazenamento do **Repositório de Arquivos** da intranet LAPOMED.

O repositório faz **upload multipart direto do navegador** para um bucket Backblaze B2 (API S3-compatível). O Django não recebe o arquivo: ele apenas gera **URLs assinadas** (pre-signed) via `boto3`, e o navegador envia cada parte do arquivo diretamente ao B2. Isso permite enviar arquivos grandes (10–20 GB) sem passar pelo servidor Railway.

O Django lê estas 5 variáveis de ambiente:

| Variável       | Exemplo                                   | O que é                                         |
| -------------- | ----------------------------------------- | ----------------------------------------------- |
| `B2_ENDPOINT`  | `https://s3.us-west-004.backblazeb2.com`  | URL do endpoint S3 do B2 (**com `https://`**)   |
| `B2_REGION`    | `us-west-004`                             | Região do bucket                                |
| `B2_KEY_ID`    | `<SEU_KEY_ID>`                            | keyID da Application Key                         |
| `B2_APP_KEY`   | `<SUA_APPLICATION_KEY>`                   | applicationKey (segredo — aparece só UMA vez)   |
| `B2_BUCKET`    | `lapomed-repositorio`                     | Nome do bucket                                  |

> **Regra de ouro:** essas chaves **NUNCA** vão para o git. Só no painel do Railway (produção) e num `.env` local não versionado (dev).

---

## 1. Criar a conta e o bucket (privado) no Backblaze B2

1. Crie/acesse sua conta em <https://www.backblaze.com/> e entre no console do **B2 Cloud Storage**.
2. No menu lateral, vá em **B2 Cloud Storage → Buckets** e clique em **Create a Bucket**.
3. Preencha:
   - **Bucket Unique Name:** `lapomed-repositorio` (o nome é global no B2; se já existir, escolha outro, ex.: `lapomed-usp-arquivos`).
   - **Files in Bucket are:** selecione **Private** (privado). Isso é essencial — o acesso só acontece via URLs assinadas geradas pelo Django.
   - **Default Encryption:** pode deixar habilitado (SSE-B2) se desejar; não interfere no upload assinado.
   - **Object Lock:** deixe **desabilitado** (a menos que você queira imutabilidade; não é necessário aqui).
4. Clique em **Create a Bucket**.

### Onde achar o Endpoint e a Region

Depois de criar, clique no bucket (ou veja o card do bucket). Procure a linha **Endpoint**, algo como:

```
s3.us-west-004.backblazeb2.com
```

A partir dela você extrai as duas variáveis:

- **`B2_REGION`** = a parte do meio do endpoint → neste exemplo `us-west-004`.
- **`B2_ENDPOINT`** = o endpoint **com o prefixo `https://`** → `https://s3.us-west-004.backblazeb2.com`.

> **Atenção:** o B2 mostra o endpoint **sem** `https://`. O `boto3` precisa da URL completa. **Sempre inclua `https://` em `B2_ENDPOINT`.** Sua região depende de onde o bucket foi criado (pode ser `us-west-002`, `us-west-004`, `eu-central-003` etc.) — use exatamente o que aparece no seu console, não copie o exemplo cegamente.

---

## 2. Criar uma Application Key restrita ao bucket

Nunca use a **Master Application Key** da conta na aplicação. Crie uma chave dedicada e restrita a este bucket.

1. No console, vá em **Account → Application Keys**.
2. Clique em **Add a New Application Key**.
3. Preencha:
   - **Name of Key:** `lapomed-repositorio-app` (nome só para você identificar).
   - **Allow access to Bucket(s):** selecione **apenas** `lapomed-repositorio` (restringe a chave a este bucket — princípio do menor privilégio).
   - **Type of Access:** **Read and Write** (precisa escrever para fazer upload e ler para gerar downloads).
   - **Allow List All Bucket Names:** pode deixar desmarcado.
   - **File name prefix** e **Duration:** deixe em branco (sem expiração/sem restrição de prefixo), a menos que queira endurecer ainda mais.
4. Clique em **Create New Key**.

### O que vai em cada variável

Após criar, o B2 mostra:

- **keyID** → vai em **`B2_KEY_ID`**.
- **applicationKey** → vai em **`B2_APP_KEY`**.

> **CRÍTICO:** a **applicationKey (o segredo) aparece UMA ÚNICA VEZ**, nesta tela, logo após a criação. Copie imediatamente para um lugar seguro (gerenciador de senhas / painel do Railway). Se você fechar a página sem copiar, **não dá para recuperar** — terá que apagar a chave e criar outra.

---

## 3. Configurar o CORS do bucket (essencial para upload direto do navegador)

Como o upload parte do **navegador** (JavaScript `fetch`/`XHR` fazendo `PUT` de cada parte diretamente ao B2), o bucket precisa de regras de **CORS** que:

1. Permitam as origens da aplicação (`https://lapomed.com.br` e `http://localhost:4008`).
2. Permitam os métodos `GET, PUT, POST, HEAD`.
3. **Exponham o header `ETag`** nas respostas.

### Por que expor o `ETag` é obrigatório

No upload multipart S3-compatible, cada parte enviada retorna um header `ETag` na resposta do `PUT`. O JavaScript precisa **ler esse `ETag` de cada parte** e enviá-lo de volta ao Django na etapa de **CompleteMultipartUpload** (a lista de partes é `[{PartNumber, ETag}, ...]`). 

Por padrão, o navegador **só deixa o JS ler um conjunto mínimo de headers** da resposta cross-origin. Se o bucket não declarar `ETag` em `exposeHeaders` / `ExposedHeaders`, o `response.headers.get('ETag')` volta **`null`**, a lista de partes fica sem ETag e o **CompleteMultipartUpload falha** (erro `InvalidPart` ou similar). Por isso expor o `ETag` não é opcional — sem ele o multipart não fecha.

### 3a. Formato nativo do B2 ("CORS Rules")

Este é o JSON no formato do próprio Backblaze B2. Salve como `cors-rules.json`:

```json
[
  {
    "corsRuleName": "repositorio-navegador",
    "allowedOrigins": [
      "https://lapomed.com.br",
      "http://localhost:4008"
    ],
    "allowedOperations": [
      "s3_get",
      "s3_head",
      "s3_post",
      "s3_put"
    ],
    "allowedHeaders": [
      "*"
    ],
    "exposeHeaders": [
      "ETag",
      "x-amz-request-id",
      "x-amz-id-2"
    ],
    "maxAgeSeconds": 3600
  }
]
```

Aplique com a CLI oficial do B2 (`b2`):

```bash
# instalar a CLI (uma vez): pip install b2  (ou brew install b2-tools)
b2 account authorize <SEU_KEY_ID> <SUA_APPLICATION_KEY>

# aplicar as regras de CORS ao bucket
b2 bucket update --cors-rules "$(cat cors-rules.json)" lapomed-repositorio allPrivate

# conferir o que ficou gravado
b2 bucket get lapomed-repositorio
```

> Observação: em versões mais antigas da CLI o comando era `b2 update-bucket <bucket> allPrivate --corsRules "$(cat cors-rules.json)"`. Se `b2 bucket update` não existir na sua versão, rode `b2 --help` para ver a forma correta. O conteúdo do JSON é o mesmo.

### 3b. Alternativa: via UI do console B2

No console web: **Bucket → CORS Rules** (ou "Bucket Settings" → seção CORS). Algumas contas oferecem um editor que aceita colar exatamente o JSON acima (array de regras no formato nativo B2). Preencha:

- **Origins:** `https://lapomed.com.br` e `http://localhost:4008`
- **Operations/Methods:** GET, HEAD, POST, PUT
- **Headers allowed:** `*`
- **Headers exposed:** `ETag` (e opcionalmente `x-amz-request-id`, `x-amz-id-2`)
- **Max age:** `3600`

### 3c. Alternativa: via AWS CLI (`put-bucket-cors`) apontando para o endpoint do B2

Como o B2 é S3-compatível, dá para usar a AWS CLI apontando `--endpoint-url` para o B2. Esse formato usa os nomes S3 (`AllowedMethods`, `ExposeHeaders` etc.). Salve como `cors-aws.json`:

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": [
        "https://lapomed.com.br",
        "http://localhost:4008"
      ],
      "AllowedMethods": [
        "GET",
        "PUT",
        "POST",
        "HEAD"
      ],
      "AllowedHeaders": [
        "*"
      ],
      "ExposeHeaders": [
        "ETag",
        "x-amz-request-id",
        "x-amz-id-2"
      ],
      "MaxAgeSeconds": 3600
    }
  ]
}
```

Aplique (configure antes `aws configure` com o keyID/applicationKey do B2, ou passe via variáveis de ambiente `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`):

```bash
# região e endpoint do B2 (ajuste para a SUA região)
aws s3api put-bucket-cors \
  --bucket lapomed-repositorio \
  --cors-configuration file://cors-aws.json \
  --endpoint-url https://s3.us-west-004.backblazeb2.com \
  --region us-west-004

# conferir
aws s3api get-bucket-cors \
  --bucket lapomed-repositorio \
  --endpoint-url https://s3.us-west-004.backblazeb2.com \
  --region us-west-004
```

> As duas abordagens (nativa B2 e AWS CLI) configuram a **mesma coisa** no bucket. Use a que for mais conveniente. O importante: origens corretas, métodos `GET/PUT/POST/HEAD` e **`ETag` exposto**.

---

## 4. Setar as variáveis no Railway

As chaves de produção vivem **apenas** no painel do Railway, nunca no git.

1. Acesse <https://railway.app/> e abra o projeto **Galhardo Lab**.
2. Selecione o serviço **lapomed-site**.
3. Abra a aba **Variables**.
4. Clique em **New Variable** (ou **+ New Variable** / **Raw Editor**) e adicione exatamente estas 5 variáveis:

   ```
   B2_ENDPOINT=https://s3.us-west-004.backblazeb2.com
   B2_REGION=us-west-004
   B2_KEY_ID=<SEU_KEY_ID>
   B2_APP_KEY=<SUA_APPLICATION_KEY>
   B2_BUCKET=lapomed-repositorio
   ```

   (Substitua os valores de exemplo de `B2_ENDPOINT`/`B2_REGION`/`B2_BUCKET` pelos seus reais, e os placeholders pelas chaves copiadas no passo 2.)

5. Salve. O Railway normalmente dispara um **redeploy** automático ao mudar variáveis; se não disparar, faça um **redeploy** manual para o serviço pegar os novos valores.

### Dev local (`.env` não versionado)

Para rodar o repositório no dev local (`http://localhost:4008`), coloque as mesmas 5 variáveis num arquivo `.env` na raiz do projeto:

```dotenv
# .env  (NÃO versionar — precisa estar no .gitignore)
B2_ENDPOINT=https://s3.us-west-004.backblazeb2.com
B2_REGION=us-west-004
B2_KEY_ID=<SEU_KEY_ID>
B2_APP_KEY=<SUA_APPLICATION_KEY>
B2_BUCKET=lapomed-repositorio
```

> **Confirme que `.env` está no `.gitignore`.** Nunca commite as chaves. Se uma chave vazar para o git, **apague-a no console do B2 e gere outra** — remover do histórico do git não basta, pois a chave já foi exposta.

---

## 5. Checklist de verificação

Antes de considerar a configuração pronta:

- [ ] Bucket é **Private**.
- [ ] Application Key restrita ao bucket, com **Read and Write**.
- [ ] As 5 variáveis estão no Railway (produção) e no `.env` local (dev), com `B2_ENDPOINT` começando em `https://`.
- [ ] `.env` está no `.gitignore` e nenhuma chave está commitada.
- [ ] CORS aplicado com origens `https://lapomed.com.br` e `http://localhost:4008`, métodos `GET/PUT/POST/HEAD`, e **`ETag` exposto**.

### Como confirmar que o CORS está certo (testar um PUT assinado e ver o ETag)

O jeito mais fiel é testar um `PUT` assinado a partir de uma origem permitida e checar se o navegador consegue ler o `ETag`:

1. Gere, pelo Django (ou manualmente via `boto3`), uma URL assinada de `PUT` (um `upload_part` ou um simples `put_object`).
2. Abra o DevTools do navegador **em uma aba de uma origem permitida** (ex.: na própria `http://localhost:4008`) e rode no console:

   ```js
   const url = "<URL_ASSINADA_PUT>";
   const resp = await fetch(url, {
     method: "PUT",
     body: new Blob(["teste-cors-" + Date.now()]),
   });
   console.log("status:", resp.status);          // espera 200
   console.log("ETag:", resp.headers.get("ETag")); // precisa NÃO ser null
   ```

   - **Status 200** e **`ETag` diferente de `null`** → CORS OK e ETag exposto. 
   - Se aparecer erro de CORS no console, ou `ETag` vier `null` → revise as regras do passo 3 (origem exata, inclusive `http` vs `https` e a porta `:4008`; e `ETag` em `exposeHeaders`/`ExposedHeaders`).

3. (Opcional) Teste rápido só do preflight com `curl` (não valida exposeHeaders para o JS, mas confirma allowOrigin/allowMethods):

   ```bash
   curl -i -X OPTIONS "https://s3.us-west-004.backblazeb2.com/lapomed-repositorio/teste" \
     -H "Origin: http://localhost:4008" \
     -H "Access-Control-Request-Method: PUT"
   # procure nos headers de resposta: Access-Control-Allow-Origin e Access-Control-Allow-Methods
   ```

### Lembrete sobre arquivos grandes

Arquivos de **10–20 GB levam tempo** e o gargalo é a **banda de upload do cliente** (não o servidor). Numa conexão doméstica típica de upload (ex.: 20–50 Mbps), 20 GB podem levar **horas**. Oriente os usuários a:

- Não fechar a aba durante o envio.
- Usar conexão estável (de preferência cabeada).
- Contar com o multipart para permitir retomar/retentar partes que falharem.

---

## 6. Nota de custo (aproximado — sujeito a mudança)

Estimativas apenas para dimensionamento. **Confirme os valores atuais no site do Backblaze** antes de decidir: <https://www.backblaze.com/cloud-storage/pricing>

- **Armazenamento:** ~**US$ 6 por TB por mês** (≈ US$ 0,006/GB/mês).
- **Egress (download/saída):** o B2 tem **franquia gratuita generosa** (historicamente, saída grátis até um múltiplo do volume armazenado, e saída grátis via parceiros como Cloudflare). Para o uso interno da intranet, o egress tende a ser **irrelevante** no custo.
- **Transações (chamadas de API):** classes B/C têm custo baixíssimo e uma franquia diária gratuita; para este volume de uso, desprezível.

**Estimativa prática:** 20 GB de arquivos ≈ **US$ 0,12/mês**. Mesmo com **vários arquivos de 20 GB** somando, digamos, 200–500 GB no total, isso fica na casa de **US$ 1 a US$ 3 por mês** — poucos dólares/mês.

> Todos os números acima são **aproximados e sujeitos a mudança**. Trate como ordem de grandeza, não como fatura. **Confirme no site oficial do Backblaze.**
