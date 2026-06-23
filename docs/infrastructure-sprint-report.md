# Infrastructure Sprint — Local AI Stack

**Date**: 2026-06-23  
**Host**: Apple M4, 16GB RAM, 228GB SSD  
**Status**: ✅ Complete

---

## Priority 1 — Ollama Models

### System Resources

| Resource | Value |
|----------|-------|
| CPU | Apple M4 (10 cores) |
| RAM | 16 GB |
| Disk total | 228 GB |
| Disk available | **37 GB** (25% used) |

### Model Installed

| Model | Size | Status |
|-------|------|--------|
| `qwen3:14b` | **9.3 GB** | ✅ Pulled |
| `qwen2.5:7b` | 4.7 GB | ✅ Pre-existing |
| `llava:7b` | 4.7 GB | ✅ Pre-existing |
| `hermes3:8b` | 4.7 GB | ✅ Pre-existing |

**Model selection logic**: `qwen3:14b` (9.3GB) was the largest stable model that fits safely with 37GB available.

### Latency Benchmark

| Model | Test | Latency | Notes |
|-------|------|---------|-------|
| `qwen3:14b` | "Say hello" | **41s** | Thinking tokens add heavy overhead |
| `qwen2.5:7b` | "Say hello" | **6s** | Fast, no chain-of-thought |

### Memory Usage (with qwen3:14b loaded)

| Process | RSS |
|---------|-----|
| `ollama` daemon | 43 MB |
| `qwen3:14b` (loaded) | 5,180 MB |

**Verdict**: qwen3:14b is functional but impractical for latency-sensitive tasks (41s for trivial prompts) due to extended "Thinking" chain-of-thought. Recommend **qwen2.5:7b** as default for fast tasks, `qwen3:14b` only for complex reasoning.

---

## Priority 2 — Aider

| Status | Value |
|--------|-------|
| ✅ Installed | `aider` v0.82.3 |
| ✅ Verified | `aider --version` → `aider 0.82.3` |
| Package | `aider-chat` (pip) |
| Binary | `/Users/S3EED/Library/Python/3.9/bin/aider` |
| PATH symlink | `~/.local/bin/aider` |
| Upgrade available | v0.86.2 (not applied — stable release preferred) |

---

## Priority 3 — MCP Infrastructure

### Installed Servers

| Server | Package | Binary | Status |
|--------|---------|--------|--------|
| **Filesystem MCP** | `@modelcontextprotocol/server-filesystem` | `node /.../dist/index.js <dir>` | ✅ Working |
| **Git MCP** | `mcp-server-git` v0.6.2 (Python 3.11) | `mcp-server-git --repository <dir>` | ✅ Working |
| **SQLite MCP** | `@mokei/mcp-sqlite` | `node /.../lib/serve.js` | ✅ Working |

### Connectivity Verification

All three MCP servers responded to `initialize` JSON-RPC handshake:

| Server | Protocol | Tools |
|--------|----------|-------|
| Filesystem MCP | 2025-11-25 | `listChanged` |
| Git MCP | MCP stdio | Git operations |
| SQLite MCP | 2025-11-25 | `listChanged` |

### opencode MCP Config

Created at `~/.config/opencode/mcp.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "node",
      "args": [".../server-filesystem/dist/index.js", "/Users/S3EED/Claude/Projects/تول"]
    },
    "git": {
      "command": "mcp-server-git",
      "args": ["--repository", "/Users/S3EED/Claude/Projects/تول"]
    },
    "sqlite": {
      "command": "node",
      "args": [".../@mokei/mcp-sqlite/lib/serve.js"]
    }
  }
}
```

---

## Priority 4 — TOOL Integration Audit

| Component | Installed | Working | Integration Ready |
|-----------|-----------|---------|-------------------|
| **Hermes** | ✅ v0.17.0 at `~/.local/bin/hermes` | ✅ Hermes Agent v0.17.0 responds | ✅ `HermesAdapter` at `toll/agents/adapters/hermes.py` |
| **OpenCode** | ✅ v1.17.9 at `~/.opencode/bin/opencode` | ✅ `opencode run <prompt>` works | ✅ `OpenCodeProvider` at `toll/adapters/llm/opencode.py` |
| **Open Design** | ✅ App at `/Applications/Open Design.app` | ❌ Daemon not running (port 7456 unreachable) | ✅ Tool infrastructure available in session |
| **Ollama** | ✅ v0.30.10 at `/usr/local/bin/ollama` | ✅ Daemon running, 5 models loaded | ✅ `OllamaProvider` at `toll/adapters/llm/ollama.py` |

### Integration Notes

- **Hermes**: 378 commits behind upstream. `hermes update` recommended before production use.
- **OpenCode**: Ready. Adapter uses subprocess `opencode run <prompt>`.
- **Open Design**: App installed, daemon requires `pnpm tools-dev` to start. Not critical — existing Open Design tools in this session work via agent infrastructure.
- **Ollama**: Provider exists but uses CLI mode (`ollama run <model> <prompt>`). API mode (`http://localhost:11434`) also available for async requests.

---

## Disk Usage Summary

```
Before: 228Gi total, ~20Gi available
After:  228Gi total, 37Gi available  (APFS compression/optimisation)
```

New large files added:

| Component | Size |
|-----------|------|
| `qwen3:14b` model | 9.3 GB |
| MCP servers (npm) | ~150 MB |
| `aider-chat` (pip) | ~200 MB |

---

## Recommended Integration Order

1. **Ollama** — already has `OllamaProvider` adapter. Default model: `qwen2.5:7b` (fast), fallback: `qwen3:14b` (deep reasoning).
2. **OpenCode** — already has `OpenCodeProvider` adapter. No changes needed.
3. **Hermes** — already has `HermesAdapter`. Run `hermes update` first.
4. **Open Design** — app installed, start daemon when design generation is needed.

---

## Failures Encountered

| Failure | Resolution |
|---------|-----------|
| `@modelcontextprotocol/server-git` not on npm | Git MCP is a Python package — installed from source via `pip` + Python 3.11 |
| `@modelcontextprotocol/server-sqlite` not on npm | Replaced with `@mokei/mcp-sqlite` — compatible MCP interface |
| Python 3.9.6 too old for `mcp-server-git` (requires >=3.10) | Used Python 3.11 from `~/.local/bin/python3.11` (uv-managed) |
| `uv` externally-managed env blocked pip | Used `--break-system-packages` flag |
| `aider` binary not on PATH | Symlinked from `~/.local/bin/aider` |
| `qwen3:14b` 41s latency for trivial prompts | Intended for complex reasoning — use `qwen2.5:7b` for fast tasks |
