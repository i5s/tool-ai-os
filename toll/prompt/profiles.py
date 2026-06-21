from __future__ import annotations

from .repository import PromptProfile


SYSTEM_PROFILES: list[PromptProfile] = [
    PromptProfile(
        id="product_ad",
        name="Product Advertisement",
        media_types=["image"],
        template=(
            "Professional product photograph of {subject}. "
            "Style: {style}. Background: {background}. "
            "Lighting: studio lighting, high contrast, dramatic shadows. "
            "Quality: ultra realistic, 8K, sharp focus, commercial photography. "
            "Mood: {tone}."
        ),
        default_params={"size": "1024x1024", "seed": None},
        compatible_models=["flux", "sdxl"],
        weight_criteria={"quality": 0.7, "latency": 0.2, "cost": 0.1},
        tags=["advertising", "product", "commercial"],
    ),
    PromptProfile(
        id="food_photography",
        name="Food Photography",
        media_types=["image"],
        template=(
            "Professional food photography of {subject}. "
            "Style: {style}, food magazine quality. "
            "Lighting: natural window light, soft shadows. "
            "Composition: top-down angle, shallow depth of field. "
            "Details: steam rising, fresh ingredients, textured surface. "
            "Mood: {tone}."
        ),
        default_params={"size": "1024x1024", "seed": None},
        compatible_models=["flux", "sdxl"],
        weight_criteria={"quality": 0.8, "latency": 0.1, "cost": 0.1},
        tags=["food", "photography", "commercial"],
    ),
    PromptProfile(
        id="travel_poster",
        name="Travel Poster",
        media_types=["image"],
        template=(
            "Travel poster design of {subject}. "
            "Style: {style}, vintage travel poster aesthetic. "
            "Colors: warm, golden hour lighting. "
            "Elements: {subject}, landscape, typography overlay. "
            "Mood: {tone}, adventurous, inviting."
        ),
        default_params={"size": "1024x768", "seed": None},
        compatible_models=["flux", "sdxl"],
        weight_criteria={"quality": 0.6, "latency": 0.3, "cost": 0.1},
        tags=["travel", "poster", "design"],
    ),
    PromptProfile(
        id="social_media",
        name="Social Media Post",
        media_types=["image"],
        template=(
            "Social media post for {subject}. "
            "Style: {style}, modern, clean design. "
            "Format: square, optimized for Instagram/Threads. "
            "Text overlay: {message}. "
            "Mood: {tone}, engaging, scroll-stopping."
        ),
        default_params={"size": "1080x1080", "seed": None},
        compatible_models=["flux", "sdxl", "dall-e"],
        weight_criteria={"quality": 0.5, "latency": 0.3, "cost": 0.2},
        tags=["social", "media", "marketing"],
    ),
    PromptProfile(
        id="research_report",
        name="Research Report",
        media_types=["text"],
        template=(
            "Write a comprehensive research report about {subject}. "
            "Format: academic report with sections. "
            "Tone: {tone}, formal and objective. "
            "Include: executive summary, methodology, findings, conclusion. "
            "Language: {language}."
        ),
        default_params={},
        compatible_models=[],
        weight_criteria={"quality": 0.9, "latency": 0.05, "cost": 0.05},
        tags=["research", "academic", "report"],
    ),
    PromptProfile(
        id="academic_report",
        name="Academic Report",
        media_types=["text"],
        template=(
            "Write an academic paper section about {subject}. "
            "Style: {style}, peer-review ready. "
            "Citation style: APA 7th edition. "
            "Structure: abstract, introduction, literature review, analysis, conclusion. "
            "Language: {language}."
        ),
        default_params={},
        compatible_models=[],
        weight_criteria={"quality": 0.9, "latency": 0.05, "cost": 0.05},
        tags=["academic", "paper", "thesis"],
    ),
    PromptProfile(
        id="presentation",
        name="Presentation",
        media_types=["text"],
        template=(
            "Create a presentation about {subject}. "
            "Style: {style}, clean and professional. "
            "Number of slides: {slide_count}. "
            "Each slide: title, bullet points, key takeaway. "
            "Tone: {tone}, persuasive and clear. "
            "Language: {language}."
        ),
        default_params={"slide_count": 8},
        compatible_models=[],
        weight_criteria={"quality": 0.7, "latency": 0.2, "cost": 0.1},
        tags=["presentation", "slides", "business"],
    ),
    PromptProfile(
        id="video_ad",
        name="Video Advertisement",
        media_types=["video"],
        template=(
            "Video advertisement for {subject}. "
            "Style: {style}, cinematic. "
            "Duration: {duration} seconds. "
            "Scene: {scene_description}. "
            "Camera motion: slow push-in, shallow depth of field. "
            "Mood: {tone}, emotional and compelling."
        ),
        default_params={"duration": 15},
        compatible_models=["veo", "runway", "kling"],
        weight_criteria={"quality": 0.8, "latency": 0.1, "cost": 0.1},
        tags=["video", "advertising", "commercial"],
    ),
    PromptProfile(
        id="ui_design",
        name="UI Design",
        media_types=["image"],
        template=(
            "User interface design for {subject}. "
            "Style: {style}, modern, minimal. "
            "Platform: mobile app. "
            "Elements: navigation bar, content cards, action buttons. "
            "Colors: {color_palette}. "
            "Mood: {tone}, clean and usable."
        ),
        default_params={"size": "1080x1920", "seed": None},
        compatible_models=["flux", "sdxl"],
        weight_criteria={"quality": 0.6, "latency": 0.3, "cost": 0.1},
        tags=["ui", "design", "app"],
    ),
    PromptProfile(
        id="logo_design",
        name="Logo Design",
        media_types=["image"],
        template=(
            "Logo design for {subject}. "
            "Style: {style}, minimal, vector-like. "
            "Background: transparent, white. "
            "Elements: icon + typography mark. "
            "Mood: {tone}, professional and memorable."
        ),
        default_params={"size": "1024x1024", "seed": None},
        compatible_models=["flux", "sdxl"],
        weight_criteria={"quality": 0.7, "latency": 0.2, "cost": 0.1},
        tags=["logo", "brand", "design"],
    ),
]


def seed_profiles(repo):
    existing = repo.list()
    existing_ids = {p.id for p in existing}
    for profile in SYSTEM_PROFILES:
        if profile.id not in existing_ids:
            repo.create(profile)
