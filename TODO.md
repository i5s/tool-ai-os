# TOOL Implementation Backlog

## Sprint 0: Foundation — IN PROGRESS

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T1 | Feature flag framework | ✅ Done | `toll/core/feature_flags.py` |
| T2 | Fix `pyproject.toml` dependencies | ✅ Done | Added playwright, pinned versions, dev deps |
| T3 | Add pytest and test structure | ✅ Done | `tests/` with fixtures |
| T4 | Remove `sys.path` hacks | ✅ Done | Package installed editable |
| T28 | Restrict CORS | ✅ Done | Local origins only, env override |

## Sprint 1: Core Infrastructure

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T5 | Add database migration system | ⬜ Pending | |
| T6 | Define ports and adapters | ⬜ Pending | |
| T10 | Refactor Provider Layer | ⬜ Pending | |
| T11 | Fix or replace BrowserAI | ⬜ Pending | |
| T12 | Wire Settings System | ⬜ Pending | |

## Sprint 2: Memory Graph + Workspace Manager

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T9 | Memory Graph v1 | ⬜ Pending | Include importance_score |
| T33 | Workspace Manager | ⬜ Pending | Brand/University/Project only |
| T34 | Workspace API endpoints | ⬜ Pending | |
| T35 | Workspace UI in dashboard | ⬜ Pending | Global sidebar selector |

## Sprint 3: Context Engine + Planner + Workflow Engine

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T36 | Context Engine | ⬜ Pending | Summarized context |
| T7 | Planner v1 | ⬜ Pending | Approval rules |
| T8 | Workflow Engine | ⬜ Pending | Approval checkpoints |
| T37 | Plan/approval UI | ⬜ Pending | |

## Sprint 4: Application Services

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T13 | Create `toll/application/` services | ⬜ Pending | |
| T14 | Refactor API router | ⬜ Pending | |
| T15 | Refactor CLI | ⬜ Pending | |
| T16 | Refactor Telegram bot | ⬜ Pending | |

## Sprint 5: Artifact System

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T17 | AI-populated reports | ⬜ Pending | |
| T18 | AI-populated presentations | ⬜ Pending | |
| T19 | AI-populated carousels | ⬜ Pending | |
| T20 | Artifact System | ⬜ Pending | |
| T21 | Link artifacts to Memory Graph | ⬜ Pending | |

## Sprint 6: Web Dashboard Evolution

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T22 | Server-side conversations | ⬜ Pending | |
| T23 | Multi-turn context | ⬜ Pending | |
| T25 | Memory sidebar sections | ⬜ Pending | |
| T26 | Image analysis | ⬜ Pending | |
| T27 | Offline PWA caching | ⬜ Pending | |

## Sprint 7: Hardening

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T29 | Input validation | ⬜ Pending | |
| T30 | API key auth (flagged) | ⬜ Pending | |
| T31 | Update SKILL.md | ⬜ Pending | |
| T32 | Architecture Decision Records | ⬜ Pending | |
