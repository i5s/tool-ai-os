"""Planner with approval matrix and execution modes.

Classifies user intent and produces a Plan that the Workflow Engine
can execute, pause, or reject based on approval requirements.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ApprovalLevel(str, Enum):
    AUTO = "auto_execute"
    PLAN_ONLY = "plan_only"
    APPROVAL = "requires_approval"


class PlannerMode(str, Enum):
    STRICT = "strict"
    BALANCED = "balanced"
    FAST = "fast"


@dataclass
class Plan:
    intent: str
    level: ApprovalLevel
    mode: PlannerMode
    title: str
    description: str
    steps: list[str]
    can_auto_execute: bool
    requires_approval: bool
    plan_only: bool
    metadata: dict = field(default_factory=dict)


class Planner:
    MATRIX: dict[str, ApprovalLevel] = {
        # AUTO EXECUTE
        "question": ApprovalLevel.AUTO,
        "summary": ApprovalLevel.AUTO,
        "translation": ApprovalLevel.AUTO,
        "prompt_generation": ApprovalLevel.AUTO,
        "brainstorm": ApprovalLevel.AUTO,
        "explanation": ApprovalLevel.AUTO,
        "code_snippet": ApprovalLevel.AUTO,
        "calculation": ApprovalLevel.AUTO,
        "image_analysis": ApprovalLevel.AUTO,
        "chat": ApprovalLevel.AUTO,
        "workspace_create": ApprovalLevel.AUTO,
        "memory_suggest": ApprovalLevel.AUTO,
        "search": ApprovalLevel.AUTO,
        # PLAN ONLY
        "research_plan": ApprovalLevel.PLAN_ONLY,
        "study_plan": ApprovalLevel.PLAN_ONLY,
        "marketing_plan": ApprovalLevel.PLAN_ONLY,
        "content_calendar": ApprovalLevel.PLAN_ONLY,
        "roadmap": ApprovalLevel.PLAN_ONLY,
        "swot": ApprovalLevel.PLAN_ONLY,
        "competitor_analysis": ApprovalLevel.PLAN_ONLY,
        # REQUIRES APPROVAL
        "report": ApprovalLevel.APPROVAL,
        "presentation": ApprovalLevel.APPROVAL,
        "carousel": ApprovalLevel.APPROVAL,
        "website_change": ApprovalLevel.APPROVAL,
        "file_operation": ApprovalLevel.APPROVAL,
        "memory_write": ApprovalLevel.APPROVAL,
        "memory_update": ApprovalLevel.APPROVAL,
        "memory_delete": ApprovalLevel.APPROVAL,
        "memory_promote": ApprovalLevel.APPROVAL,
        "bulk_content": ApprovalLevel.APPROVAL,
        "code_file": ApprovalLevel.APPROVAL,
        "email_send": ApprovalLevel.APPROVAL,
        "publish": ApprovalLevel.APPROVAL,
        "migration": ApprovalLevel.APPROVAL,
        "settings_change": ApprovalLevel.APPROVAL,
        "workspace_delete": ApprovalLevel.APPROVAL,
        "image_generation": ApprovalLevel.APPROVAL,
        "pdf_export": ApprovalLevel.APPROVAL,
        "data_import": ApprovalLevel.APPROVAL,
        "research": ApprovalLevel.APPROVAL,
        "research_quick": ApprovalLevel.AUTO,
        "research_deep": ApprovalLevel.APPROVAL,
    }

    KEYWORDS: dict[str, list[str]] = {
        "question": ["what", "how", "why", "when", "where", "who", "?", "explain"],
        "summary": ["summarize", "summary", "ملخص", "لخص"],
        "translation": ["translate", "translation", "ترجم", "ترجمة"],
        "prompt_generation": ["prompt", "برومبت", "برمبت"],
        "brainstorm": ["brainstorm", "ideas", "افكار", "أفكار"],
        "explanation": ["explain", "تفسير", "شرح"],
        "code_snippet": ["code snippet", "example code", "مثال كود"],
        "calculation": ["calculate", "compute", "احسب"],
        "image_analysis": ["analyze image", "describe image", "صورة"],
        "workspace_create": ["/brand", "/university", "/project", "/semester", "create workspace"],
        "memory_suggest": ["remember this", "suggest memory", "احفظ"],
        "search": ["ابحث", "search", "find", "google", "قوقل", "بحث عن", "look for", "بحث"],
        "research_plan": ["research plan", "خطة بحث"],
        "study_plan": ["study plan", "خطة دراسة"],
        "marketing_plan": ["marketing plan", "خطة تسويق"],
        "content_calendar": ["content calendar", "تقويم محتوى"],
        "roadmap": ["roadmap", "خطة"],
        "swot": ["swot", "سوات"],
        "competitor_analysis": ["competitor analysis plan", "خطة تحليل المنافسين"],
        "report": ["report", "تقرير"],
        "presentation": ["presentation", "present", "عرض تقديمي"],
        "carousel": ["carousel", "كروسيل"],
        "website_change": ["website", "موقع", "update site", "تعديل الموقع"],
        "file_operation": ["save file", "delete file", "move file", "file operation"],
        "memory_write": ["write to memory", "store in memory"],
        "memory_update": ["update memory", "تعديل الذاكرة"],
        "memory_delete": ["delete memory", "احذف من الذاكرة"],
        "memory_promote": ["promote memory", "memory promotion", "promote this memory"],
        "bulk_content": ["generate 10", "bulk", "many posts", "batch"],
        "code_file": ["write code to file", "generate file", "انشئ ملف"],
        "email_send": ["send email", "ارسل ايميل"],
        "publish": ["publish", "post to", "انشر"],
        "migration": ["migration", "ترحيل"],
        "settings_change": ["change setting", "settings"],
        "workspace_delete": ["delete workspace", "احذف workspace"],
        "image_generation": ["generate image", "create image", "صورة جديدة"],
        "pdf_export": ["export pdf", "pdf"],
        "data_import": ["import data", "استيراد بيانات"],
        "research": ["research", "بحث", "أبحاث"],
        "research_quick": ["quick research", "بحث سريع"],
        "research_deep": ["deep research", "بحث معمق"],
    }

    def __init__(self, mode: PlannerMode = PlannerMode.BALANCED):
        self.mode = mode

    @classmethod
    def from_flags(cls, strict: bool = False, fast: bool = False) -> "Planner":
        if strict and fast:
            import logging
            logging.getLogger(__name__).warning(
                "Both planner_strict_mode and planner_fast_mode are enabled; strict takes precedence"
            )
        if strict:
            return cls(PlannerMode.STRICT)
        if fast:
            return cls(PlannerMode.FAST)
        return cls(PlannerMode.BALANCED)

    def plan(self, message: str, context: dict | None = None) -> Plan:
        intent = self._detect_intent(message)
        base_level = self.MATRIX.get(intent, ApprovalLevel.AUTO)
        level = self._apply_mode(base_level)

        title = self._title_for(intent)
        description = self._describe(intent, level)

        return Plan(
            intent=intent,
            level=level,
            mode=self.mode,
            title=title,
            description=description,
            steps=[],
            can_auto_execute=level == ApprovalLevel.AUTO,
            requires_approval=level == ApprovalLevel.APPROVAL,
            plan_only=level == ApprovalLevel.PLAN_ONLY,
            metadata={"input": message, "context": context or {}},
        )

    def _detect_intent(self, message: str) -> str:
        text = message.lower()
        scores: dict[str, int] = {}
        max_keyword_len: dict[str, int] = {}

        for intent, keywords in self.KEYWORDS.items():
            count = 0
            longest = 0
            for kw in keywords:
                if kw.lower() in text:
                    count += 1
                    longest = max(longest, len(kw))
            if count > 0:
                scores[intent] = count
                max_keyword_len[intent] = longest

        if not scores:
            return "chat"

        max_score = max(scores.values())
        tied = [intent for intent, s in scores.items() if s == max_score]

        if len(tied) == 1:
            return tied[0]

        # Tie-break: longest keyword match wins
        tied.sort(key=lambda i: max_keyword_len.get(i, 0), reverse=True)
        if len(tied) > 1 and max_keyword_len[tied[0]] > max_keyword_len[tied[1]]:
            return tied[0]

        # Tie-break: prefer Arabic keywords
        arabic_patterns = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
        def arabic_score(intent: str) -> int:
            return sum(1 for kw in self.KEYWORDS[intent] if any(c in arabic_patterns for c in kw))
        tied.sort(key=arabic_score, reverse=True)
        if len(tied) > 1 and arabic_score(tied[0]) > arabic_score(tied[1]):
            return tied[0]

        # Final: first in matrix order (dict insertion order preserved)
        for intent in self.MATRIX:
            if intent in tied:
                return intent
        return tied[0]

    def _apply_mode(self, level: ApprovalLevel) -> ApprovalLevel:
        if self.mode == PlannerMode.STRICT:
            if level == ApprovalLevel.AUTO:
                return ApprovalLevel.AUTO
            return ApprovalLevel.APPROVAL
        if self.mode == PlannerMode.FAST:
            if level == ApprovalLevel.PLAN_ONLY:
                return ApprovalLevel.AUTO
            return level
        return level

    def _title_for(self, intent: str) -> str:
        return intent.replace("_", " ").title()

    def _describe(self, intent: str, level: ApprovalLevel) -> str:
        if level == ApprovalLevel.AUTO:
            return f"'{intent}' is safe to execute automatically."
        if level == ApprovalLevel.PLAN_ONLY:
            return f"'{intent}' will produce a plan for review before execution."
        return f"'{intent}' requires explicit user approval before execution."
