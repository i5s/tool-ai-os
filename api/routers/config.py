from fastapi import APIRouter, Depends

from api.dependencies import get_settings, get_feature_flags
from toll.core.settings import Settings
from toll.core.feature_flags import FeatureFlags

router = APIRouter()


@router.get("/config")
def get_config(settings: Settings = Depends(get_settings)):
    keys = [
        "daily_limit_opencode",
        "daily_limit_ollama",
        "ollama_model",
        "opencode_bin",
        "website_path",
    ]
    return {k: settings.get(k) for k in keys}


@router.post("/config/{key}/{value}")
def set_config(key: str, value: str, settings: Settings = Depends(get_settings)):
    settings.set(key, value)
    return {"key": key, "value": value}


@router.get("/flags")
def get_flags(feature_flags: FeatureFlags = Depends(get_feature_flags)):
    return feature_flags.get_all()


@router.post("/flags/{name}/{enabled}")
def set_flag(
    name: str,
    enabled: bool,
    feature_flags: FeatureFlags = Depends(get_feature_flags),
):
    feature_flags.set(name, enabled)
    return {"name": name, "enabled": enabled}
