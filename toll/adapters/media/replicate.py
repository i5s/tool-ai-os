from __future__ import annotations

import logging
import time
import urllib.request

from ...ports.media import MediaPort, MediaRequest, MediaResult

logger = logging.getLogger(__name__)


class ReplicateMediaAdapter(MediaPort):
    name = "replicate"

    def __init__(self, api_token: str | None = None):
        self.api_token = api_token
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            import replicate
            self._client = replicate
        except ImportError:
            self._client = None

    def is_available(self) -> bool:
        return self._client is not None

    def supported_types(self) -> list[str]:
        return ["image"]

    def generate(self, request: MediaRequest) -> MediaResult:
        if not self._client:
            return MediaResult(success=False, error="Replicate package not installed")

        start = time.monotonic()
        try:
            input_params = self._build_input(request)
            output = self._client.run(
                request.provider_model_id,
                input=input_params,
            )
            elapsed = int((time.monotonic() - start) * 1000)

            url, data = self._resolve_output(output)
            if not url:
                return MediaResult(success=False, error="No output from Replicate",
                                   provider_latency_ms=elapsed)

            content_type = self._guess_content_type(url)
            return MediaResult(
                success=True,
                url=url,
                media_data=data,
                media_type=request.media_type,
                provider=self.name,
                provider_model_id=request.provider_model_id,
                duration_ms=elapsed,
                content_type=content_type,
                file_size_bytes=len(data) if data else 0,
                seed=request.seed,
            )
        except Exception as e:
            elapsed = int((time.monotonic() - start) * 1000)
            logger.warning("Replicate generation failed: %s", e)
            return MediaResult(success=False, error=str(e), provider_latency_ms=elapsed)

    def _build_input(self, request: MediaRequest) -> dict:
        params = {"prompt": request.prompt}
        if request.size:
            parts = request.size.split("x")
            if len(parts) == 2:
                params["width"] = int(parts[0])
                params["height"] = int(parts[1])
        if request.seed is not None:
            params["seed"] = request.seed
        if request.negative_prompt:
            params["negative_prompt"] = request.negative_prompt
        return params

    def _resolve_output(self, output) -> tuple[str | None, bytes | None]:
        if isinstance(output, list):
            for item in output:
                url = str(item)
                if url.startswith("http"):
                    data = self._download(url)
                    if data:
                        return url, data
            return None, None
        url = str(output)
        if url.startswith("http"):
            data = self._download(url)
            return url, data
        return None, None

    def _download(self, url: str) -> bytes | None:
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return resp.read()
        except Exception as e:
            logger.warning("Failed to download from %s: %s", url, e)
            return None

    def _guess_content_type(self, url: str) -> str:
        lower = url.lower()
        if ".png" in lower:
            return "image/png"
        if ".jpg" in lower or ".jpeg" in lower:
            return "image/jpeg"
        if ".webp" in lower:
            return "image/webp"
        if ".mp4" in lower:
            return "video/mp4"
        return "application/octet-stream"
