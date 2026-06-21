from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..context.engine import ContextEngine
from ..core.connection_manager import ConnectionManager
from ..core.feature_flags import FeatureFlags
from ..core.registry import ProviderRegistry
from ..model_registry.service import ModelRegistryService
from .execution_profile import ExecutionProfileRepository
from .memory import PromptMemory
from .profile_service import PromptProfileService

logger = logging.getLogger(__name__)


@dataclass
class PromptPackage:
    prompt: str
    model_id: str
    profile_id: str
    execution_profile_id: str = ""
    prompt_version: int = 1
    params: dict = field(default_factory=dict)
    debug_info: dict = field(default_factory=dict)


class PromptIntelligenceEngine:
    def __init__(
        self,
        cm: ConnectionManager,
        flags: FeatureFlags,
        registry: ProviderRegistry,
        model_registry: ModelRegistryService | None = None,
    ):
        self.cm = cm
        self.flags = flags
        self.registry = registry
        self.model_registry = model_registry
        self.profile_service = PromptProfileService(cm, flags)
        self.execution_repo = ExecutionProfileRepository()
        self.prompt_memory = PromptMemory(cm)
        self.context_engine = ContextEngine(cm, flags)

    def resolve(self, user_input: str, media_type: str = "image",
                execution_profile_id: str = "",
                model_id: str | None = None) -> PromptPackage:
        self.profile_service.ensure_seeded()

        execution_profile = self.execution_repo.get(execution_profile_id)
        intent = self._detect_intent(user_input)

        prompt_profile = self._select_prompt_profile(execution_profile, intent, media_type)
        if not prompt_profile:
            logger.warning("No prompt profile found for intent=%s, media=%s", intent, media_type)
            return self._fallback(user_input, model_id)

        selected_model = self._select_model(prompt_profile, media_type, model_id)
        resolved_model_id = selected_model or (self.registry.available_media() + [""])[0]

        context = self._gather_context(user_input, media_type)
        prompt = self._render_template(
            prompt_profile.template,
            context | {"subject": user_input},
        )

        params = dict(prompt_profile.default_params)
        params["media_type"] = media_type

        return PromptPackage(
            prompt=prompt,
            model_id=resolved_model_id,
            profile_id=prompt_profile.id,
            execution_profile_id=execution_profile_id or "",
            prompt_version=prompt_profile.version,
            params=params,
            debug_info={
                "intent": intent,
                "profile": prompt_profile.id,
                "execution_profile": execution_profile_id,
                "context_keys": list(context.keys()),
            },
        )

    def _detect_intent(self, text: str) -> str:
        text_lower = text.lower()
        intent_map = {
            "اعلان": "product_ad",
            "منتج": "product_ad",
            "product": "product_ad",
            "advertisement": "product_ad",
            "اكل": "food_photography",
            "طعام": "food_photography",
            "كيك": "food_photography",
            "شوكولاتة": "food_photography",
            "food": "food_photography",
            "تصوير": "food_photography",
            "سفر": "travel_poster",
            "travel": "travel_poster",
            "بوست": "social_media",
            "social": "social_media",
            "منشور": "social_media",
            "بحث": "research_report",
            "research": "research_report",
            "تقرير": "research_report",
            "report": "research_report",
            "paper": "academic_report",
            "عرض": "presentation",
            "presentation": "presentation",
            "فيديو": "video_ad",
            "video": "video_ad",
            "واجهة": "ui_design",
            "ui": "ui_design",
            "شعار": "logo_design",
            "logo": "logo_design",
        }
        for keyword, intent in intent_map.items():
            if keyword in text_lower:
                return intent
        return "product_ad"

    def _select_prompt_profile(self, execution_profile, intent: str,
                                media_type: str):
        profiles = self.profile_service.repo.list(media_type=media_type)
        if execution_profile and execution_profile.sub_profiles:
            for sub_id in execution_profile.sub_profiles:
                match = next((p for p in profiles if p.id == sub_id), None)
                if match:
                    return match

        exact = next((p for p in profiles if p.id == intent), None)
        if exact:
            return exact

        tag_match = next((p for p in profiles if intent in p.tags), None)
        if tag_match:
            return tag_match

        return profiles[0] if profiles else None

    def _select_model(self, prompt_profile, media_type: str,
                      preferred: str | None) -> str | None:
        if preferred:
            if self._model_available(preferred):
                return preferred
            return preferred

        if self.prompt_memory.is_blacklisted(prompt_profile.id, preferred or ""):
            pass

        if self.model_registry:
            best = self.model_registry.find_best(media_type=media_type)
            if best:
                return best.id

        available = self.registry.available_media()
        if available:
            return available[0]
        return None

    def _model_available(self, model_id: str) -> bool:
        if self.model_registry:
            model = self.model_registry.get(model_id)
            if model and model.status == "active":
                return True
        return False

    def _gather_context(self, user_input: str, media_type: str) -> dict:
        context = {
            "style": "modern",
            "tone": "professional",
            "background": "clean",
            "language": "arabic",
            "scene_description": user_input,
            "color_palette": "neutral",
        }
        try:
            ctx = self.context_engine.get_active_context()
            if ctx:
                context["active_brand"] = ctx.get("brand", "")
                context["active_project"] = ctx.get("project", "")
        except Exception as e:
            logger.debug("Context assembly failed: %s", e)
        return context

    def _render_template(self, template: str, context: dict) -> str:
        result = template
        for key, val in context.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(val))
        return result

    def _fallback(self, user_input: str, model_id: str | None) -> PromptPackage:
        return PromptPackage(
            prompt=user_input,
            model_id=model_id or "",
            profile_id="fallback",
            prompt_version=0,
            params={"media_type": "image"},
            debug_info={"fallback": True},
        )
