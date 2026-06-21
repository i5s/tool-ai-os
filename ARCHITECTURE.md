TOOL (تول) - Architecture Document
==================================

Architecture Principles
-----------------------

1. Local First
2. Modular Design
3. Feature Flags
4. Memory-Centric Architecture
5. Planner-Driven Workflows
6. Extensible Provider Layer

Layer 1: Core Layer
===================

These components are mandatory and always enabled.

Planner
-------

Responsible for:

* Intent understanding
* Task decomposition
* Workflow planning
* Provider selection

Workflow Engine
---------------

Responsible for:

* Progress tracking
* Execution stages
* Status updates
* Approval checkpoints

Memory Graph
------------

Main memory system.

Contains:

* Global Memory
* Brand Memory
* Study Memory
* Project Memory

Provider Layer
--------------

Provider abstraction layer.

Supported modes:

### Native

Examples:

* OpenCode
* OpenDesign

### API

Examples:

* OpenAI
* Claude
* Gemini

### Browser

Examples:

* Services without APIs

Storage Manager
---------------

Responsible for:

* File organization
* Folder structure
* Retention policies
* Archive management

Settings System
---------------

Centralized configuration management.

Request Lifecycle (Sprint 7B)
=============================

User Input
    |
    v
Planner
    |
    v
Prompt Intelligence Engine
    |
    v
Execution Profile
    |
    v
Provider Selector (benchmark-aware)
    |
    v
Service (Research / Report / Presentation / Media)
    |
    v
Adapter (OpenCode / Replicate / Ollama / etc.)
    |
    v
Artifact (stored + rendered)

All four generation services now route through Prompt Intelligence when the
`prompt_intelligence` feature flag is enabled (default: False). When disabled,
the system falls back to the pre-Sprint 7A direct path:

User -> Service -> Adapter -> Artifact

### Prompt Intelligence Layer

| Component | File | Status |
|-----------|------|--------|
| PromptIntelligenceEngine | `toll/prompt/engine.py` | Production |
| PromptProfileRepository | `toll/prompt/repository.py` | Production |
| PromptProfileService | `toll/prompt/profile_service.py` | Production |
| PromptMemory | `toll/prompt/memory.py` | Production (blacklist active, recording ready) |
| ExecutionProfileRepository | `toll/prompt/execution_profile.py` | Production |
| Seed Profiles (10) | `toll/prompt/profiles.py` | Production |
| API Router | `api/routers/prompt.py` | Production |
| Migration 0012 | `toll/model/migrations/0012_prompt_intelligence.sql` | Production |

### Execution Profiles (6)

| Profile | Sub-Profiles | Default Media |
|---------|-------------|---------------|
| Research | research_report, academic_report, literature_review | text |
| Academic Report | academic_report, citation_paper, thesis_section | text |
| Marketing | product_ad, social_media, brand_copy, seo_content | image/text |
| Product Advertisement | product_ad, food_photography, packaging_design | image |
| Presentation | presentation, slide_deck, pitch_deck | text |
| Video Generation | video_ad, video_presentation, short_form_video | video |

### Benchmark-Aware Provider Selection

ProviderSelector._quality_score() now supports a benchmark-aware path:

1. If `benchmark_auto_quality` flag is enabled AND `BenchmarkRepository`
   has data for the provider, use `avg_quality_auto` from benchmark runs.
2. Otherwise, fall back to static quality scores.

This closes the gap between the Benchmark Lab (Sprint 6A) and Provider
Selection (Sprint 7B).

### PromptMemory

PromptMemory provides:

* `record_success()` - records a successful generation with score
* `record_failure()` - adds a model+profile pair to the blacklist
* `is_blacklisted()` - checks if a model is blacklisted for a profile
  (active in production - filters model selection)
* `get_avg_score()` - retrieves average quality score per profile/model
* `get_consecutive_failures()` - counts recent consecutive failures

Blacklist consumption is active: `PromptIntelligenceEngine._select_model()`
filters out blacklisted models from the model registry results.

Layer 2: Dormant Features
==========================

Implemented but disabled by default.

Preference Memory
-----------------

Learns user preferences over time.

Feature Flag: preference_memory=false

Knowledge Vault
---------------

Stores long-term structured knowledge.

Feature Flag: knowledge_vault=false

Artifact System
---------------

Stores generated outputs.

Examples:

* Reports
* Presentations
* Carousels
* Designs
* Code

Feature Flag: artifact_system=false

Google Drive Sync
-----------------

Backup and archive system.

Feature Flag: google_drive_sync=false

Telegram Integration
--------------------

Optional communication channel.

Feature Flag: telegram_enabled=false

Task Journal
------------

Execution history and analytics.

Feature Flag: task_journal=false

Health Dashboard
----------------

System monitoring.

Feature Flag: health_dashboard=false

Self Improvement Queue
----------------------

Stores system improvement suggestions.

Feature Flag: self_improvement=false

User System
-----------

Future-ready user architecture.

Feature Flag: users_enabled=false

Layer 3: Future Layer
=====================

Not implemented in V1.

* Teams
* Billing
* Marketplace
* MCP
* Cloud Sync
* Multi-Tenant SaaS

Data Structure
==============

Memory Graph

Global Memory -> Preferences -> Brands -> University -> Projects -> Knowledge Vault

File Structure
==============

Data/

Brands/University/Projects/Artifacts/Archive/

Retention Policy
================

Supported modes:

* Never Delete
* 30 Days
* 60 Days
* 90 Days
* 180 Days

Archive before deletion.

Approval Workflow
=================

Discuss -> Plan -> Approve -> Execute -> Learn

This workflow is mandatory for major tasks.

Development Rule
================

OpenCode must never implement features outside the approved sprint plan.

All development must follow:

Architecture -> TODO -> Sprint -> Implementation
