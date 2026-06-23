"""Proof: Sprint X-9 — Activate Ollama in Runtime."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.runtime.service import RuntimeService
from toll.agents.service import AgentService


def main() -> int:
    tmp = Path(tempfile.mkdtemp()) / "proof_ollama.db"
    cm = ConnectionManager(str(tmp))
    cm.execute("PRAGMA journal_mode=WAL;")
    cm.execute("PRAGMA foreign_keys = OFF;")

    FeatureFlags(cm=cm).enable("multi_agent_runtime")

    agent_svc = AgentService(cm)
    hermes = agent_svc.create_agent(name="Hermes", role="architect", rank="leader", provider="Standard", model="Hermes")
    opencode = agent_svc.create_agent(name="OpenCode", role="developer", rank="deputy", provider="Standard", model="OpenCode")
    ollama = agent_svc.create_agent(name="Ollama", role="researcher", rank="advisor", provider="Local", model="Ollama")
    print("hermes_id:", hermes.id)
    print("opencode_id:", opencode.id)
    print("ollama_id:", ollama.id)

    runtime_svc = RuntimeService(cm)
    job = runtime_svc.create_runtime_job(
        task_id="proof-ollama-sprint-x9",
        plan_text="Verify Ollama in Runtime alongside Hermes and OpenCode",
    )
    fragments = [
        {"fragment": "Acknowledge task", "agent_id": hermes.id},
        {"fragment": "Hi", "agent_id": opencode.id},
        {"fragment": "Say hi", "agent_id": ollama.id},
    ]
    assignments = runtime_svc.assign_agents(job.id, fragments)
    assignment_ids = [a.id for a in assignments]
    print("job_id:", job.id)
    print("assignment_ids:", assignment_ids)

    results = runtime_svc.execute_assignments(job.id)
    execution_ids = [a.execution_id for a in results]
    print("execution_ids:", execution_ids)

    merged = runtime_svc.merge_results(job.id)
    runtime_svc.finalize_job(job.id, merged)

    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row

    print("\n--- runtime_jobs ---")
    for row in conn.execute("SELECT * FROM runtime_jobs").fetchall():
        print(dict(row))

    print("\n--- runtime_assignments ---")
    for row in conn.execute("SELECT * FROM runtime_assignments").fetchall():
        print(dict(row))

    print("\n--- runtime_results ---")
    for row in conn.execute("SELECT * FROM runtime_results").fetchall():
        print(dict(row))

    print("\n--- agent_executions ---")
    for row in conn.execute("SELECT * FROM agent_executions").fetchall():
        print(dict(row))

    print("\n--- learning_entries ---")
    for row in conn.execute("SELECT * FROM learning_entries").fetchall():
        print(dict(row))

    print("\n--- agent_reputation ---")
    for row in conn.execute("SELECT * FROM agent_reputation").fetchall():
        print(dict(row))

    # Assertions
    assert len(conn.execute("SELECT * FROM runtime_jobs").fetchall()) == 1
    assert len(conn.execute("SELECT * FROM runtime_assignments").fetchall()) == 3
    assert len(conn.execute("SELECT * FROM runtime_results").fetchall()) == 3
    assert len(conn.execute("SELECT * FROM agent_executions").fetchall()) == 3
    job_row = conn.execute("SELECT * FROM runtime_jobs WHERE id = ?", (job.id,)).fetchone()
    assert job_row["status"] == "completed"
    assert bool(merged)
    print("\nProof passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
