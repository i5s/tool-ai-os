from __future__ import annotations

import asyncio
import json
import time
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
from toll.agents.adapters.opendesign import OpenDesignAdapter
from toll.adapters.llm.opencode import OpenCodeProvider
from toll.adapters.llm.ollama import OllamaProvider
from toll.mcp.service import MCPService


class RuntimeService:
    def __init__(self, cm, project_root: str | None = None):
        self.cm = cm
        self.repo = RuntimeRepository(cm)
        self.mcp = MCPService(project_root or "/Users/S3EED/Claude/Projects/تول")

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
            started = time.time()
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resp = loop.run_until_complete(provider.ask(prompt))
                loop.close()
                duration = int((time.time() - started) * 1000)
                return {
                    "status": "success",
                    "output": resp.text,
                    "duration_ms": duration,
                    "metadata": {"provider": "opencode"},
                }
            except Exception as exc:
                duration = int((time.time() - started) * 1000)
                return {
                    "status": "failed",
                    "output": str(exc),
                    "duration_ms": duration,
                    "metadata": {"error": str(exc)},
                }
        if name == "ollama" or name.startswith("ollama"):
            provider = OllamaProvider()
            if not provider.is_available():
                raise RuntimeError("Ollama binary not found")
            started = time.time()
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resp = loop.run_until_complete(provider.ask(prompt))
                loop.close()
                duration = int((time.time() - started) * 1000)
                return {
                    "status": "success",
                    "output": resp.text,
                    "duration_ms": duration,
                    "metadata": {"provider": "ollama", "model": provider.settings.ollama_model()},
                }
            except Exception as exc:
                duration = int((time.time() - started) * 1000)
                return {
                    "status": "failed",
                    "output": str(exc),
                    "duration_ms": duration,
                    "metadata": {"error": str(exc)},
                }
        if name == "opendesign" or name.startswith("opendesign") or "open design" in name:
            adapter = OpenDesignAdapter()
            if not adapter.validate():
                raise RuntimeError("Open Design daemon not available")
            return adapter.execute(
                task_id="",
                title=prompt,
                description=None,
                context=None,
            )
        raise ValueError(f"No real adapter registered for agent: {agent.name!r}")

    def _run_mcp(self, agent_id: str, raw_prompt: str) -> dict:
        try:
            spec = json.loads(raw_prompt)
        except json.JSONDecodeError:
            return {
                "status": "failed",
                "output": "Invalid MCP task format",
                "duration_ms": 0,
                "metadata": {"error": "Invalid JSON", "raw": raw_prompt[:200]},
            }
        server = spec.get("server") or ""
        tool = spec.get("tool") or ""
        args = spec.get("arguments") or {}
        if not server or not tool:
            return {
                "status": "failed",
                "output": "MCP task requires 'server' and 'tool'",
                "duration_ms": 0,
                "metadata": {"error": "Missing fields", "spec": spec},
            }
        result = self.mcp.call(server=server, tool=tool, arguments=args)
        status = "success" if result.get("success") else "failed"
        return {
            "status": status,
            "output": json.dumps(result, ensure_ascii=False, indent=2) if not isinstance(result.get("output"), str) else result.get("output"),
            "duration_ms": result.get("duration_ms") or 0,
            "metadata": result,
        }

    def _execute_one(self, assignment: RuntimeAssignment, task_id: str) -> dict:
        raw = self._run_mcp(assignment.assigned_agent_id, assignment.task_fragment) if assignment.task_fragment.startswith("mcp:") else self._run_agent(assignment.assigned_agent_id, assignment.task_fragment)
        execution = ExecutionService(self.cm).start_execution(
            task_id=task_id,
            agent_id=assignment.assigned_agent_id,
            metadata={
                "runtime_job_id": assignment.runtime_job_id,
                "runtime_assignment_id": assignment.id,
            },
        )
        status = JobStatus.COMPLETED.value if raw.get("status") == "success" else JobStatus.FAILED.value
        duration_ms = raw.get("duration_ms") or 0
        output = raw.get("output") or ""
        metadata = raw.get("metadata")
        if status == JobStatus.COMPLETED.value:
            ExecutionService(self.cm).complete_execution(
                execution_id=execution.id,
                duration_ms=duration_ms,
                stdout=output,
                stderr="",
                metadata=metadata,
            )
        else:
            ExecutionService(self.cm).fail_execution(
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
        LearningService(self.cm).record_execution_learning(
            execution_id=execution.id,
            agent_id=assignment.assigned_agent_id,
            task_id=task_id,
            status=assignment.status,
            stdout=output,
            stderr="" if status == JobStatus.COMPLETED.value else output,
            duration_ms=duration_ms,
        )
        ReputationService(self.cm).refresh_agent_reputation(assignment.assigned_agent_id)
        return raw

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
        results = []
        for assignment in assignments:
            self.repo.update_assignment(assignment.id, status=JobStatus.RUNNING.value)
            self._execute_one(assignment, task_id=job.task_id)
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
