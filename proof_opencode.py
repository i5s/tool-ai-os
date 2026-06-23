#!/usr/bin/env python3
"""Proof script for Sprint X-7.6: real Hermes + OpenCode execution in Runtime."""
import sqlite3
import tempfile
from pathlib import Path

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.agents.service import AgentService
from toll.runtime.service import RuntimeService


def main():
    tmp = Path(tempfile.mkdtemp()) / "proof_opencode.db"
    cm = ConnectionManager(str(tmp))
    cm.execute("PRAGMA journal_mode=WAL;")
    cm.execute("PRAGMA foreign_keys = OFF;")

    flags = FeatureFlags(cm=cm)
    for key in [
        "task_dispatcher",
        "agent_runtime",
        "shared_memory",
        "agent_execution_history",
        "agent_council",
        "learning_loop",
        "agent_analytics",
        "agent_reputation",
        "multi_agent_runtime",
    ]:
        flags.enable(key)

    agent_svc = AgentService(cm)
    hermes = agent_svc.create_agent(name="Hermes", role="architect", rank="leader", provider="Standard", model="Hermes")
    opencode = agent_svc.create_agent(name="OpenCode", role="developer", rank="deputy", provider="Standard", model="OpenCode")
    print(f"Hermes agent_id: {hermes.id}")
    print(f"OpenCode agent_id: {opencode.id}")

    svc = RuntimeService(cm)
    job = svc.create_runtime_job(task_id="proof-opencode-1", plan_text="Real Hermes + OpenCode execution")

    # Explicitly assign both agents
    svc.assign_agents(job.id, [
        {"fragment": "Hi", "agent_id": hermes.id},
        {"fragment": "Hi", "agent_id": opencode.id},
    ])

    assignments = svc.execute_assignments(job.id)
    print(f"\nAssignments executed: {len(assignments)}")
    for a in assignments:
        print(f"  - {a.assigned_agent_id}: {a.status} (execution_id={a.execution_id})")

    merged = svc.merge_results(job.id)
    svc.finalize_job(job.id, merged)

    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row

    tables = [
        "runtime_jobs",
        "runtime_assignments",
        "runtime_results",
        "agent_executions",
        "learning_entries",
        "agent_reputation",
    ]
    for table in tables:
        print(f"\n--- {table} ---")
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        for row in rows:
            print(dict(row))

    # Summary counts
    print("\n--- Summary ---")
    for table in tables:
        count = conn.execute(f"SELECT count(*) as cnt FROM {table}").fetchone()["cnt"]
        print(f"{table}: {count} rows")

    conn.close()
    cm.close()


if __name__ == "__main__":
    main()
