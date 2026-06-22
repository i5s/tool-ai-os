# Agent Registry — Implementation

> **Sprint**: X — Architecture Foundation  
> **Status**: Implemented and committed in Sprint X.  
> **Principle**: Single source of truth for every agent instance the runtime may dispatch.

---

## 1. Purpose

The Agent Registry is the **control plane** for the multi-agent runtime. It knows:

* which agents exist,
* what each agent can do (role, rank),
* which provider backs it,
* whether it is currently active, disabled, or experimental,
* quality and reputation scores for intelligent dispatching.

No runtime component should start an agent without consulting the registry first.

---

## 2. Agent Model

```text
Agent
  id: str                    # UUID
  name: str                  # Human-readable name
  role: str                  # architect | developer | designer | researcher | reviewer | custom
  rank: str                  # leader | deputy | advisor | worker
  status: str                # active | disabled | experimental
  provider: str              # e.g. "Standard", "Local", "OpenCode"
  model: str                 # e.g. "hermes-runtime", "opencode-runtime"
  cost_tier: str             # "standard" | "local" | custom
  reputation_score: float    # 0.0–1.0, overall trustworthiness
  quality_score: float       # 0.0–1.0, output quality
  speed_score: float         # 0.0–1.0, response speed
  created_at: str            # ISO8601
  updated_at: str            # ISO8601
```

### Rank hierarchy

Agents follow a promotion ladder:

```
Worker -> Advisor -> Deputy -> Leader
```

* `promote` moves the agent one step up.
* `demote` moves the agent one step down.
* Boundaries are clamped (Worker cannot demote further, Leader cannot promote further).

### Role semantics

| Role       | Description                                     |
|------------|-------------------------------------------------|
| architect  | System design, planning, orchestration          |
| developer  | Code generation, implementation                 |
| designer   | Visual design, brand assets, UI                 |
| researcher | Information gathering, analysis                 |
| reviewer   | Code review, quality assurance                  |
| custom     | User-defined, no preset expectations            |

---

## 3. Registry Service Responsibilities

* **Registration / Deregistration**
  * Create agent with role, rank, provider, and scores.
  * Hard-delete agent.
  * Update mutable fields individually.
* **Promotion / Demotion**
  * Move agent up or down the rank ladder.
  * Clamp at boundaries (no promotion above Leader, no demotion below Worker).
* **Discovery**
  * List agents with filters: role, rank, status, provider, name.
  * Sort by creation date descending.
* **Auto-seed**
  * On first use, populate 4 default agents: Hermes, OpenCode, Open Design, Ollama.

### Non-Goals (Current MVP)

The following are **not yet implemented** in the current MVP (designed for future phases):
* Heartbeat tracking and health monitoring
* Concurrency control (max_concurrency, in-flight tracking)
* Versioning (updates mutate in place)
* Workspace scoping
* ProviderRegistry validation on registration

---

## 4. Database Schema

```sql
CREATE TABLE IF NOT EXISTS agents (
    id               TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    role             TEXT NOT NULL,
    rank             TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'active',
    provider         TEXT NOT NULL DEFAULT '',
    model            TEXT NOT NULL DEFAULT '',
    cost_tier        TEXT NOT NULL DEFAULT 'standard',
    reputation_score REAL NOT NULL DEFAULT 0.0,
    quality_score    REAL NOT NULL DEFAULT 0.0,
    speed_score      REAL NOT NULL DEFAULT 0.0,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_agents_role   ON agents(role);
CREATE INDEX IF NOT EXISTS ix_agents_rank   ON agents(rank);
CREATE INDEX IF NOT EXISTS ix_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS ix_agents_provider ON agents(provider);
```

### Seed Data

On first `AgentService` construction, 4 default agents are auto-seeded:

| Name        | Role       | Rank   | Provider    | Model              |
|-------------|------------|--------|-------------|--------------------|
| Hermes      | architect  | leader | Standard    | hermes-runtime     |
| OpenCode    | developer  | deputy | Standard    | opencode-runtime   |
| Open Design | designer   | advisor| Standard    | opendesign-runtime |
| Ollama      | researcher | advisor| Local       | ollama-runtime     |

---

## 5. API Surface

Base path: `/api/agents`

Feature flag: `agent_runtime` (default: `False`) — all endpoints return 404 when disabled.

### Endpoints

| Method | Path                              | Description                    |
|--------|-----------------------------------|--------------------------------|
| GET    | `/api/agents`                     | List agents (filters: role, rank, status, provider, name, limit) |
| POST   | `/api/agents`                     | Create agent                   |
| GET    | `/api/agents/{id}`                | Get one agent                  |
| PUT    | `/api/agents/{id}`                | Update mutable fields          |
| DELETE | `/api/agents/{id}`                | Hard-delete                    |
| POST   | `/api/agents/{id}/promote`        | Promote rank one level         |
| POST   | `/api/agents/{id}/demote`         | Demote rank one level          |

### Request Schemas

**Create:**
```json
{ "name": "string", "role": "developer", "rank": "worker",
  "status": "active", "provider": "", "model": "",
  "cost_tier": "standard", "reputation_score": 0.0,
  "quality_score": 0.0, "speed_score": 0.0 }
```

**Update:**
```json
{ "name": "string (optional)", "role": "string (optional)",
  "rank": "string (optional)", "status": "string (optional)",
  "provider": "string (optional)", "model": "string (optional)",
  "cost_tier": "string (optional)", "reputation_score": 0.0 (optional),
  "quality_score": 0.0 (optional), "speed_score": 0.0 (optional) }
```

### Error Handling

| Status | Meaning                                    |
|--------|--------------------------------------------|
| 200    | Success (data in response body)            |
| 404    | Agent not found / feature flag disabled    |
| 422    | Validation error (missing required field)  |

---

## 6. Integration Points

* **Feature Flags** — `agent_runtime` gates the entire registry; when off the system behaves exactly as before Sprint X.
* **Connection Manager** — uses the existing `ConnectionManager` from `toll/core/` for database access.
* **Existing API Router** — registered in `api/main.py` alongside all other routers at `/api/agents`.
* **Frontend** — AgentsPanel.svelte in the Svelte 5 shell displays agent data with promote/demote/status toggle actions.

---

## 7. Non-Goals (Out of Scope)

* Agent execution runtime itself (planned for future phase).
* Dynamic agent generation from prompts (future feature).
* Cross-provider failover logic (belongs to `ProviderSelector`).
* Heartbeat / health monitoring (future phase).
* Concurrency rate limiting (future phase).
* Agent versioning (future phase).
* Agent Council coordination layer (design only — see `docs/agent-council.md`).
* Workspace-scoped agents (future phase).
