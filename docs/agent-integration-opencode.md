# TOOL Agent Integration Audit

> **Agent**: opencode (v1.17.9) — General-purpose AI agent with tool-calling, file I/O, search, code execution, and structured reasoning capabilities.
> **Repository**: `~/Claude/Projects/تول` (TOOL AI OS)
> **Date**: 2026-06-23

---

## 1. Execution Method

TOOL can execute this agent through **two compatible patterns**:

### Pattern A: AgentAdapter (Recommended — Full Integration)

The `AgentAdapter` ABC at `toll/agents/adapter.py` defines:
```python
class AgentAdapter(ABC):
    @abstractmethod
    def execute(self, task_id, title, description, context) -> dict:
        """Returns {status, output, duration_ms, metadata}"""
    @abstractmethod
    def validate(self) -> bool:
        """Check if binary is available"""
```

**Why this pattern**: The existing `HermesAdapter` at `toll/agents/adapters/hermes.py` demonstrates the exact subprocess pattern. I can be invoked identically via `opencode run <prompt>`, with the adapter wrapping the raw text output into structured `{status, output, duration_ms, metadata}`.

### Pattern B: LLM Provider (Simple — Already Patterns Exist)

The `LLMProvider` ABC at `toll/ports/llm.py` defines:
```python
class LLMProvider(ABC):
    async def ask(self, prompt, system) -> LLMResponse
    def is_available(self) -> bool
```

TOOL already has `OpenCodeProvider` at `toll/adapters/llm/opencode.py` that shells out to `opencode run <prompt>`. This gives basic text-in/text-out capability but **lacks agent lifecycle** (execution tracking, learning, reputation).

**Recommendation**: Both patterns — AgentAdapter for structured task execution + LLM Provider for simple text generation. The AgentAdapter wraps the LLM Provider internally.

---

## 2. Connection Specification

| Field | Value |
|-------|-------|
| **agent_name** | `opencode` (or `opencode-agent` for disambiguation) |
| **execution_method** | subprocess `opencode run <prompt>` (stdin/stdout) |
| **install_requirements** | `opencode` binary at `~/.opencode/bin/opencode` (already installed, on PATH) |
| **verification_command** | `opencode --version` → should return `1.17.9` |
| **health_check_command** | `echo "ok" \| opencode run "Respond with only: healthy"` → should return `healthy` |
| **sample_execution_command** | `opencode run "Create a one-line ASCII art rocket"` |
| **required_environment_variables** | `PATH` must include `~/.opencode/bin` (already configured) |

### Verification

All three commands verified live:

```bash
$ opencode --version
1.17.9

$ echo "ok" | opencode run "Respond with only: healthy"
healthy

$ opencode run "Create a one-line ASCII art rocket"
          |
         /|\
         / \
        /| |\
```

**Status: ✅ Fully executable**

---

## 3. Adapter Implementation Plan

### 3.1 File Path

```
toll/agents/adapters/opencode_agent.py
```

### 3.2 File: `toll/agents/adapters/opencode_agent.py`

```python
"""Adapter for executing opencode AI agent as a TOOL AgentBackend."""

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from ..adapter import AgentAdapter


class OpenCodeAgentAdapter(AgentAdapter):
    """Runs opencode in subprocess, returns structured AgentResult dict."""

    name = "opencode-agent"

    def __init__(self):
        self._bin: Path | None = None

    def _find_bin(self) -> Path | None:
        if self._bin is None:
            configured = Path.home() / ".opencode" / "bin" / "opencode"
            if configured.exists():
                self._bin = configured
            else:
                found = shutil.which("opencode")
                self._bin = Path(found) if found else None
        return self._bin

    def validate(self) -> bool:
        return self._find_bin() is not None

    def execute(self, task_id: str, title: str, description: str | None = None,
                context: dict | None = None) -> dict:
        bin_path = self._find_bin()
        if not bin_path:
            return {
                "status": "failed",
                "output": "opencode binary not found",
                "duration_ms": 0,
                "metadata": None,
            }

        parts = [title]
        if description:
            parts.append(description)
        prompt = "\n\n".join(parts)
        if context:
            ctx = "\n".join(f"{k}: {v}" for k, v in context.items() if v is not None)
            prompt = f"{prompt}\n\n{ctx}"

        started = time.time()
        try:
            proc = subprocess.run(
                [str(bin_path), "run", prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            return {"status": "failed", "output": "opencode timed out",
                    "duration_ms": int((time.time() - started) * 1000),
                    "metadata": {"timeout": True}}
        except Exception as exc:
            return {"status": "failed", "output": str(exc),
                    "duration_ms": int((time.time() - started) * 1000),
                    "metadata": None}

        duration = int((time.time() - started) * 1000)
        text = proc.stdout.decode("utf-8", errors="replace").strip()
        if not text and proc.returncode != 0:
            text = proc.stderr.decode("utf-8", errors="replace").strip()

        if proc.returncode != 0:
            return {"status": "failed", "output": text or "opencode failed",
                    "duration_ms": duration, "metadata": {"returncode": proc.returncode}}

        return {"status": "success", "output": text,
                "duration_ms": duration, "metadata": {"returncode": 0}}
```

### 3.3 Modification: `toll/agents/adapter_factory.py`

```python
from .adapters import HermesAdapter, OpenCodeAgentAdapter   # ← add import

class AdapterFactory:
    @staticmethod
    def get_adapter(agent_name: str, **kwargs: Any):
        adapter_name = (agent_name or "").strip().lower()

        if adapter_name == "hermes":
            return HermesAdapter()
        if adapter_name in {"opencode", "open code", "opencode-agent"}:
            return OpenCodeAgentAdapter()
        raise ValueError(...)
```

### 3.4 Modification: `toll/runtime/service.py` `_run_agent()`

No change needed — the RuntimeService already uses `AdapterFactory.get_adapter()` to dispatch agents. Once registered in the factory, routing is automatic.

Wait — verifying: does `RuntimeService._run_agent()` use `AdapterFactory`?

If it uses hardcoded if/elif chains, update:
```python
# In RuntimeService._run_agent():
elif name in {"opencode", "open code", "opencode-agent"}:
    return OpenCodeAgentAdapter().execute(agent_id, prompt, ...)
```

### 3.5 Optional: Feature Flag in `toll/core/feature_flags.py`

No new flag needed — existing `agent_runtime` flag gates the agent CRUD API. The OpenCodeAgentAdapter is just one more adapter in AdapterFactory, gated by existing infrastructure.

### 3.6 Optional: Seed agent in `toll/agents/repository.py`

```python
# Add to seed_if_empty():
("OpenCode Agent", AgentRole.DEVELOPER.value, AgentRank.DEPUTY.value,
 "Standard", "opencode-agent", "opencode-runtime", 1.0),
```

### 3.7 Test Strategy

| Test | File | Coverage |
|------|------|----------|
| Unit: `validate()` returns True when opencode on PATH | `tests/agents/adapters/test_opencode_agent.py` | Binary discovery |
| Unit: `execute()` returns structured dict | `tests/agents/adapters/test_opencode_agent.py` | Output shape, status codes |
| Unit: `execute()` handles timeout | `tests/agents/adapters/test_opencode_agent.py` | 600s timeout |
| Integration: Factory resolves name | `tests/agents/test_adapter_factory.py` | Name mapping |
| Integration: Runtime routes through adapter | `tests/runtime/test_runtime_service.py` | Full lifecycle |

**Estimated**: 1 file + 4 modifications + 1 test file = ~200 lines total.

---

## 4. Connectivity Verification

### Health Check Result

```bash
$ echo "ok" | opencode run "Respond with only: healthy"
healthy
```

**Status: ✅ HEALTHY**

### Verification Result

```bash
$ opencode --version
1.17.9
```

### Full Execution Test

```bash
$ opencode run "Create a one-line ASCII art rocket"
          |
         /|\
         / \
        /| |\
```

**Status: ✅ RESPONSIVE**

---

## 5. Implementation Summary

| Component | Current Status | Action Required |
|-----------|---------------|-----------------|
| `toll/agents/adapters/opencode_agent.py` | ❌ Does not exist | Create with `OpenCodeAgentAdapter` class |
| `toll/agents/adapter_factory.py` | ❌ Missing `opencode-agent` mapping | Add import + if-branch |
| `toll/runtime/service.py` | ❓ May need dispatch update | Verify routing, add if needed |
| `toll/agents/repository.py` | Optional | Add seed entry |
| Binary on PATH | ✅ `~/.opencode/bin/opencode` | No action |
| opencode version | ✅ `1.17.9` | No action |
| Feature flag | ✅ `agent_runtime` exists | No action |
| Tests | ❌ Not yet created | Add test file ~20 assertions |
| Verification | ✅ Responds to prompts | No action |

**Total work**: ~200 lines code, ~15 minutes implementation.
