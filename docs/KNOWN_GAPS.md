# Known Architectural Gaps

> **Last Updated**: Sprint 7B (v0.7b-prompt-intelligence-integration)
>
> This document tracks all known gaps between the current platform state and the
> VISION.md goals. Gaps are organized by priority.

---

## High Priority

### 1. Prompt Learning Loop Incomplete

PromptMemory infrastructure exists (record_success, record_failure, blacklist,
avg_scores) but success/failure feedback hooks are not wired into service flows.

- **What's missing**: After each generation in ResearchService, ReportService,
  PresentationService, and MediaService, call prompt_memory.record_success() or
  record_failure() with the profile_id, model_id, and score.
- **Impact**: The learning loop is manual. Blacklist is active but never
  populated. Scores are never recorded. Profile tuning cannot happen.
- **Target Sprint**: 7C

### 2. PromptMemory `get_avg_score()` Not Consumed in Engine

The engine has `get_avg_score()` available on PromptMemory but never calls it
during model selection.

- **What's missing**: In `_select_model()`, use `get_avg_score()` as a weight
  when ranking candidates — prefer models with higher average scores for the
  same profile.
- **Impact**: Model selection ignores historical quality data. Blacklist is
  the only memory signal used.
- **Target Sprint**: 7C

### 3. Usage Tracking Missing

No per-provider, per-user, or per-endpoint usage tracking exists.

- **What's missing**: A UsageService that records every generation request,
  tracks daily/monthly quotas, and provides a usage history API.
- **Impact**: No cost awareness. No quota enforcement. No analytics for
  provider performance comparison.
- **Target Sprint**: 8

---

## Medium Priority

### 4. Provider Dashboard Missing

No visual dashboard for provider performance, benchmark results, or cost
comparison.

- **What's missing**: UI views for ProviderSelector ranking, benchmark suite
  results, per-model quality/latency/cost breakdown.
- **Impact**: Users cannot compare providers or see benchmark-driven
  recommendations.
- **Target Sprint**: 8

### 5. Caching Layer Missing

No prompt-to-artifact cache exists. Identical requests regenerate from scratch.

- **What's missing**: A CacheService that hashes prompt+params+model and
  returns previously generated artifacts when identical requests are made.
- **Impact**: Redundant generation for repeated prompts. Higher API costs and
  latency.
- **Target Sprint**: 8

### 6. Cost Monitoring Missing

No per-provider, per-profile, or per-generation cost tracking exists.

- **What's missing**: Cost recording in the generation pipeline — capture
  model cost_per_unit, actual cost per generation, accumulate per session.
- **Impact**: No budget awareness. Hard to compare provider cost efficiency.
- **Target Sprint**: 8

### 7. Model-Aware Prompt Adaptation Not Implemented

The Sprint 7 design specified ModelPromptRules per model family (Flux, SDXL,
DALL-E, Veo, Runway, Kling) but this was deferred from Sprint 7B.

- **What's missing**: A ModelPromptRules table + prompt transformers that
  adapt generated prompts per model family (size constraints, parameter
  mapping, language preferences).
- **Impact**: Prompts are generated via template without model-specific
  optimization. Flux prompts work but may not be optimal for SDXL or DALL-E.
- **Target Sprint**: 7B (deferred — no target set)

---

## Low Priority

### 8. Video Generation Incomplete

Video media type exists in ArtifactType enum and MediaPort interface, but no
video adapter is implemented.

- **What's missing**: Veo, Runway, or Kling adapter that implements MediaPort
  for video generation. enable_media_video flag exists but has no effect.
- **Impact**: Video generation feature is entirely unavailable.
- **Target Sprint**: 9

### 9. Audio Generation Incomplete

No audio/TTS generation exists.

- **What's missing**: AudioPort, adapters (ElevenLabs, Kokoro), audio pipeline
  in MediaService.
- **Impact**: No voiceover, no audio overview generation.
- **Target Sprint**: 9

### 10. Automation Layer Missing

No scheduled tasks, auto-retry, event-driven workflows, or webhook triggers.

- **What's missing**: A scheduler service that can trigger workflows at
  intervals or on events. Auto-retry logic on generation failure.
- **Impact**: All workflows require manual triggering. Batch/recurring tasks
  are not possible.
- **Target Sprint**: 9+

### 11. Multi-User Support Missing

No authentication, isolated workspaces, or shared resources.

- **What's missing**: Auth system (login, API keys), tenant isolation,
  shared workspace support.
- **Impact**: Platform is single-user only. Cannot be deployed as a team
  service.
- **Target Sprint**: 10+

### 12. No End-to-End Integration Tests

Tests cover individual components and API endpoints but no full lifecycle
test (User -> Planner -> PIE -> Service -> Adapter -> Artifact).

- **What's missing**: Integration test that sends a chat message, follows the
  full workflow, and verifies artifact creation.
- **Impact**: Regressions in cross-component interactions may not be caught.
- **Target Sprint**: 8
