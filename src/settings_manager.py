import json
import os
from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import datetime


SETTINGS_FILE = "config/settings.json"


class APISettings(BaseModel):
    engine_type: str = "hybrid"
    timeout: int = 30
    max_retries: int = 3


class CacheSettings(BaseModel):
    enabled: bool = True
    ttl_seconds: int = 3600
    max_entries: int = 1000


class RateLimitingSettings(BaseModel):
    default_tier: str = "default"
    default_requests: int = 100
    default_window: int = 3600
    trial_requests: int = 20
    trial_window: int = 3600
    premium_requests: int = 1000
    premium_window: int = 3600


class UIPreferences(BaseModel):
    theme: str = "dark"
    refresh_interval: int = 5
    compact_mode: bool = False
    show_stats: bool = True
    language: str = "en"


class SettingsModel(BaseModel):
    api: APISettings
    cache: CacheSettings
    rate_limiting: RateLimitingSettings
    ui_preferences: UIPreferences
    last_modified: Optional[str] = None


DEFAULT_SETTINGS = {
    "api": {
        "engine_type": "hybrid",
        "timeout": 30,
        "max_retries": 3,
    },
    "cache": {
        "enabled": True,
        "ttl_seconds": 3600,
        "max_entries": 1000,
    },
    "rate_limiting": {
        "default_tier": "default",
        "default_requests": 100,
        "default_window": 3600,
        "trial_requests": 20,
        "trial_window": 3600,
        "premium_requests": 1000,
        "premium_window": 3600,
    },
    "ui_preferences": {
        "theme": "dark",
        "refresh_interval": 5,
        "compact_mode": False,
        "show_stats": True,
        "language": "en",
    },
}


def _ensure_config_dir():
    os.makedirs("config", exist_ok=True)


def _load_json_settings() -> Dict[str, Any]:
    """Load settings from JSON file"""
    _ensure_config_dir()
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS.copy()


def _save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to JSON file"""
    try:
        _ensure_config_dir()
        settings["last_modified"] = datetime.utcnow().isoformat()
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


def get_settings() -> SettingsModel:
    """Load settings from file and return SettingsModel"""
    settings_data = _load_json_settings()
    return SettingsModel(
        api=settings_data.get("api", DEFAULT_SETTINGS["api"]),
        cache=settings_data.get("cache", DEFAULT_SETTINGS["cache"]),
        rate_limiting=settings_data.get(
            "rate_limiting", DEFAULT_SETTINGS["rate_limiting"]
        ),
        ui_preferences=settings_data.get(
            "ui_preferences", DEFAULT_SETTINGS["ui_preferences"]
        ),
        last_modified=settings_data.get("last_modified"),
    )


def get_settings_dict() -> Dict[str, Any]:
    """Load settings as plain dictionary"""
    settings = get_settings()
    return {
        "api": settings.api.model_dump(),
        "cache": settings.cache.model_dump(),
        "rate_limiting": settings.rate_limiting.model_dump(),
        "ui_preferences": settings.ui_preferences.model_dump(),
        "last_modified": settings.last_modified,
    }


def get_category(category: str) -> Optional[Dict[str, Any]]:
    """Get a specific category of settings"""
    settings_data = _load_json_settings()
    if category in settings_data:
        return settings_data[category]
    return None


def update_setting(category: str, key: str, value: Any) -> bool:
    """Update a specific setting in a category"""
    settings_data = _load_json_settings()

    if category not in settings_data:
        return False

    if category == "api":
        defaults = DEFAULT_SETTINGS["api"]
    elif category == "cache":
        defaults = DEFAULT_SETTINGS["cache"]
    elif category == "rate_limiting":
        defaults = DEFAULT_SETTINGS["rate_limiting"]
    elif category == "ui_preferences":
        defaults = DEFAULT_SETTINGS["ui_preferences"]
    else:
        return False

    if key not in defaults:
        return False

    try:
        settings_data[category][key] = value
        return _save_settings(settings_data)
    except Exception:
        return False


def update_category(category: str, values: Dict[str, Any]) -> bool:
    """Update an entire category with new values"""
    settings_data = _load_json_settings()

    if category not in DEFAULT_SETTINGS:
        return False

    try:
        settings_data[category] = {**DEFAULT_SETTINGS[category], **values}
        return _save_settings(settings_data)
    except Exception:
        return False


def reset_to_defaults() -> bool:
    """Reset all settings to defaults"""
    try:
        return _save_settings(DEFAULT_SETTINGS.copy())
    except Exception:
        return False


def get_rate_limits() -> Dict[str, Dict[str, int]]:
    """Get rate limits formatted for RateLimiter"""
    settings_data = _load_json_settings()
    rate_limits = settings_data.get("rate_limiting", DEFAULT_SETTINGS["rate_limiting"])

    return {
        "default": {
            "requests": rate_limits.get("default_requests", 100),
            "window": rate_limits.get("default_window", 3600),
        },
        "trial": {
            "requests": rate_limits.get("trial_requests", 20),
            "window": rate_limits.get("trial_window", 3600),
        },
        "premium": {
            "requests": rate_limits.get("premium_requests", 1000),
            "window": rate_limits.get("premium_window", 3600),
        },
    }
