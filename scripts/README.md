# Scripts utilitarios

## `download_coalitvs_photos.py`

Baixa fotos dos 53 pesquisadores do COALITVS via Wikipedia REST API.

### Como rodar (localmente, na sua maquina)

```bash
cd /caminho/para/site-galeria
python scripts/download_coalitvs_photos.py
```

Nao precisa de virtualenv ou dependencias: usa so `urllib` da stdlib.

### O que faz

Para cada um dos 53 pesquisadores:

1. Verifica se ja existe `media/coalitvs/<slug>.<ext>` -> pula
2. Tenta Wikipedia em ingles via REST API (`/api/rest_v1/page/summary/<Name>`)
3. Tenta Wikipedia em portugues (fallback util pra brasileiros/ibericos)
4. Se nao achar, marca como FALHA no relatorio

Saidas:
- `media/coalitvs/<slug>.jpg` (ou `.png`/`.webp`) com a foto baixada
- `scripts/download_report.txt` com resumo: ok/falha por pessoa

### Expectativa de cobertura

Pesquisadores muito conhecidos com pagina na Wikipedia (Ian Hodder, Andrea Berlin,
Pedro Funari, Pedro Paulo Funari, Jaś Elsner etc.): **~30-50% de sucesso**.

Para os demais, voce vai precisar:
- Adicionar URL manualmente no array `MEMBERS` do script (3o elemento da tupla,
  campo `override`)
- OU fazer upload pelo admin: `/admin/core/coalitvsmember/`

### Apos rodar

1. **Revise visualmente** o conteudo de `media/coalitvs/` — Wikipedia as vezes
   pega imagens erradas (ex: pessoa com mesmo nome). Delete o que nao serve.

2. **Commit** as fotos (ou nao — depende da sua estrategia de media):
   ```bash
   git add media/coalitvs/
   git commit -m "media: fotos do COALITVS"
   git push origin <branch>
   ```

3. **Deploy** automaticamente roda a migration `0028_coalitvs_photos`, que
   correlaciona cada arquivo com o membro do banco via slug. Idempotente.

### Para os pesquisadores que falharem

Tres opcoes:

**A) Adicionar URL manualmente no script** (e re-rodar)
```python
("Marcio Teixeira-Bastos", "nacional", "https://exemplo.com/foto.jpg"),
```

**B) Upload manual pelo admin** (recomendado para uploads pontuais)
```
/admin/core/coalitvsmember/<id>/change/ -> campo Foto
```

**C) Colocar arquivo direto em `media/coalitvs/<slug>.jpg`** e deixar a
migration correlacionar no proximo deploy.
