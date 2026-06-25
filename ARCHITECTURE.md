# Architecture

## Overview

This document is the single source of truth for TOOL architecture after v0.14.0-auth-beta.

## Purpose
- Provide stable architectural context across sprints
- Define layering, module boundaries, and extension points
- Document runtime, auth, MCP, and deployment flows
- Support review-driven changes only

## Goals
- Preserve ideological constants that define application behavior
- Enable new functionality without foundational rework
- Maintain backward compatibility with existing test suites
- Keep configuration centralized and repository patterns uniform

## Scope
- Runtime, council, agents, MCP, learning, reputation, analytics, auth, health, deployment

---

## Module Organization

### Current Packages
- `toll.agents` — agent adapter registry and factory
- `toll.adapters` — external integrations (provider adapters)
- `toll.analytics` — analytics data and service layer
- `toll.application` — application-level orchestration services
- `toll.auth` — authentication, roles, session management
- `toll.benchmark` — benchmark data and service layer
- `toll.context` — context engine
- `toll.core` — foundational services (connection manager, feature flags, provider selector, settings, storage)
- `toll.council` — council models, repository, service
- `toll.engine` — engine/prompt generation/reports
- `toll.executions` — execution models, repository, service
- `toll.learning` — learning models, repository, service
- `toll.mcp` — MCP client and service facade
- `toll.memory` — memory graph
- `toll.model` — model abstractions
- `toll.model_registry` — model registry data and service
- `toll.operations` — cost, cleanup, dashboard, storage, usage services
- `toll.planner` — planner domain
- `toll.ports` — interface/port definitions
- `toll.prompt` — prompt engine, execution profiles, memory, profiles/repository
- `toll.reputation` — reputation models, repository, service
- `toll.research` — research services and engines
- `toll.runtime` — runtime models, repository, service
- `toll.shared_memory` — shared memory models, repository, service
- `toll.tasks` — task models, repository, service
- `toll.workflow` — workflow engine
- `toll.workspace` — workspace manager
- `api.routers` — FastAPI presenters
- `tests` — non-production test code

---

## Layer Diagram

```
Presentation Layer
    FastAPI routers (api.routers)
        |
        v
API Layer
    router endpoints, request validation, auth dependencies
        |
        v
Application / Service Layer
    toll.application.*
    toll.analytics.service
    toll.auth.service
    toll.benchmark.service
    toll.council.service
    toll.executions.service
    toll.learning.service
    toll.mcp.service
    toll.model_registry.service
    toll.operations.*
    toll.prompt.profile_service
    toll.reputation.service
    toll.research.*
    toll.runtime.service
    toll.shared_memory.service
    toll.tasks.service
        |
        v
Repository Layer
    toll.*.repository
        |
        v
Persistence Layer
    SQLite via toll.core.connection_manager
    toll.core.storage
    toll.core.feature_flags
    toll.core.settings
    toll.core.config
```

## Layer Dependency Rules
- Presentation may import API routers and FastAPI utilities.
- API routers may import services and dependencies.
- Services may import repositories.
- Repositories may import persistence/connection utilities.
- Cross-layer violations are considered architecture debt.
- No top-level domain module may import a router or application transport layer.

---

## Flow Diagrams

### Runtime Flow
1. Request enters FastAPI router
2. Router calls runtime/service endpoint
3. Service uses runtime repository
4. Repository persists via connection manager
5. Response returns to client

### Agent Flow
1. Adapter implements behavior for a target agent
2. Factory instantiates adapters
3. Runtime consumes adapters
4. Execution runs agent lifecycle

### MCP Flow
1. Client connects to MCP server
2. Service facade coordinates client interactions
3. Runtime executes operations
4. Response returns through service and client

### Auth Flow
1. Client authenticates with credentials
2. Auth service validates credentials
3. Session token created and returned
4. Protected endpoints validate token via auth dependency
5. Logout invalidates session

### Deployment Flow
1. Environment variables load at startup
2. systemd starts FastAPI service
3. Caddy terminates TLS and forwards HTTP
4. Health endpoints expose status
5. Backups export SQLite database

---

## Runtime

### Runtime Modules
- `toll.runtime.models` — runtime records
- `toll.runtime.repository` — runtime persistence
- `toll.runtime.service` — runtime behavior

### Constraints
- Runtime behavior must not be changed without sprint-level approval
- Runtime tests use connection-managed paths

## Council

### Council Modules
- `toll.council.models` — council records
- `toll.council.repository` — council persistence
- `toll.council.service` — council orchestration

## Agents

### Agent Modules
- `toll.agents.adapter` — agent adapter interface
- `toll.agents.adapter_factory` — adapter instantiation
- `toll.agents.models` — agent data models
- `toll.agents.repository` — agent persistence
- `toll.agents.service` — agent service layer

### Standard Pattern
Adapter -> Factory -> Runtime -> Execution

## MCP

### MCP Modules
- `toll.mcp.client` — MCP connector abstraction
- `toll.mcp.service` — MCP service facade

### Connectors
- Filesystem
- Git
- SQLite

### Extension Contract
Future connectors must implement the same client interface and be registerable through the service facade.

## Learning

### Learning Modules
- `toll.learning.models` — learning state
- `toll.learning.repository` — learning persistence
- `toll.learning.service` — learning behavior

## Reputation

### Reputation Modules
- `toll.reputation.models` — reputation state
- `toll.reputation.repository` — reputation persistence
- `toll.reputation.service` — reputation behavior

## Analytics

### Analytics Modules
- `toll.analytics.models` — analytics state
- `toll.analytics.service` — analytics behavior

## Auth

### Auth Modules
- `toll.auth.models` — user/session models
- `toll.auth.repository` — auth persistence
- `toll.auth.service` — auth behavior
- `toll.auth.dependencies` — FastAPI auth dependencies
- `api.routers.auth` — auth API endpoints
- `api.routers.auth_bootstrap` — auth router inclusion
- `api.routers.users` — user management endpoints

### Auth Invariants
- Real database setup required (no mocking of AuthService, SessionService, UserRepository)
- bcrypt hashing with passlib
- Session invalidation on logout

## Health

### Health Modules
- `api.routers.health` — health endpoints

## Deployment

### Deployment Modules
- `deployment/Caddyfile`
- `deployment/toll.service`
- `deployment/backup.sh`
- `deployment/.env.example`

### Invariants
- All secrets externalized
- No secrets in repository
- Frontend build served via reverse proxy

---
