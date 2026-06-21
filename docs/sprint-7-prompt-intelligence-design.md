# Sprint 7 — Prompt Intelligence Engine — Design Review

> **Status**: Approved — Sprint 7A in progress  
> **After**: Sprint 6A (v0.6-media-foundation)  
> **Architectural Addition**: Execution Profiles (Section 1.5)

---

## 1. Prompt Intelligence Engine

### Responsibilities

| Responsibility | Description |
|---|---|
| **Intent Resolution** | Parse raw user input into a structured intent object (type, subject, tone, constraints) |
| **Context Assembly** | Gather workspace state, active brand/university/semester, active conversation history, memory graph signals |
| **Profile Matching** | Match intent to a `PromptProfile` (product ad, food photo, research report, etc.) |
| **Model Selection Input** | Feed context + media type to `ProviderSelector` + `ModelRegistryService.find_best()` with benchmark scores as weights |
| **Prompt Generation** | Assemble a model-specific prompt using the matched profile, context data, and model constraints |
| **Output** | Return a `PromptPackage` containing the final prompt string, metadata (model, profile, version), and optional debug info |

### Inputs

| Input | Source | Notes |
|---|---|---|
| User text | Chat input / workflow params | Raw Arabic or English string |
| Workspace context | `ContextEngine` via `toll/context/engine.py` | Active brand, university, semester, project IDs |
| Memory signals | `MemoryGraph` via `toll/memory/graph.py` | Recent high-importance memories, user preferences |
| Research memory | `MemoryService` via `toll/research/memory_service.py` | Auto-indexed knowledge vault entries |
| Brand style data | Workspace metadata | Color palette, tone, audience — stored in workspace extras |
| Benchmark scores | `BenchmarkRepository.avg_scores()` | Quality/latency/cost per model for the target media type |
| Active profile | `PromptProfile` from profile registry | Templates and config per use case |

### Outputs

| Field | Type | Example |
|---|---|---|
| `final_prompt` | `str` | The fully rendered prompt string |
| `model_id` | `str` | `"replicate:flux-schnell"` |
| `profile_id` | `str` | `"product_ad"` |
| `prompt_version` | `int` | `3` |
| `params` | `dict` | Extra generation params (seed, size, negative_prompt, style) |
| `debug_info` | `dict` | Profile used, model selected, benchmark score, context size |

The engine itself is a stateless coordinator — it delegates to existing systems and does no persistence of its own.

---

## 1.5 Execution Profiles

An **Execution Profile** is a user-facing mode that groups related `PromptProfile`s under a single conceptual label. Users select an Execution Profile (e.g. "Marketing") and the engine automatically routes to the appropriate Prompt Profile based on intent.

### Execution Profile Catalogue

| Profile | Sub-Profiles (Prompt Profiles) | Default Media Type |
|---|---|---|
| **Research** | `research_report`, `academic_report`, `literature_review` | `text` |
| **Academic Report** | `academic_report`, `citation_paper`, `thesis_section` | `text` |
| **Marketing** | `product_ad`, `social_media`, `brand_copy`, `seo_content` | `image` / `text` |
| **Product Advertisement** | `product_ad`, `food_photography`, `packaging_design` | `image` |
| **Presentation** | `presentation`, `slide_deck`, `pitch_deck` | `text` |
| **Video Generation** | `video_ad`, `video_presentation`, `short_form_video` | `video` |

### Execution Profile Schema

```python
@dataclass
class ExecutionProfile:
    id: str                       # "marketing"
    name: str                     # "Marketing Profile"
    description: str              # "Social media posts, ads, brand content"
    sub_profiles: list[str]       # ["product_ad", "social_media", "brand_copy"]
    default_media_type: str       # "image"
    icon: str                     # "📢" (for UI)
```

### Layer Position

```
User selects Execution Profile (e.g. "Marketing")
    │
    ▼
ExecutionProfile resolves to PromptProfile based on intent
    │
    ▼
PromptIntelligenceEngine generates model-specific prompt
    │
    ▼
Handler → Adapter → Artifact
```

Execution Profiles are the outermost layer — users interact with them, never with Prompt Profiles directly (unless in Advanced mode). When `prompt_intelligence` is disabled, Execution Profiles are ignored.

---

## 2. Prompt Profiles

A `PromptProfile` is a config bundle that maps an intent to a prompt template and model constraints.

### Profile Registry (initial catalogue)

| Profile ID | Intent Trigger | Media Type | Example Input |
|---|---|---|---|
| `product_ad` | Advertising / product promotion | `image` | "ابا اعلان حليب فاخر" |
| `food_photography` | Food / drink visuals | `image` | "تصوير كيكة شوكولاتة فاخرة" |
| `travel_poster` | Travel / destination | `image` | "ملصق سياحي لمدينة جدة" |
| `social_media` | Social post / story | `image` | "بوست انستقرام عطر" |
| `research_report` | Academic / research | `text` | "بحث عن الذكاء الاصطناعي" |
| `presentation` | Slide deck | `text` | "عرض تقديمي عن التسويق" |
| `video_ad` | Video commercial | `video` | "فيديو اعلاني لسيارة" |
| `ui_design` | App / website UI | `image` | "تصميم واجهة تطبيق" |
| `logo_design` | Brand logo | `image` | "شعار لمتجر الكتروني" |

### Profile Schema

```python
@dataclass
class PromptProfile:
    id: str                       # "product_ad"
    name: str                     # "Product Advertisement"
    media_types: list[str]        # ["image"]
    template: str                 # Jinja2-compatible prompt template
    default_params: dict          # { "size": "1024x1024", "seed": null }
    compatible_models: list[str]  # model family filters: ["flux", "sdxl"]
    weight_criteria: dict         # benchmark weight overrides: { "quality": 0.7, "latency": 0.3 }
    tags: list[str]               # ["advertising", "product"]
```

### Storage Strategy

Prompt profiles live in the **Model Registry database** in a new `prompt_profiles` table. They are seeded on first init (like seed models) and can be extended via the API. They are NOT hardcoded — users/admins can create custom profiles.

A smaller set of "system profiles" is shipped as code in `toll/prompt/profiles.py` for the core use cases.

---

## 3. Prompt Memory

### Learning from Success

When an artifact is created via the Prompt Intelligence Engine and the user:
- Does **not** regenerate → the prompt scored positively (implicit signal)
- Rates it up / marks as favorite → explicit positive signal (future)

Each successful generation records:
- The `PromptProfile` used
- The model ID + parameters
- The final prompt string
- The resulting artifact's `file_size_bytes`, `content_type`, and (if benchmark-enabled) auto-quality score

This data feeds into:
- **Profile ranking** — which profile works best for which model
- **Model ranking** — which model produces highest quality for this profile type
- **Parameter tuning** — which size/seed/negative_prompt combos correlate with success

### Avoiding Failure

Failed generations are tracked in the existing `benchmark_runs` table (via `BenchmarkRunner`). When a model+profile pair has >2 consecutive failures (error, timeout, 0-byte output), the engine:
1. Falls back to the next-best model for that profile
2. Flags the pair in a `prompt_blacklist` table
3. Logs the failure for review

### Benchmark Influence

The `ProviderSelector._quality_score()` method (currently static) is updated to consume `BenchmarkRepository.avg_scores(model_id)`. When benchmark data exists:
- `quality_score` = weighted average of `avg_quality_auto`, inverted `avg_latency_ms`, and inverted `avg_cost_cents`
- Each `PromptProfile` can override these weights via `weight_criteria`

When no benchmark data exists, the engine falls back to the current static scores.

---

## 4. Model Awareness

Different models require different prompt structures. The engine must know how to adapt prompts per model.

| Model | Family | Prompt Style | Key Constraints |
|---|---|---|---|
| `replicate:flux-schnell` | Flux | Short descriptive prompt, prefers English, sensitive to negative prompts | Max 512 chars, `aspect_ratio` param, no `negative_prompt` in some versions |
| `replicate:flux-pro` | Flux | Longer prompts, supports style references, good with Arabic prompt + English style | `output_format`, `guidance_scale`, `interval` params |
| `replicate:sdxl` | SDXL | Structured prompt + negative prompt, prefers `(keyword:weight)` syntax | `width/height` in multiples of 64, `cfg_scale`, `clip_skip` params |
| `openai:dall-e-3` | DALL-E | Natural language prompt, no negative prompt, good with Arabic | Max 4000 chars, `quality` param ("hd"), `style` ("vivid"/"natural"), size must be `1024x1024` |
| `veo:*` (future) | Veo | Video description, camera motion, lighting direction | `duration_seconds`, `fps`, `camera_motion` params |
| `runway:*` (future) | Runway | Scene description, style reference, motion intensity | `prompt_strength`, `motion_bucket_id`, `seed` params |
| `kling:*` (future) | Kling | Short action-focused prompt, prefers English, camera motion | `duration`, `motion_type`, `cfg_scale` params |

### Implementation

A `ModelAdapter` registry maps model families to prompt transformers:

```python
@dataclass
class ModelPromptRules:
    family: str
    max_prompt_length: int
    supports_negative_prompt: bool
    supports_seed: bool
    size_constraints: dict       # { "multiples_of": 64, "allowed": ["1024x1024", ...] }
    style_augmentation: str      # "append_to_prompt" | "separate_param" | "none"
    preferred_language: str      # "en" | "ar" | "auto"
```

A small set of transformer functions adapt the generated prompt and params to the target model's rules, clipping, converting, or dropping unsupported features.

---

## 5. Workflow Integration

```
User
  │
  ▼
Chat Input / Workflow Params
  │
  ▼
Planner (toll/planner/)
  ├─ Resolves intent (25 types)
  ├─ Checks approval matrix
  └─ Calls handler via WorkflowEngine
       │
       ▼
  Handler (e.g. "media_generate")
       │
       ▼
  Prompt Intelligence Engine (NEW)
       ├─ 1. Intent Resolution
       ├─ 2. Context Assembly (ContextEngine, MemoryGraph, ResearchMemory)
       ├─ 3. Profile Matching (PromptProfile registry)
       ├─ 4. Model Selection (ProviderSelector + BenchmarkRepository)
       ├─ 5. Prompt Generation (template + model-aware transformation)
       └─ 6. Return PromptPackage
            │
            ▼
  MediaService / ReportService / CarouselService
       │
       ▼
  Adapter (Replicate / OpenCode / etc.)
       │
       ▼
  ArtifactService → Artifact stored with PromptPackage metadata
```

### Key Integration Points

1. **New handler** `"prompt_intelligence"` registered in `HandlerRegistry` — wraps the existing `media_generate`, `research`, `report`, `presentation`, `carousel` handlers
2. **Planner already has intent resolution** — the PIE reads the resolved intent from the workflow params (no duplicated intent detection)
3. **ProviderSelector already has scoring** — PIE feeds it benchmark weights
4. **ArtifactService already stores artifacts** — PIE attaches `prompt_profile`, `prompt_version`, `final_prompt` to artifact content

The PIE is an optional layer — it wraps existing handlers. When disabled (flag `prompt_intelligence = False`), the system behaves exactly as before.

---

## 6. Prompt Evolution

### Versioning

Each `PromptProfile` has a `version` field (incremented on edit). Prompts generated with version N are recorded in the artifact metadata.

A `prompt_profile_versions` table tracks the full history:
- `profile_id`, `version`, `template` (the template at that version), `default_params`, `changed_by`, `changed_at`

### Scoring

Each generated prompt gets a score derived from:
- **User signal**: Did the user keep the result? (implicit: not regenerated within 60s = positive)
- **Benchmark quality**: If auto-quality is enabled, the `QualityScorer` score
- **Artifact metrics**: file_size_bytes, content_type compliance

These scores feed a `prompt_scores` table (model_id, profile_id, score, prompt_hash, created_at).

### Feedback Loop

```
Prompt → Generation → Artifact → Score → Profile Template Tuning
```

1. Engine generates prompt from profile template
2. Adapter produces artifact
3. Score is recorded
4. If avg_score for profile drops below threshold (e.g. <0.6 over 10 runs), the profile is flagged for review
5. Admin can examine failing prompts and adjust the profile template

This is a **manual** feedback loop (engine flags, human adjusts). Automatic template mutation is explicitly deferred.

---

## 7. Database Impact

### New Tables

| Table | Columns | Purpose |
|---|---|---|
| `prompt_profiles` | `id`, `name`, `media_types`, `template`, `default_params`, `compatible_models`, `weight_criteria`, `tags`, `version`, `created_at`, `updated_at` | Prompt profile registry |
| `prompt_profile_versions` | `id`, `profile_id`, `version`, `template`, `default_params`, `changed_by`, `changed_at` | Profile version history |
| `prompt_scores` | `id`, `profile_id`, `model_id`, `score`, `prompt_hash`, `artifact_id` (FK → artifacts), `created_at` | Per-generation prompt quality scores |
| `prompt_blacklist` | `model_id`, `profile_id`, `reason`, `flagged_at` | Model+profile pairs with repeated failures |
| `model_prompt_rules` | `family`, `max_prompt_length`, `supports_negative_prompt`, `supports_seed`, `size_constraints`, `style_augmentation`, `preferred_language` | Per-model-family prompt adaptation rules |

### New Indexes

- `idx_prompt_scores_profile` on `prompt_scores(profile_id)`
- `idx_prompt_scores_model` on `prompt_scores(model_id)`
- `idx_prompt_blacklist_lookup` on `prompt_blacklist(model_id, profile_id)`
- `idx_prompt_profiles_types` on `prompt_profiles(media_types)`

### New Memory Types (MemoryGraph)

No new memory graph types needed. The existing 5 types (global, brand, university, project, knowledge) + the research memory knowledge vault provide sufficient context. However, the `MemoryGraph.retrieve_context()` call during context assembly should include:
- Recent high-importance memories (importance > 7)
- Memories tagged with the active brand/project ID
- Research memory vault entries matching the user's prompt keywords

### Migration

`0012_prompt_intelligence.sql` — 5 tables + 4 indexes.

---

## 8. UI Design

### Prompt Visibility Modes

The ZUNO UI shows a toggle in the header (near the model selector):

| Mode | Behavior | Default |
|---|---|---|
| **Hidden** | Prompt is invisible to the user. Artifact appears as if generated directly. | ✅ User-facing production |
| **Preview** | Before generation, a small collapsible panel shows the generated prompt (Arabic+English) with an "Edit" button. User can tweak and regenerate. | Power users |
| **Advanced** | Full prompt engineering view — shows profile, model, params, benchmark scores, template variables. User can edit the template, switch model, adjust weights. | Administrators / prompt engineers |

### UI Components

1. **Prompt toggle** — 3-state switch in the header bar
2. **Prompt panel** — collapsible drawer between header and messages, showing:
   - Prompt text (editable in Preview/Advanced modes)
   - Model badge (name + quality score)
   - Profile badge
   - "Regenerate with edits" button
   - "View prompt details" expandable section (Advanced mode only)
3. **Profile management page** — accessible from sidebar (Settings → Prompt Profiles):
   - List of profiles with version, last used, avg score
   - Profile editor (template, params, compatible models)
   - Score history chart

The existing ZUNO sidebar layout supports adding a "Prompt Profiles" nav item under "Settings" submenu.

---

## 9. Sprint Breakdown

### Sprint 7A — Core Engine + Profiles (Estimated: 5-7 days)

**Deliverables**:
- `toll/prompt/engine.py` — `PromptIntelligenceEngine` class (intent → profile → prompt)
- `toll/prompt/profiles.py` — Seed profiles (product_ad, food_photography, travel_poster, social_media, research_report, presentation, video_ad, ui_design, logo_design)
- `toll/prompt/repository.py` — `PromptProfileRepository` (CRUD + versioning)
- `toll/prompt/profile_service.py` — `PromptProfileService` (list, get, create, update profile)
- Migration `0012_prompt_intelligence.sql` — `prompt_profiles`, `prompt_profile_versions` tables
- API: `GET/POST /api/prompt/profiles`, `GET/PUT /api/prompt/profiles/{id}`
- Handler: `"prompt_intelligence"` wraps existing handlers
- Feature flags: `prompt_intelligence` (default False), `prompt_intelligence_preview` (default True)
- 25 new tests

**Risks**:
- Template rendering complexity (Jinja2 dependency, or lightweight custom templating)
- Arabic prompt quality with English-dominant models (Flux/SDXL)

**Files**: ~12 new, ~4 modified

---

### Sprint 7B — Model Awareness + Benchmark Integration (Estimated: 5-7 days)

**Deliverables**:
- `toll/prompt/model_rules.py` — `ModelPromptRules` registry per model family
- Prompt transformers for Flux, SDXL, DALL-E, Veo, Runway, Kling
- `model_prompt_rules` table + seed data
- `ProviderSelector` update: consume `BenchmarkRepository.avg_scores()` for dynamic quality scores
- `PromptProfile.weight_criteria` — benchmark weight overrides per profile
- Prompt memory: `prompt_scores` table, `prompt_blacklist` table
- Fallback logic for model+profile failure pairs
- API: `GET /api/prompt/models/rules`, `GET /api/prompt/profiles/{id}/scores`
- Feature flag: `prompt_intelligence_benchmark` (default False)
- 25 new tests

**Risks**:
- Benchmark data sparsity — most models won't have runs recorded
- Model family detection (registry model_id → family mapping)

**Files**: ~8 new, ~6 modified

---

### Sprint 7C — UI + Polish (Estimated: 4-6 days)

**Deliverables**:
- Prompt visibility toggle in ZUNO header (Hidden / Preview / Advanced)
- Collapsible prompt panel in chat view
- Prompt profile management page
- Score history chart (Chart.js mini line chart)
- Edit-and-regenerate flow in Preview/Advanced modes
- Context assembly integration: `ContextEngine`, `MemoryGraph`, `ResearchMemory` → prompt template variables
- End-to-end test: user input → engine → handler → artifact
- Feature flag: `prompt_intelligence_advanced` (default False)
- 15 new tests

**Risks**:
- UI complexity for Advanced mode (template editor requires code-editing UX)
- Context assembly latency (multiple DB queries before generation)

**Files**: ~4 new, ~3 modified

---

### Total Sprint 7 Estimate

| | Files | Tests | Risk |
|---|---|---|---|
| Sprint 7A | ~16 | 25 | Medium |
| Sprint 7B | ~14 | 25 | Medium |
| Sprint 7C | ~7 | 15 | Low |
| **Total** | **~37** | **65** | |

---

## 10. Future Vision — ZUNO Agent

The Prompt Intelligence Engine is the first step toward a fully autonomous **ZUNO Agent** that:

1. **Receives fuzzy intent** — "اعلان حليب", "تصميم واجهة", "ابحث لي عن..." in Arabic, English, or mixed
2. **Resolves all ambiguity** using workspace context, memory graph, brand style, user history, and benchmark data
3. **Selects the optimal tool** — media generation, research, report, presentation, carousel, or code — without the user specifying
4. **Generates artifacts autonomously** — from prompt to finished deliverable in one step
5. **Learns from every interaction** — what the user kept, what they edited, what they rejected

### Evolution Stages

| Stage | Capability | Sprint |
|---|---|---|
| **Stage 1** | Prompt Intelligence Engine (profiles + model awareness) | Sprint 7 |
| **Stage 2** | Automatic tool selection (Planner enhancement: intent → tool without explicit handler) | Sprint 8 |
| **Stage 3** | Multi-step workflows (user says "اعلان حليب فاخر وقاعدة بيانات للعملاء", engine runs two parallel pipelines) | Sprint 9 |
| **Stage 4** | Autonomous refinement (engine generates, presents, user tweaks, engine regenerates — all within one conversation) | Sprint 10 |

### ZUNO Agent Architecture (Future)

```
User Input
    │
    ▼
┌─────────────────────────────────────────────┐
│  ZUNO Agent                                  │
│                                              │
│  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Intent Router │→ │ Prompt Intelligence  │  │
│  │ (Planner+)    │  │ Engine               │  │
│  └──────────────┘  └──────────┬───────────┘  │
│         │                     │              │
│         ▼                     ▼              │
│  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Context       │  │ Provider Selector    │  │
│  │ Assembly      │  │ (benchmark-driven)   │  │
│  └──────────────┘  └──────────┬───────────┘  │
│         │                     │              │
│         └─────────┬───────────┘              │
│                   ▼                          │
│  ┌──────────────────────────────────────┐    │
│  │ Execution (Handler → Adapter →       │    │
│  │           Artifact)                  │    │
│  └──────────────────────────────────────┘    │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │ Feedback Loop (Score → Profile →     │    │
│  │           Template Tuning)           │    │
│  └──────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

The key architectural insight: **all existing systems remain**. The ZUNO Agent is a thin orchestration layer on top — it delegates to Planner, Prompt Intelligence Engine, Provider Selector, and existing handlers. No existing code is rewritten.

---

## Design Decisions Summary

| Decision | Rationale |
|---|---|
| PIE is an **optional wrapper**, not a replacement | When disabled (`prompt_intelligence = False`), existing handlers work unchanged |
| Profiles are **DB-backed with code seed**, not hardcoded | Users can create custom profiles without modifying source code |
| Benchmark integration is **opt-in** (`prompt_intelligence_benchmark` flag) | Avoids requiring benchmark runs before basic prompt intelligence works |
| Template engine is **lightweight string formatting** (Python f-strings or Jinja2 evaluated as simple `.replace()`) | Avoids Jinja2 dependency; templates use `{variable}` syntax, resolved via simple string replacement |
| Prompt memory is **implicit** (artifact kept = positive) + **explicit** (ratings) | Implicit signals require no extra UI work; explicit ratings can be added later |
| Model prompt rules are **DB-backed** (seed data, no hardcoding) | Adding a new model family requires only a DB insert, not code changes |
| No automatic template mutation | Manual review before template changes reduces risk of quality regression |
| Context assembly queries are **time-budgeted** (max 500ms) | Prevents slow context retrieval from delaying generation |
