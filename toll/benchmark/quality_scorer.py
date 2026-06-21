from __future__ import annotations


class QualityScorer:
    def __init__(self):
        self._registry: dict[str, float] = {}

    def register_criterion(self, name: str, weight: float = 1.0):
        self._registry[name] = weight

    def score(self, run_data: dict) -> float:
        total = 0.0
        weight_sum = 0.0
        for criterion, weight in self._registry.items():
            value = self._eval(criterion, run_data)
            if value is not None:
                total += value * weight
                weight_sum += weight
        return round(total / weight_sum, 2) if weight_sum > 0 else 0.0

    def _eval(self, criterion: str, data: dict) -> float | None:
        if criterion == "latency_ms":
            lat = data.get("provider_latency_ms")
            if lat is None:
                return None
            if lat <= 1000:
                return 1.0
            if lat <= 5000:
                return 0.7
            if lat <= 15000:
                return 0.4
            return 0.1
        if criterion == "file_size_bytes":
            size = data.get("file_size_bytes", 0)
            if size <= 0:
                return None
            if size >= 50000:
                return 1.0
            if size >= 10000:
                return 0.7
            return 0.4
        if criterion == "no_error":
            return 1.0 if not data.get("error") else 0.0
        return None
