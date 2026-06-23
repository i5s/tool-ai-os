#!/usr/bin/env python3
"""Proof script for real agent connectivity in Sprint X-7.5."""
import sqlite3
import tempfile
from pathlib import Path

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.agents.service import AgentService
from toll.runtime.service import RuntimeService


def main():
    tmp = Path(tempfile.mkdtemp()) / "proof.db"
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

    _ = AgentService(cm)  # seeds Hermes, OpenCode, Open Design

    svc = RuntimeService(cm)
    job = svc.create_runtime_job(task_id="proof-task-1", plan_text="Prove real connectivity")
    assignments = svc.execute_assignments(job.id)
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

    conn.close()
    cm.close()


if __name__ == "__main__":
    main()
