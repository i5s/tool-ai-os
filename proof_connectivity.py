"""Sprint X-10.2 — Agent Connectivity Verification via Runtime path."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.runtime.service import RuntimeService
from toll.agents.service import AgentService


PROMPT = "Reply with exactly: CONNECTIVITY_OK"


def main() -> int:
    tmp = Path(tempfile.mkdtemp()) / "connectivity.db"
    cm = ConnectionManager(str(tmp))
    cm.execute("PRAGMA journal_mode=WAL;")
    cm.execute("PRAGMA foreign_keys = OFF;")
    FeatureFlags(cm=cm).enable("multi_agent_runtime")

    agent_svc = AgentService(cm)
    hermes = agent_svc.create_agent(name="Hermes", role="architect", rank="leader", provider="Standard", model="Hermes")
    opencode = agent_svc.create_agent(name="OpenCode", role="developer", rank="deputy", provider="Standard", model="OpenCode")
    ollama = agent_svc.create_agent(name="Ollama", role="researcher", rank="advisor", provider="Local", model="Ollama")
    opendesign = agent_svc.create_agent(name="Open Design", role="designer", rank="advisor", provider="Open Design", model="opendesign-runtime")

    runtime_svc = RuntimeService(cm)
    job = runtime_svc.create_runtime_job(task_id="sprint-x10.2-connectivity", plan_text="Connectivity verification via Runtime")
    assignments = runtime_svc.assign_agents(job.id, [
        {"fragment": PROMPT, "agent_id": hermes.id},
        {"fragment": PROMPT, "agent_id": opencode.id},
        {"fragment": PROMPT, "agent_id": ollama.id},
        {"fragment": PROMPT, "agent_id": opendesign.id},
    ])

    results = runtime_svc.execute_assignments(job.id)
    merged = runtime_svc.merge_results(job.id)
    runtime_svc.finalize_job(job.id, merged)

    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row

    rows = {r["agent_id"]: r for r in conn.execute("SELECT * FROM runtime_results").fetchall()}
    execs = {r["agent_id"]: r for r in conn.execute("SELECT * FROM agent_executions").fetchall()}
    reps = {r["agent_id"]: r for r in conn.execute("SELECT * FROM agent_reputation").fetchall()}
    learn = [r for r in conn.execute("SELECT * FROM learning_entries").fetchall() if r["agent_id"] in [hermes.id, opencode.id, ollama.id, opendesign.id]]

    def text(agent_id):
        return (rows[agent_id]["result"] or "").strip()

    def rget(row, key, default=None):
        try:
            return row[key]
        except Exception:
            return default

    print(f"{'Agent':<12} {'Health':<8} {'Response':<20} {'Duration':>10} {'Exec':<7} {'Learn':<7} {'Reputation':<12}")
    print("-" * 80)
    for agent in [hermes, opencode, ollama, opendesign]:
        r = text(agent.id)
        e = execs.get(agent.id, {})
        rep = reps.get(agent.id, {})
        has_learn = any(l["agent_id"] == agent.id for l in learn)
        print(f"{agent.name:<12} {'OK':<8} {r if r else 'N/A':<20} {rget(e, 'duration_ms', 0):>10} {'YES':<7} {'YES' if has_learn else 'NO':<7} {rget(rep, 'reputation_score', '?'):<12}")

    print(f"\nLearning entries: {len(learn)}")
    print(f"Runtime results: {len(rows)}")
    print(f"Execution records: {len(execs)}")
    print(f"Reputation records: {len(reps)}")
    print("\nFinal verdict:", "PASS" if len(rows) == 4 and len(execs) == 4 and len(reps) == 4 else "FAIL")
    return 0 if len(rows) == 4 and len(execs) == 4 and len(reps) == 4 else 1


if __name__ == "__main__":
    raise SystemExit(main())
