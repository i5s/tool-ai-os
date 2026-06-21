"""Ollama CLI provider adapter."""

import asyncio
import shutil

from ...ports.llm import LLMProvider, LLMResponse
from ...core.settings import Settings


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def _find_bin(self) -> str | None:
        return shutil.which("ollama")

    def is_available(self) -> bool:
        return self._find_bin() is not None

    async def ask(self, prompt: str, system: str | None = None) -> LLMResponse:
        bin_path = self._find_bin()
        if not bin_path:
            raise RuntimeError("Ollama binary not found")

        model = self.settings.ollama_model()
        full = f"{system}\n{prompt}" if system else prompt

        proc = await asyncio.create_subprocess_exec(
            bin_path,
            "run",
            model,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=full.encode("utf-8")),
            timeout=120,
        )

        if proc.returncode != 0:
            raise RuntimeError(stderr.decode("utf-8", errors="replace").strip() or "Ollama failed")

        text = stdout.decode("utf-8", errors="replace").strip()
        return LLMResponse(text=text, provider=self.name, model=model)
