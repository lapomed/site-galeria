# Roadmap — Visitas Virtuais 3D

Plano para evoluir as Visitas Virtuais do LAPOMED em direção a uma experiência narrada e
navegável no estilo da [CyArk Tapestry](https://tapestry.cyark.org/library).

---

## 1. Estado atual (Fase 1 — entregue)

- Modelo `VirtualTour` com `slug`, `tagline`, `location`, `language`, `thumbnail`, `hero_image`,
  `embed_url`, `embed_code`, `model_file`.
- Listagem `/visitas-3d/` no estilo Tapestry: hero gradient, search bar com filtros visuais,
  grid full-bleed clicável.
- Splash page `/visitas-3d/<slug>/` com glass card centralizado, botão **START**.
- START aciona Fullscreen API real e injeta o conteúdo (iframe Sketchfab/Matterport/Kuula
  ou `<model-viewer>` para `.glb`/`.gltf`). Loading spinner + atalho ESC para sair.
- `<model-viewer>` melhorado: auto-rotate suave, prompt de interação, barra de progresso
  dourada, hint "clique e arraste · scroll para zoom".
- Conversão automática de URL pública do Sketchfab para URL de embed.
- Limites de upload elevados (DATA_UPLOAD 200MB) + Gunicorn timeout 300s para `.glb` grande.

**Limitações atuais**:
- Sem capítulos / cenas estruturadas.
- Sem narração de áudio sincronizada.
- Sem hotspots clicáveis sobre o modelo 3D.
- Sem galeria contextual ao lado da experiência.
- Sem suporte multi-idioma na narração.

---

## 2. Visão da Fase 2 — experiência narrada

Replicar os 4 pilares da Tapestry/CyArk:

1. **Capítulos numerados** (sidebar 1, 2, 3…) com transição automática ou manual.
2. **Narração de áudio** sincronizada com captions, controles play/pause/skip.
3. **Hotspots clicáveis** sobre a cena 3D que abrem cards de detalhe.
4. **Galeria lateral** (rp_gallery) com fotos contextuais do capítulo.

---

## 3. Modelos a criar

```python
class TourScene(models.Model):
    """Capítulo / cena de uma visita virtual."""
    tour = ForeignKey(VirtualTour, related_name='scenes')
    order = PositiveIntegerField(db_index=True)
    title = CharField()           # "Welcome to Pompeii"
    subtitle = CharField()         # "Frozen by Vesuvius in 79 CE..."
    description = HTMLField()      # texto longo opcional
    panorama_image = ImageField()  # 360° equirectangular OU
    embed_url = URLField()         # Sketchfab/Matterport scoped à cena
    initial_yaw = FloatField()     # ângulo de partida da câmera
    initial_pitch = FloatField()
    duration_estimate = IntegerField()  # segundos esperados nesta cena

class TourNarration(models.Model):
    """Faixa de áudio narrada de um capítulo (uma por idioma)."""
    scene = ForeignKey(TourScene, related_name='narrations')
    language = CharField(choices=[('pt', 'Português'), ('en', 'English'), ('es', 'Español')])
    audio_file = FileField(upload_to='tours/audio/')   # MP3 ou WebM
    captions_vtt = FileField(upload_to='tours/captions/', blank=True)  # WebVTT
    duration = IntegerField()  # segundos, lido do header

class TourHotspot(models.Model):
    """Ponto interativo sobre a cena 3D."""
    scene = ForeignKey(TourScene, related_name='hotspots')
    x = FloatField()  # coordenadas no espaço da cena (Yaw/Pitch para 360°)
    y = FloatField()
    label = CharField()              # texto curto exibido no hover
    title = CharField()              # título do popup
    body = HTMLField()               # corpo do popup
    image = ImageField(blank=True)   # imagem ilustrativa (opcional)

class TourGalleryImage(models.Model):
    """Foto contextual exibida na aba Gallery do tour ou de uma cena específica."""
    tour = ForeignKey(VirtualTour, related_name='gallery_images')
    scene = ForeignKey(TourScene, blank=True, null=True,
                       help_text='Vincula a uma cena específica; se vazio, aparece na galeria geral')
    order = PositiveIntegerField()
    image = ImageField(upload_to='tours/gallery/')
    caption = CharField()
    credit = CharField(blank=True)
```

Migration adiciona as 4 tabelas. Admin com `TabularInline` aninhado:
`VirtualTourAdmin → TourSceneInline → (TourNarration + TourHotspot + TourGalleryImage)`.
Como Django não suporta inline aninhado nativamente, usar **django-nested-admin** ou
registrar `TourScene` como top-level com seus próprios inlines.

---

## 4. Frontend stack proposto

Para cenas 360° panorâmicas, evitar Three.js custom — usar uma das libs maduras:

| Lib | Pros | Contras |
|---|---|---|
| **Marzipano** (Pannellum's spiritual successor) | Open source, suporta multi-resolução, zoom, hotspots nativos, hooks de evento, ~80kb gzip | API menos amigável que Pannellum |
| **Pannellum** | API simples, JSON config direto, popular | Sem zoom infinito, hotspots básicos |
| **Photo Sphere Viewer** | Plugin ecosystem rico (markers, gyroscope, VR), boa docs | ~150kb gzip |

**Recomendação**: **Marzipano** — usado pela Google em vários projetos, hotspots interativos
robustos, comportamento consistente em mobile.

Para narração: **Howler.js** (~7kb) — sincronização precisa, suporte WebVTT pra captions
nativo via `<track>` em `<audio>`, fade in/out automático entre cenas.

Para a UI:
- Continuar com **Tailwind** + **Vanilla JS** (sem React/Vue) — mantém consistência com o
  resto do projeto.
- Componentes da experiência:
  - `SceneNav` (sidebar esquerda numerada, marca a cena ativa)
  - `AudioPlayer` (overlay inferior: play/pause/prev/next, slider, captions toggle)
  - `HotspotLayer` (markers posicionados em yaw/pitch que abrem cards)
  - `GalleryPanel` (aba lateral direita deslizante com grid de fotos)
  - `CaptionsOverlay` (legenda sincronizada exibida sobre a cena)

---

## 5. API endpoints

```
GET /api/visitas-3d/<slug>/
→ {
    "title": "...",
    "scenes": [
      {
        "id": 1, "order": 1, "title": "...", "subtitle": "...",
        "panorama": "/media/...", "yaw": 0, "pitch": 0,
        "narration": { "pt": {"audio": "...", "captions": "...", "duration": 44},
                       "en": {...} },
        "hotspots": [{ "x": 0.34, "y": -0.12, "label": "...", "title": "...", "body": "..." }],
        "gallery": [...]
      },
      ...
    ]
  }
```

Implementar via `JsonResponse` simples no view (não precisa de DRF) ou usar `serializers.py`
manual. Sem auth — endpoint público.

---

## 6. Fluxo do usuário

1. `/visitas-3d/` → escolhe um tour → `/visitas-3d/<slug>/` (splash atual).
2. Clica **START** → fullscreen + carrega cena 1.
3. Áudio começa automaticamente (idioma do navegador, fallback PT).
4. Usuário pode:
   - Navegar a câmera arrastando.
   - Clicar hotspots → card abre, áudio pausa, retoma ao fechar.
   - Pular cena (next/prev).
   - Abrir aba Gallery (botão lateral).
   - Trocar idioma da narração (dropdown topo).
   - CC ligar/desligar.
5. Ao terminar última cena → tela "Obrigado por explorar" com link pra biblioteca.

---

## 7. Plano de cadastro (UX do admin)

1. Criar `VirtualTour` (já existe).
2. Adicionar cenas via inline `TourScene` (mín. 1 obrigatória) com upload do panorama 360°.
3. Para cada cena, anexar 1+ `TourNarration` (idioma + áudio MP3 + WebVTT opcional).
4. Posicionar `TourHotspot` (no admin, idealmente um picker visual; v1 = inputs numéricos).
5. Subir `TourGalleryImage` por cena ou pra galeria geral.

Todos os arquivos vão pro Railway Volume (já configurado).

---

## 8. Estimativa de esforço

| Tarefa | Estimativa |
|---|---|
| Modelos + migrations + admin (incluindo nested-admin) | 1 dia |
| API JSON endpoint | meio dia |
| Integração Marzipano + carregamento de cena | 1 dia |
| Audio player com Howler + sync de captions | 1 dia |
| Hotspots clicáveis + popup | meio dia |
| Galeria lateral | meio dia |
| Multi-idioma + UI controls | meio dia |
| Polish + testes + responsividade mobile | 1 dia |
| **Total** | **~6 dias úteis** |

---

## 9. Decisões pendentes

- **Hotspots em embed externo (Sketchfab/Matterport)?** Eles já oferecem hotspots/anotações
  internas. Para esses casos, fazer só link "Veja anotações no Sketchfab" e pular a layer
  custom. Hotspots LAPOMED ficam disponíveis quando a cena é panorama 360° próprio.
- **Narração: TTS gerada vs. gravada?** Gravada é melhor (ElevenLabs/Resemble são opções
  pagas; estúdio acadêmico em alguns casos). TTS de Edge/Google grátis serve pra v1.
- **Tour multi-cenas obrigatório?** Não — `TourScene` opcional. Se um tour não tem cenas
  cadastradas, o comportamento atual (embed direto fullscreen) continua valendo.

---

## 10. Próximo passo recomendado

Antes de codar a Fase 2 inteira, validar com 1 tour piloto:
- Escolher 1 sítio que faça sentido (ex: Pampa Negro ou Beit She'an).
- Capturar/gerar 3-4 panoramas 360° (drone ou foto esférica do iPhone Pro).
- Cadastrar manualmente um JSON de prova com `scenes`/`hotspots` e renderizar via
  Marzipano embedado num template estático — sem migration ainda.
- Se a navegação convencer, partir pros modelos Django e admin.

Esse "spike" custa ~1 dia e evita gastar 6 dias no abstrato.
