"""Sprint X-11 — MCP Runtime Proof"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.runtime.service import RuntimeService
from toll.agents.service import AgentService


def main() -> int:
    tmp = Path(tempfile.mkdtemp()) / "mcp_runtime.db"
    cm = ConnectionManager(str(tmp))
    cm.execute("PRAGMA journal_mode=WAL;")
    cm.execute("PRAGMA foreign_keys = OFF;")
    FeatureFlags(cm=cm).enable("multi_agent_runtime")

    agent_svc = AgentService(cm)
    hermes = agent_svc.create_agent(name="Hermes", role="architect", rank="leader", provider="Standard", model="Hermes")
    opencode = agent_svc.create_agent(name="OpenCode", role="developer", rank="deputy", provider="Standard", model="OpenCode")
    ollama = agent_svc.create_agent(name="Ollama", role="researcher", rank="advisor", provider="Local", model="Ollama")
    opendesign = agent_svc.create_agent(name="Open Design", role="designer", rank="advisor", provider="Open Design", model="opendesign-runtime")

    runtime_svc = RuntimeService(cm, project_root=str(Path("/Users/S3EED/Claude/Projects/تول").resolve()))
    job = runtime_svc.create_runtime_job(task_id="sprint-x11-mcp", plan_text="MCP integration proof")

    assignments = runtime_svc.assign_agents(job.id, [
        {
            "agent_id": hermes.id,
            "fragment": json.dumps({"server": "filesystem", "tool": "list_directory", "arguments": {"path": "."}}),
        },
        {
            "agent_id": opencode.id,
            "fragment": json.dumps({"server": "git", "tool": "git_status", "arguments": {}}),
        },
        {
            "agent_id": ollama.id,
            "fragment": json.dumps({"server": "sqlite", "tool": "sqlite_run", "arguments": {"sql": "SELECT name FROM sqlite_master WHERE type='table'"}}),
        },
        {
            "agent_id": opendesign.id,
            "fragment": "Acknowledge MCP integration",
        },
    ])

    results = runtime_svc.execute_assignments(job.id)
    merged = runtime_svc.merge_results(job.id)
    runtime_svc.finalize_job(job.id, merged)

    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row

    rows = {r["assigned_agent_id"]: r for r in conn.execute("SELECT * FROM runtime_assignments").fetchall()}
    res_rows = {r["agent_id"]: r for r in conn.execute("SELECT * FROM runtime_results").fetchall()}
    execs = {r["agent_id"]: r for r in conn.execute("SELECT * FROM agent_executions").fetchall()}
    reps = {r["agent_id"]: r for r in conn.execute("SELECT * FROM agent_reputation").fetchall()}
    learn = [r for r in conn.execute("SELECT * FROM learning_entries").fetchall() if r["agent_id"] in [a.assigned_agent_id for a in assignments]]

    def text(res_row):
        text_val = res_row["result"] if "result" in res_row.keys() else ""
        return (text_val or "")[:38] + (".." if len(text_val or "") > 40 else "")

    print(f"{'Agent':<12} {'Status':<10} {'Output':<40} {'Duration':>10} {'Learn':<7} {'Reputation':<12}")
    print("-" * 85)
    for agent in [hermes, opencode, ollama, opendesign]:
        row = rows.get(agent.id, {})
        res = res_rows.get(agent.id, {})
        ex = execs.get(agent.id, {})
        rep = reps.get(agent.id, {})
        out = text(res)
        has_learn = any(l["agent_id"] == agent.id for l in learn)
        print(f"{agent.name:<12} {row.get('status','?') if hasattr(row, 'get') else row['status']:<10} {out:<40} {ex.get('duration_ms',0) if hasattr(ex, 'get') else ex['duration_ms']:>10} {'YES' if has_learn else 'NO':<7} {rep.get('recommended_rank','?') if hasattr(rep, 'get') else rep['recommended_rank']:<12}")

    print(f"\nAssignments: {len(rows)}")
    print(f"Results: {len(res_rows)}")
    print(f"Executions: {len(execs)}")
    print(f"Reputation: {len(reps)}")
    print(f"Learning: {len(learn)}")
    ok = len(rows) == 4 and len(res_rows) == 4 and len(execs) == 4 and len(reps) == 4 and len(learn) == 4
    print("\nVerdict:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
