from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from ..adapter import AgentAdapter


class HermesAdapter(AgentAdapter):
    name = "hermes"

    def __init__(self):
        self._bin: Path | None = None

    def _find_bin(self) -> Path | None:
        if self._bin is None:
            configured = Path("/Users/S3EED/.hermes/hermes-agent/venv/bin/hermes")
            if configured.exists():
                self._bin = configured
            else:
                found = shutil.which("hermes")
                self._bin = Path(found) if found else None
        return self._bin

    def validate(self) -> bool:
        return self._find_bin() is not None

    def execute(self, task_id: str, title: str, description: str | None, context: dict | None = None) -> dict:
        bin_path = self._find_bin()
        if not bin_path:
            return {
                "status": "failed",
                "output": "Hermes binary not found",
                "duration_ms": 0,
                "metadata": None,
            }

        prompt = title
        if description:
            prompt = f"{title}\n\n{description}"
        if context:
            ctx_parts = [f"{k}: {v}" for k, v in context.items() if v is not None]
            if ctx_parts:
                prompt = f"{prompt}\n\nContext:\n" + "\n".join(ctx_parts)

        started = time.time()
        try:
            proc = subprocess.run(
                [str(bin_path), "chat", "-q", prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            duration = int((time.time() - started) * 1000)
            return {
                "status": "failed",
                "output": "Hermes execution timed out",
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
        text = proc.stdout.decode("utf-8", errors="replace").strip()
        if not text and proc.returncode != 0:
            text = proc.stderr.decode("utf-8", errors="replace").strip()

        if proc.returncode != 0:
            return {
                "status": "failed",
                "output": text or "Hermes execution failed",
                "duration_ms": duration,
                "metadata": {"returncode": proc.returncode},
            }

        return {
            "status": "success",
            "output": text,
            "duration_ms": duration,
            "metadata": {"returncode": 0},
        }
