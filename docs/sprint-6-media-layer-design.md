# Sprint 6 — Media Layer Foundation

**Status:** Design  
**Target:** v0.7.0-media  
**Depends on:** Sprint 5C (Research Memory)  

---

## 1. Motivation

The application currently generates text-based artifacts (carousels, reports, presentations, research). Users cannot produce images, audio, or video through the system. Adding media generation as first-class capabilities unlocks:

- AI-generated hero images for reports/carousels/presentations
- Audio overviews from research synopses
- Promotional short videos from presentation decks
- Voice-annotated research memos
- Social media video clips from carousel content

---

## 2. Architecture: Media Layer

```
┌────────────────────────────────────────────────┐
│                Application Layer                │
│  ImageService  │  AudioService  │ VideoService  │
├────────────────────────────────────────────────┤
│               Ports (Abstract)                  │
│  MediaPort (gen_image, gen_audio, gen_video)    │
├────────────────────────────────────────────────┤
│              Adapter Layer                       │
│  ReplicateAdapter │ OpenAIAdapter │ FalAdapter   │
├────────────────────────────────────────────────┤
│                  Storage Layer                   │
│  media_files (FS)  │ media_meta (SQLite)         │
└────────────────────────────────────────────────┘
```

### 2.1 Layer Boundaries

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| **Ports** | Abstract media generation contract | `toll/ports/media.py` |
| **Adapters** | Provider-specific implementation | `toll/adapters/media/*.py` |
| **Services** | Business logic, prompt building, artifact creation | `toll/application/media_service.py` |
| **Renderers** | HTML preview of media in context | `toll/engine/renderers/media_renderer.py` |
| **Storage** | File system + metadata DB | `media_files/` dir, migration 0010 |

### 2.2 Design Constraints

- **Local-first** — no mandatory cloud dependency; optional providers
- **File + metadata** — media binaries stored on filesystem, metadata (provider, model, prompt, dimensions, duration) in SQLite
- **Size limits** — images ≤ 20 MB, audio ≤ 50 MB, video ≤ 200 MB (configurable via settings)
- **Async generation** — video and audio may take seconds; services are sync-call with timeout, but the architecture must support future async webhook patterns
- **No streaming yet** — Sprint 6 returns completed media; streaming is a future sprint
- **Preview-first** — preview renderer shows media inline with metadata card

---

## 3. Files Changed/Added (13 files)

### New Files (10)

| # | File | Purpose |
|---|------|---------|
| 1 | `toll/ports/media.py` | `MediaPort` abstract class + `MediaRequest`/`MediaResult` dataclasses |
| 2 | `toll/adapters/media/__init__.py` | Package init |
| 3 | `toll/adapters/media/replicate.py` | Replicate adapter (Flux, Stable Diffusion, etc.) |
| 4 | `toll/adapters/media/ollama.py` | Ollama adapter (local image gen if supported) |
| 5 | `toll/adapters/media/opencode.py` | OpenCode adapter (delegates to opencode media cmds) |
| 6 | `toll/ports/media_storage.py` | `MediaStorage` port — save/retrieve/delete media files |
| 7 | `toll/adapters/media/fs_storage.py` | Filesystem implementation of `MediaStorage` |
| 8 | `toll/application/media_service.py` | `MediaService` — generate images/audio/video, wrap in artifacts |
| 9 | `toll/engine/renderers/media_renderer.py` | Preview renderers for image/audio/video artifacts |
| 10 | `toll/model/migrations/0010_media.sql` | `media_meta` table + `media_resources` table |

### Modified Files (3)

| # | File | Change |
|---|------|--------|
| 11 | `toll/model/artifact.py` | Add `IMAGE_GEN`, `AUDIO`, `VIDEO` to `ArtifactType` enum |
| 12 | `toll/core/feature_flags.py` | Register 6 media feature flags |
| 13 | `toll/application/handler_registry.py` | Register `media_generate` handler |

---

## 4. Port Design (`toll/ports/media.py`)

```python
@dataclass
class MediaRequest:
    prompt: str
    media_type: str  # "image" | "audio" | "video"
    negative_prompt: str = ""
    size: str | None = None       # e.g. "1024x1024", "1920x1080"
    duration: int | None = None   # seconds (audio/video)
    model: str | None = None
    seed: int | None = None
    input_media_path: str | None = None  # for image-to-image, image-to-video
    voice: str | None = None            # for TTS
    style: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class MediaResult:
    success: bool
    media_path: str | None = None
    media_type: str = ""
    provider: str = ""
    model: str = ""
    duration_ms: int = 0
    content_type: str = ""  # mime
    width: int | None = None
    height: int | None = None
    file_size_bytes: int = 0
    seed: int | None = None
    error: str | None = None
    raw_response: dict = field(default_factory=dict)


class MediaPort(ABC):
    name: str = "abstract_media"

    @abstractmethod
    def generate(self, request: MediaRequest) -> MediaResult:
        ...

    def is_available(self) -> bool:
        return True

    def supported_types(self) -> list[str]:
        return ["image"]
```

### Port Design Rationale

- Single `generate()` method covers all media types — provider decides what it can do based on `request.media_type`
- `MediaResult` captures both success and error paths uniformly
- `input_media_path` enables image-to-image and image-to-video workflows
- `seed` for reproducible generations
- `supported_types()` lets the service discover provider capabilities

---

## 5. Storage Design

### 5.1 Filesystem Layout

```
data/
├── media/
│   ├── images/         # .png, .jpg, .webp
│   ├── audio/          # .mp3, .wav, .ogg
│   └── video/          # .mp4, .webm
```

Each file named: `{uuid}.{ext}`  

### 5.2 `MediaStorage` Port (`toll/ports/media_storage.py`)

```python
class MediaStorage(ABC):
    @abstractmethod
    def save(self, data: bytes, media_type: str, extension: str) -> str:
        """Save bytes, return storage key (relative path)."""
        ...

    @abstractmethod
    def get_path(self, storage_key: str) -> Path | None:
        """Resolve storage key to absolute filesystem path."""
        ...

    @abstractmethod
    def delete(self, storage_key: str) -> bool:
        ...
```

### 5.3 SQLite Migrations (`0010_media.sql`)

```sql
CREATE TABLE IF NOT EXISTS media_meta (
    id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    media_type TEXT NOT NULL,        -- 'image', 'audio', 'video'
    storage_key TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT,
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    width INTEGER,
    height INTEGER,
    duration_ms INTEGER,
    file_size_bytes INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    seed INTEGER,
    style TEXT,
    voice TEXT,
    error TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_media_artifact_id ON media_meta(artifact_id);
CREATE INDEX idx_media_type ON media_meta(media_type);

CREATE TABLE IF NOT EXISTS media_resources (
    id TEXT PRIMARY KEY,
    source_media_id TEXT NOT NULL,
    derived_media_id TEXT NOT NULL,
    operation TEXT NOT NULL,          -- 'gen_image', 'gen_video', 'edit', 'upscale'
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (source_media_id) REFERENCES media_meta(id),
    FOREIGN KEY (derived_media_id) REFERENCES media_meta(id)
);
```

---

## 6. Service Design (`toll/application/media_service.py`)

```python
class MediaService:
    def __init__(self, artifact_service, selector, cm, flags=None):
        self.artifact_service = artifact_service
        self.selector = selector
        self.cm = cm
        self.flags = flags or FeatureFlags(cm=cm)
        self.ai = AI(cm=cm)
        self.preview = MediaPreviewRenderer()
        self.storage = FsMediaStorage()

    def execute(self, plan: dict, metadata=None) -> dict:
        """Main entry point. Dispatches by media_type in plan."""
        media_type = plan.get("media_type", "image")
        if media_type == "image":
            return self._generate_image(plan, metadata)
        elif media_type == "audio":
            return self._generate_audio(plan, metadata)
        elif media_type == "video":
            return self._generate_video(plan, metadata)
        return {"error": f"Unknown media_type: {media_type}"}

    def _generate_image(self, plan, metadata) -> dict:
        """Generate image → store → create artifact → return result."""

    def _generate_audio(self, plan, metadata) -> dict:
        """Generate TTS/music → store → create artifact."""

    def _generate_video(self, plan, metadata) -> dict:
        """Generate video → store → create artifact."""
```

### 6.1 Provider Selection

`MediaService` uses `self.selector.select(ArtifactType.IMAGE_GEN)` — the `ProviderSelector` is extended to understand media types. Currently the selector only handles LLM provider scoring; Sprint 6 extends `_quality_score` with media provider entries.

### 6.2 Output Format

```python
{
    "artifact_id": "uuid",
    "type": "image_gen" | "audio" | "video",
    "title": "...",
    "media_url": "/data/media/images/uuid.png",
    "media_type": "image",
    "content_type": "image/png",
    "file_size_bytes": 123456,
    "width": 1024,
    "height": 1024,
    "duration_ms": null,
    "provider": "replicate",
    "model": "flux-schnell",
    "seed": 42,
    "preview_url": "/data/artifacts/uuid/preview.html",
}
```

---

## 7. Provider Adapter Design

### 7.1 Replicate Adapter (`toll/adapters/media/replicate.py`)

```python
class ReplicateMediaAdapter(MediaPort):
    name = "replicate"

    MODELS = {
        "image": {
            "flux-schnell": "black-forest-labs/flux-schnell",
            "flux-pro": "black-forest-labs/flux-pro",
            "sdxl": "stability-ai/sdxl",
        },
        "audio": {
            "elevenlabs": "elevenlabs/elevenlabs-tts",
        },
        "video": {
            "stable-video": "stability-ai/stable-video-diffusion",
        },
    }

    def generate(self, request: MediaRequest) -> MediaResult:
        # Map model name → Replicate model ID
        # Call replicate.run(model_id, input={...})
        # Download output to bytes
        # Return MediaResult
```

### 7.2 Ollama Adapter (`toll/adapters/media/ollama.py`)

Stub for future local image generation models (e.g., llava, bakllava). Returns `not_available` for audio/video.

### 7.3 OpenCode Adapter (`toll/adapters/media/opencode.py`)

Delegates to `opencode` CLI if it has media commands. Returns `not_available` if no media support.

---

## 8. Renderer Design (`toll/engine/renderers/media_renderer.py`)

### 8.1 Preview Renderers

```python
class MediaPreviewRenderer:
    def image_preview(self, artifact: Artifact) -> str:
        """Full HTML page showing image + metadata card."""

    def audio_preview(self, artifact: Artifact) -> str:
        """HTML with <audio> player + waveform placeholder + metadata."""

    def video_preview(self, artifact: Artifact) -> str:
        """HTML with <video> player + controls + metadata."""
```

### 8.2 Integrated Previews

`image_preview` shows:
- The image at natural size (max 100% width)
- Below: metadata table (provider, model, seed, dimensions, prompt)
- Prompt displayed in a code block for review

`audio_preview` shows:
- `<audio>` element with controls (play, pause, seek, volume, download)
- Duration and format info
- Voice/style metadata if applicable

`video_preview` shows:
- `<video>` element with controls + poster frame
- Resolution, duration, codec info
- Download link

---

## 9. Artifact Model Changes

Add to `ArtifactType` enum in `toll/model/artifact.py`:

```python
class ArtifactType(str, Enum):
    # ... existing ...
    IMAGE_GEN = "image_gen"   # new (distinct from existing IMAGE which may be uploaded)
    AUDIO = "audio"           # new
    VIDEO = "video"           # new
```

**Rationale:** `IMAGE` already exists but represents uploaded/imported images. `IMAGE_GEN` represents AI-generated images with a prompt, model, and seed.

---

## 10. Enhanced Preview Renderer

The existing `PreviewRenderer` in `toll/engine/renderers/preview_renderer.py` needs three new methods:

```python
def image_gen_preview(self, artifact: Artifact) -> str: ...
def audio_preview(self, artifact: Artifact) -> str: ...
def video_preview(self, artifact: Artifact) -> str: ...
```

And `_summarize` needs three new branches for the JSON preview.

---

## 11. Feature Flags

Register 6 new flags in `toll/core/feature_flags.py`:

```python
# Media Layer — Sprint 6
"media_generation": False,       # master switch
"media_image": False,            # image generation
"media_audio": False,            # audio/TTS generation
"media_video": False,            # video generation
"provider_replicate": False,     # Replicate provider (may already exist)
"media_local_storage": True,     # filesystem storage for media
```

---

## 12. Handler Registration

In `toll/application/handler_registry.py`:

```python
if flags.is_enabled("media_generation"):
    svc = MediaService(artifact_service, selector, cm, flags)
    wf_engine.register_handler("media_generate", svc.execute)
```

---

## 13. Workflow Plan Schema

Plans accepted by the `media_generate` handler:

```json
{
    "intent": "media_generate",
    "media_type": "image",
    "prompt": "A serene mountain landscape at sunset, digital art",
    "size": "1024x1024",
    "model": "flux-schnell",
    "seed": 12345,
    "style": "digital-art",
    "negative_prompt": "blurry, low quality",
    "title": "Sunset Mountain"
}
```

Audio example:
```json
{
    "intent": "media_generate",
    "media_type": "audio",
    "prompt": "Generate a calm, meditative ambient soundscape with soft piano",
    "duration": 30,
    "model": "musicgen",
    "title": "Meditation Soundscape"
}
```

Video example:
```json
{
    "intent": "media_generate",
    "media_type": "video",
    "prompt": "A time-lapse of flowers blooming in a garden",
    "duration": 10,
    "size": "1920x1080",
    "model": "stable-video",
    "title": "Flower Bloom Timelapse"
}
```

---

## 14. Integration Points

### 14.1 Research → Media (Future Sprint)

Research artifacts can seed media generation:
- Research synopsis → TTS audio overview
- Key findings → social video clip

### 14.2 Carousel/Presentation → Media (Future Sprint)

- Carousel slides → animated video export
- Presentation → speaker audio overlay

### 14.3 NotebookLM → Media

- Notebook source → TTS audio
- Notebook notes → image generation for featured images

---

## 15. Edge Cases & Error Handling

| Scenario | Handling |
|----------|----------|
| Provider not available | `MediaResult(success=False, error="...")` → service returns `{"error": "..."}` |
| Generation timeout | Catch `asyncio.TimeoutError` or `subprocess.TimeoutExpired` → return error |
| File too large | Validate `file_size_bytes < max` in `FsMediaStorage.save()` |
| Unsupported media_type | `execute()` returns `{"error": "Unknown media_type"}` |
| Invalid dimensions | Clamp to provider-supported sizes (e.g., Replicate SDXL: 1024x1024, 1152x896, 1216x832) |
| Disk full | `FsMediaStorage.save()` catches `OSError` → returns error |
| Corrupted output | Provider returns success but bytes are 0 or invalid; service checks file size > 0 |

---

## 16. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Provider API changes | Medium | High | Port abstraction isolates impact to one adapter |
| Large media files fill disk | Low | Medium | Configurable max sizes, periodic cleanup job |
| Slow generation blocks workflow | High | Medium | Timeout per provider; future async support |
| Copyright from generated content | Low | Low | Prompts are user-provided; no training on copyrighted data |

---

## 17. Test Plan (18 tests)

### Unit Tests (12)

| # | Test | File |
|---|------|------|
| 1 | `MediaRequest` dataclass default values | `tests/ports/test_media.py` |
| 2 | `MediaResult` handles success path | `tests/ports/test_media.py` |
| 3 | `MediaResult` handles error path | `tests/ports/test_media.py` |
| 4 | `FsMediaStorage.save()` creates correct path | `tests/adapters/test_fs_storage.py` |
| 5 | `FsMediaStorage.get_path()` returns existing | `tests/adapters/test_fs_storage.py` |
| 6 | `FsMediaStorage.get_path()` returns None for missing | `tests/adapters/test_fs_storage.py` |
| 7 | `FsMediaStorage.delete()` removes file | `tests/adapters/test_fs_storage.py` |
| 8 | `ReplicateMediaAdapter.generate()` builds correct model map | `tests/adapters/test_media_replicate.py` |
| 9 | `ReplicateMediaAdapter.generate()` returns error on unsupported type | `tests/adapters/test_media_replicate.py` |
| 10 | `MediaService._generate_image()` creates artifact | `tests/application/test_media_service.py` |
| 11 | `MediaService._generate_audio()` falls back on missing provider | `tests/application/test_media_service.py` |
| 12 | `MediaService.execute()` dispatches by media_type | `tests/application/test_media_service.py` |

### Integration Tests (4)

| # | Test | File |
|---|------|------|
| 13 | Full image gen pipeline: plan → execute → artifact stored → media file exists | `tests/api/test_media_api.py` |
| 14 | No provider available returns error gracefully | `tests/api/test_media_api.py` |
| 15 | Feature flag gating: media not generated when flag disabled | `tests/api/test_media_api.py` |
| 16 | Media metadata persisted in SQLite after generation | `tests/api/test_media_api.py` |

### Preview Tests (2)

| # | Test | File |
|---|------|------|
| 17 | `image_preview` returns valid HTML with `<img>` tag | `tests/engine/test_media_renderer.py` |
| 18 | `audio_preview` returns valid HTML with `<audio>` tag | `tests/engine/test_media_renderer.py` |

---

## 18. Implementation Order (3 Phases)

### Phase 1 — Storage & Ports (Sprint Day 1–2)
1. `toll/ports/media.py` — `MediaRequest`, `MediaResult`, `MediaPort`
2. `toll/ports/media_storage.py` — `MediaStorage` abstract
3. `toll/adapters/media/fs_storage.py` — filesystem implementation
4. `toll/model/migrations/0010_media.sql` — `media_meta` + `media_resources`
5. `toll/model/artifact.py` — add `IMAGE_GEN`, `AUDIO`, `VIDEO` to enum
6. Tests for storage + ports

### Phase 2 — Adapters & Service (Sprint Day 3–4)
7. `toll/adapters/media/replicate.py` — Replicate adapter
8. `toll/adapters/media/ollama.py` — Ollama stub adapter
9. `toll/adapters/media/opencode.py` — OpenCode adapter
10. `toll/application/media_service.py` — `MediaService` with all three generators
11. `toll/core/feature_flags.py` — register 6 flags
12. `toll/application/handler_registry.py` — register handler
13. Tests for adapters + service

### Phase 3 — Renderers & Polish (Sprint Day 5)
14. `toll/engine/renderers/media_renderer.py` — image/audio/video previews
15. `PreviewRenderer.image_gen_preview()` + `audio_preview()` + `video_preview()` + updated `_summarize`
16. Full integration tests
17. Edge case hardening (timeouts, disk full, invalid output)

---

## 19. Future Considerations (Post-Sprint 6)

- **Async/Webhook support** — for long-running video generation, return a `job_id` and poll
- **Streaming** — chunked delivery for large audio/video files
- **Multi-modal prompts** — image generation from text + reference image
- **Batch generation** — generate N images from a prompt in one call
- **Upload support** — user-uploaded media imported as artifacts
- **CDN/s3 storage** — optional cloud storage for media files
- **Media gallery** — web UI to browse generated images/audio/video
- **Image editing** — inpainting, outpainting, style transfer via adapter
- **Video editing** — concatenate clips, add transitions, overlay text
