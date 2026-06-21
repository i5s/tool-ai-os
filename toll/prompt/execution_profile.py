from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExecutionProfile:
    id: str
    name: str
    description: str = ""
    sub_profiles: list[str] = field(default_factory=list)
    default_media_type: str = "image"
    icon: str = "📋"
    tags: list[str] = field(default_factory=list)


DEFAULT_EXECUTION_PROFILES: list[ExecutionProfile] = [
    ExecutionProfile(
        id="research",
        name="Research Profile",
        description="Academic research, literature review, citation management",
        sub_profiles=["research_report", "academic_report", "literature_review"],
        default_media_type="text",
        icon="🔬",
        tags=["academic", "research"],
    ),
    ExecutionProfile(
        id="academic_report",
        name="Academic Report Profile",
        description="Formal academic writing, thesis sections, citation papers",
        sub_profiles=["academic_report", "citation_paper", "thesis_section"],
        default_media_type="text",
        icon="📄",
        tags=["academic", "report"],
    ),
    ExecutionProfile(
        id="marketing",
        name="Marketing Profile",
        description="Social media posts, advertisements, brand content",
        sub_profiles=["product_ad", "social_media", "brand_copy", "seo_content"],
        default_media_type="image",
        icon="📢",
        tags=["marketing", "social"],
    ),
    ExecutionProfile(
        id="product_advertisement",
        name="Product Advertisement Profile",
        description="Product photography, food photography, packaging design",
        sub_profiles=["product_ad", "food_photography", "packaging_design"],
        default_media_type="image",
        icon="🏷️",
        tags=["advertising", "product"],
    ),
    ExecutionProfile(
        id="presentation",
        name="Presentation Profile",
        description="Slide decks, pitch decks, conference presentations",
        sub_profiles=["presentation", "slide_deck", "pitch_deck"],
        default_media_type="text",
        icon="📊",
        tags=["presentation", "business"],
    ),
    ExecutionProfile(
        id="video_generation",
        name="Video Generation Profile",
        description="Video advertisements, short-form video, video presentations",
        sub_profiles=["video_ad", "video_presentation", "short_form_video"],
        default_media_type="video",
        icon="🎬",
        tags=["video", "media"],
    ),
]


class ExecutionProfileRepository:
    def __init__(self):
        self._profiles: dict[str, ExecutionProfile] = {
            p.id: p for p in DEFAULT_EXECUTION_PROFILES
        }

    def list(self) -> list[ExecutionProfile]:
        return list(self._profiles.values())

    def get(self, profile_id: str) -> ExecutionProfile | None:
        return self._profiles.get(profile_id)

    def resolve_prompt_profile(self, execution_id: str, intent: str) -> str | None:
        profile = self._profiles.get(execution_id)
        if not profile or not profile.sub_profiles:
            return None
        for sub in profile.sub_profiles:
            if sub == intent or intent in sub:
                return sub
        return profile.sub_profiles[0]
