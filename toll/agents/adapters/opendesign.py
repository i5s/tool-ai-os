from __future__ import annotations

import json
import subprocess
import time
from typing import Any

from ..adapter import AgentAdapter


class OpenDesignAdapter(AgentAdapter):
    name = "opendesign"

    def __init__(self, base_url: str = "http://127.0.0.1:49152", agent_id: str = "amr"):
        self.base_url = base_url
        self.agent_id = agent_id

    def validate(self) -> bool:
        try:
            proc = subprocess.run(
                ["/Applications/Open Design.app/Contents/Resources/open-design/bin/vela", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return proc.returncode == 0
        except Exception:
            return False

    def health_check(self) -> dict:
        try:
            proc = subprocess.run(
                ["/Applications/Open Design.app/Contents/Resources/open-design/bin/vela", "whoami"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode != 0:
                return {"ok": False, "error": proc.stderr.strip() or proc.stdout.strip()}
            return {"ok": True, "user": proc.stdout.strip()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def execute(self, task_id: str, title: str, description: str | None = None, context: dict | None = None) -> dict:
        prompt = title
        if description:
            prompt = f"{title}\n\n{description}"
        if context:
            parts = [f"{k}: {v}" for k, v in context.items() if v is not None]
            if parts:
                prompt = f"{prompt}\n\nContext:\n" + "\n".join(parts)

        started = time.time()
        try:
            payload = json.dumps({"agentId": self.agent_id, "message": prompt})
            proc = subprocess.run(
                [
                    "curl", "-s", "-N",
                    "-X", "POST", f"{self.base_url}/api/chat",
                    "-H", "Content-Type: application/json",
                    "-d", payload,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            duration = int((time.time() - started) * 1000)
            return {
                "status": "failed",
                "output": "Open Design execution timed out",
                "duration_ms": duration,
                "metadata": {"timeout": True},
            }
        except Exception as exc:
            duration = int((time.time() - started) * 1000)
            return {
                "status": "failed",
                "output": str(exc),
                "duration_ms": duration,
                "metadata": None,
            }

        duration = int((time.time() - started) * 1000)
        raw = proc.stdout.decode("utf-8", errors="replace")
        text = self._parse_sse(raw)

        if proc.returncode != 0 or not text:
            err = proc.stderr.decode("utf-8", errors="replace").strip()
            return {
                "status": "failed",
                "output": text or err or "Open Design execution failed",
                "duration_ms": duration,
                "metadata": {"returncode": proc.returncode, "stderr": err} if err else {"returncode": proc.returncode},
            }

        return {
            "status": "success",
            "output": text,
            "duration_ms": duration,
            "metadata": {"provider": "opendesign", "agent_id": self.agent_id, "durationMs": duration},
        }

    def metadata(self) -> dict:
        return {
            "provider": "opendesign",
            "agent_id": self.agent_id,
            "base_url": self.base_url,
        }

    @staticmethod
    def _parse_sse(raw: str) -> str:
        chunks: list[str] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("data: "):
                continue
            data = line[len("data: "):]
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            event_type = obj.get("type")
            if event_type == "text_delta":
                delta = obj.get("delta", "")
                if delta:
                    chunks.append(delta)
            elif event_type == "text":
                text = obj.get("text", "")
                if text:
                    chunks.append(text)
            elif event_type == "runtime_close":
                status = obj.get("status")
                if status and status != "succeeded":
                    break
            elif event_type == "error":
                break
        return "".join(chunks).strip()
