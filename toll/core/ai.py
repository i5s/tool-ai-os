import subprocess, json, tempfile
from pathlib import Path
from .limiter import Limiter
from .browser import BrowserAI
from .storage import Storage
from . import config

class AI:
    def __init__(self):
        self.limiter = Limiter()
        self.browser = BrowserAI()
        self.db = Storage()
        self.providers = ["opencode", "ollama", "browser"]

    def ask(self, prompt: str, system: str = "") -> str:
        for provider in self.providers:
            if not self.limiter.can_use(provider):
                continue
            try:
                if provider == "opencode":
                    return self._opencode(prompt, system)
                elif provider == "ollama":
                    return self._ollama(prompt, system)
                elif provider == "browser":
                    return self._browser(prompt)
            except Exception as e:
                continue
        raise RuntimeError("كل مزودي AI غير متاحين اليوم (تم استهلاك الـ limit)")

    def _opencode(self, prompt: str, system: str = "") -> str:
        full = f"{system}\n\n{prompt}" if system else prompt
        cmd = [str(config.OPENCODE_BIN), "run", full]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        self.limiter.log_usage("opencode")
        if r.returncode == 0:
            return r.stdout.strip() or r.stderr.strip()
        raise RuntimeError(r.stderr.strip() or r.stdout.strip() or "opencode فشل")

    def _ollama(self, prompt: str, system: str = "") -> str:
        model = self.db.get_config("ollama_model", config.OLLAMA_MODEL_DEFAULT)
        full = f"{system}\n{prompt}" if system else prompt
        r = subprocess.run(
            [config.OLLAMA_BIN, "run", model],
            input=full, capture_output=True, text=True, timeout=120
        )
        self.limiter.log_usage("ollama")
        if r.returncode == 0:
            return r.stdout.strip()
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())

    def _browser(self, prompt: str) -> str:
        result = self.browser.ask(prompt)
        self.limiter.log_usage("browser")
        return result

    def limit_status(self):
        return self.limiter.status()
