from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from .models import RuntimeJob, RuntimeAssignment, RuntimeResult, RuntimeMemory, JobStatus
from .repository import RuntimeRepository
from toll.executions.service import ExecutionService
from toll.learning.service import LearningService
from toll.reputation.service import ReputationService
from toll.agents.service import AgentService
from toll.agents.adapters.hermes import HermesAdapter
from toll.adapters.llm.opencode import OpenCodeProvider
from toll.adapters.llm.ollama import OllamaProvider


class RuntimeService:
    def __init__(self, cm):
        self.cm = cm
        self.repo = RuntimeRepository(cm)

    def create_runtime_job(self, task_id: str, council_session_id: Optional[str] = None, plan_text: Optional[str] = None) -> RuntimeJob:
        job = RuntimeJob(
            task_id=task_id,
            council_session_id=council_session_id,
            plan_text=plan_text,
            status=JobStatus.PENDING.value,
        )
        return self.repo.create_job(job)

    def split_task(self, job_id: str, fragments: list[dict]) -> list[RuntimeAssignment]:
        job = self.repo.get_job(job_id)
        if not job:
            raise ValueError("Runtime job not found")
        assignments = []
        for frag in fragments:
            assignment = RuntimeAssignment(
                runtime_job_id=job_id,
                task_fragment=frag.get("fragment", ""),
                assigned_agent_id=frag.get("agent_id", ""),
                status=JobStatus.ASSIGNED.value,
            )
            self.repo.create_assignment(assignment)
            assignments.append(assignment)
        if assignments:
            self.repo.update_job_status(job_id, JobStatus.ASSIGNED.value)
        return assignments

    def assign_agents(self, job_id: str, assignments_data: list[dict]) -> list[RuntimeAssignment]:
        return self.split_task(job_id, assignments_data)

    def _run_agent(self, agent_id: str, prompt: str) -> dict:
        agent = AgentService(self.cm).get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        name = (agent.name or "").strip().lower()
        if name == "hermes" or name.startswith("hermes"):
            adapter = HermesAdapter()
            if not adapter.validate():
                raise RuntimeError("Hermes binary not found")
            return adapter.execute(
                task_id="",
                title=prompt,
                description=None,
                context=None,
            )
        if name == "opencode" or name.startswith("opencode") or "open code" in name:
            provider = OpenCodeProvider()
            if not provider.is_available():
                raise RuntimeError("OpenCode binary not found")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resp = loop.run_until_complete(provider.ask(prompt))
                loop.close()
                return {
                    "status": "success",
                    "output": resp.text,
                    "duration_ms": 0,
                    "metadata": {"provider": "opencode"},
                }
            except Exception as exc:
                return {
                    "status": "failed",
                    "output": str(exc),
                    "duration_ms": 0,
                    "metadata": {"error": str(exc)},
                }
        if name == "ollama" or name.startswith("ollama"):
            provider = OllamaProvider()
            if not provider.is_available():
                raise RuntimeError("Ollama binary not found")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resp = loop.run_until_complete(provider.ask(prompt))
                loop.close()
                return {
                    "status": "success",
                    "output": resp.text,
                    "duration_ms": 0,
                    "metadata": {"provider": "ollama", "model": provider.settings.ollama_model()},
                }
            except Exception as exc:
                return {
                    "status": "failed",
                    "output": str(exc),
                    "duration_ms": 0,
                    "metadata": {"error": str(exc)},
                }
        raise ValueError(f"No real adapter registered for agent: {agent.name!r}")

    def execute_assignments(self, job_id: str) -> list[RuntimeAssignment]:
        job = self.repo.get_job(job_id)
        if not job:
            raise ValueError("Runtime job not found")
        assignments = self.repo.list_assignments(job_id)
        if not assignments:
            agent_svc = AgentService(self.cm)
            candidates = agent_svc.list_agents(name_contains="Hermes", limit=1)
            if not candidates:
                raise ValueError("Default agent Hermes not found")
            assignments = [RuntimeAssignment(
                runtime_job_id=job_id,
                task_fragment=f"Acknowledge task {job.task_id}",
                assigned_agent_id=candidates[0].id,
                status=JobStatus.ASSIGNED.value,
            )]
            for a in assignments:
                self.repo.create_assignment(a)
        execution_svc = ExecutionService(self.cm)
        learning_svc = LearningService(self.cm)
        reputation_svc = ReputationService(self.cm)
        results = []
        for assignment in assignments:
            self.repo.update_assignment(assignment.id, status=JobStatus.RUNNING.value)
            raw_result = self._run_agent(assignment.assigned_agent_id, assignment.task_fragment)
            execution = execution_svc.start_execution(
                task_id=job.task_id,
                agent_id=assignment.assigned_agent_id,
                metadata={
                    "runtime_job_id": job.id,
                    "runtime_assignment_id": assignment.id,
                },
            )
            status = JobStatus.COMPLETED.value if raw_result.get("status") == "success" else JobStatus.FAILED.value
            duration_ms = raw_result.get("duration_ms") or 0
            output = raw_result.get("output", "")
            metadata = raw_result.get("metadata")
            if status == JobStatus.COMPLETED.value:
                execution_svc.complete_execution(
                    execution_id=execution.id,
                    duration_ms=duration_ms,
                    stdout=output,
                    stderr="",
                    metadata=metadata,
                )
            else:
                execution_svc.fail_execution(
                    execution_id=execution.id,
                    duration_ms=duration_ms,
                    error=output,
                    metadata=metadata,
                )
            assignment.status = status
            assignment.completed_at = datetime.now(timezone.utc).isoformat()
            assignment.execution_id = execution.id
            self.repo.update_assignment(
                assignment.id,
                status=assignment.status,
                completed_at=assignment.completed_at,
                execution_id=execution.id,
            )
            result = RuntimeResult(
                runtime_assignment_id=assignment.id,
                agent_id=assignment.assigned_agent_id,
                result=output,
                metadata=json.dumps(metadata) if metadata else None,
            )
            self.repo.create_result(result)
            learning_svc.record_execution_learning(
                execution_id=execution.id,
                agent_id=assignment.assigned_agent_id,
                task_id=job.task_id,
                status=assignment.status,
                stdout=output,
                stderr="" if status == JobStatus.COMPLETED.value else output,
                duration_ms=duration_ms,
            )
            reputation_svc.refresh_agent_reputation(assignment.assigned_agent_id)
            results.append(assignment)
        return results

    def merge_results(self, job_id: str) -> str:
        results = self.repo.get_results_for_job(job_id)
        if not results:
            return ""
        merged = "\n\n".join(f"[{r.agent_id}]: {r.result}" for r in results)
        self.repo.create_memory(RuntimeMemory(
            runtime_job_id=job_id,
            memory_type="merged_result",
            content=merged,
        ))
        return merged

    def finalize_job(self, job_id: str, merged_result: str) -> RuntimeJob:
        now = datetime.now(timezone.utc).isoformat()
        self.repo.update_job_status(job_id, JobStatus.COMPLETED.value, completed_at=now)
        self.cm.execute("UPDATE runtime_jobs SET merged_result = ? WHERE id = ?", (merged_result, job_id))
        self.cm.commit()
        job = self.repo.get_job(job_id)
        if not job:
            raise ValueError("Runtime job not found after finalize")
        return job


__all__ = ["RuntimeService"]
