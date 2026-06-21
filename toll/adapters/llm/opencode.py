"""OpenCode CLI provider adapter."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from ...ports.llm import LLMProvider, LLMResponse
from ...core.settings import Settings


class OpenCodeProvider(LLMProvider):
    name = "opencode"

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self._bin: Path | None = None

    def _find_bin(self) -> Path | None:
        if self._bin is None:
            configured = self.settings.opencode_bin()
            if configured and Path(configured).exists():
                self._bin = Path(configured)
            else:
                found = shutil.which("opencode")
                self._bin = Path(found) if found else None
        return self._bin

    def is_available(self) -> bool:
        bin_path = self._find_bin()
        return bin_path is not None and bin_path.exists()

    async def ask(self, prompt: str, system: str | None = None) -> LLMResponse:
        bin_path = self._find_bin()
        if not bin_path:
            raise RuntimeError("OpenCode binary not found")

        full = f"{system}\n\n{prompt}" if system else prompt
        proc = await asyncio.create_subprocess_exec(
            str(bin_path),
            "run",
            full,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        if proc.returncode != 0:
            raise RuntimeError(stderr.decode("utf-8", errors="replace").strip() or "OpenCode failed")

        text = stdout.decode("utf-8", errors="replace").strip()
        if not text:
            text = stderr.decode("utf-8", errors="replace").strip()

        return LLMResponse(text=text, provider=self.name)
