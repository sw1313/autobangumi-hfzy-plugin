"""Misc plugin settings, stored independently in ``config/hfzy.json``."""

import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

CONFIG_ROOT = Path("config")
HFZY_CONFIG_PATH = (CONFIG_ROOT / "hfzy.json").resolve()

REVISION_POLICIES = ("hold", "replace")

DEFAULT_HFZY: dict = {
    "player_enable": True,
    "rss_name_priority": True,
    "rss_episode_count": True,
    "rss_copy_fix": True,
    "rss_filter_hit": True,
    "tmdb_include_adult": True,
    "rss_form_season": True,
    "revision_conflict_policy": "hold",
    "revision_group_fallback": True,
    "revision_single_video": True,
    "downloader_filter": True,
    "special_rename": True,
    "tmdb_info": True,
}


def normalize_revision_policy(value: object) -> str:
    """Return ``hold`` or ``replace``. Anything else stays on hold."""
    if isinstance(value, str):
        policy = value.strip().lower()
        if policy in REVISION_POLICIES:
            return policy
    return "hold"


class HfzySettings(BaseModel):
    player_enable: bool = Field(True, description="Show the downloader play button")
    rss_name_priority: bool = Field(
        True,
        description="Prefer the filled RSS name for non-aggregate TMDB lookups",
    )
    rss_episode_count: bool = Field(
        True,
        description="Show how many episodes remain in the RSS after filters",
    )
    rss_copy_fix: bool = Field(
        True,
        description="Copy the RSS link when the page is opened over plain http",
    )
    rss_filter_hit: bool = Field(
        True,
        description="Outline filter terms that match at least one RSS title",
    )
    tmdb_include_adult: bool = Field(
        True,
        description="Include adult titles in TMDB TV and movie search",
    )
    rss_form_season: bool = Field(
        True,
        description="Use the season typed in Add RSS instead of the filename season",
    )
    revision_conflict_policy: str = Field(
        "hold",
        description="Hold or replace when a higher revision targets an existing episode",
    )
    revision_group_fallback: bool = Field(
        True,
        description="Use the first bracket as the release group when it was not parsed",
    )
    revision_single_video: bool = Field(
        True,
        description="Count only videos when deciding a single-episode revision replacement",
    )
    downloader_filter: bool = Field(
        True,
        description="Show a completed / incomplete filter on the downloader title row",
    )
    special_rename: bool = Field(
        True,
        description="Rename specials as season 0 when the subscription type is special",
    )
    tmdb_info: bool = Field(
        True,
        description="When the parser is TMDB, allow an optional type and id",
    )

    def model_dump(self, *args, by_alias=True, **kwargs):
        return super().model_dump(*args, by_alias=by_alias, **kwargs)


def load_hfzy_dict() -> dict:
    if not HFZY_CONFIG_PATH.exists():
        return dict(DEFAULT_HFZY)
    try:
        with open(HFZY_CONFIG_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        logger.warning("[HFZY] Cannot read %s: %s", HFZY_CONFIG_PATH, exc)
        return dict(DEFAULT_HFZY)
    result = dict(DEFAULT_HFZY)
    if isinstance(data, dict):
        result.update(
            {
                "player_enable": bool(data.get("player_enable", True)),
                "rss_name_priority": bool(data.get("rss_name_priority", True)),
                "rss_episode_count": bool(data.get("rss_episode_count", True)),
                "rss_copy_fix": bool(data.get("rss_copy_fix", True)),
                "rss_filter_hit": bool(data.get("rss_filter_hit", True)),
                "tmdb_include_adult": bool(data.get("tmdb_include_adult", True)),
                "rss_form_season": bool(data.get("rss_form_season", True)),
                "revision_conflict_policy": normalize_revision_policy(
                    data.get("revision_conflict_policy", "hold")
                ),
                "revision_group_fallback": bool(
                    data.get("revision_group_fallback", True)
                ),
                "revision_single_video": bool(data.get("revision_single_video", True)),
                "downloader_filter": bool(data.get("downloader_filter", True)),
                "special_rename": bool(data.get("special_rename", True)),
                "tmdb_info": bool(data.get("tmdb_info", True)),
            }
        )
    return result


def save_hfzy_dict(data: dict) -> dict:
    normalized = {
        "player_enable": bool(data.get("player_enable", True)),
        "rss_name_priority": bool(data.get("rss_name_priority", True)),
        "rss_episode_count": bool(data.get("rss_episode_count", True)),
        "rss_copy_fix": bool(data.get("rss_copy_fix", True)),
        "rss_filter_hit": bool(data.get("rss_filter_hit", True)),
        "tmdb_include_adult": bool(data.get("tmdb_include_adult", True)),
        "rss_form_season": bool(data.get("rss_form_season", True)),
        "revision_conflict_policy": normalize_revision_policy(
            data.get("revision_conflict_policy", "hold")
        ),
        "revision_group_fallback": bool(data.get("revision_group_fallback", True)),
        "revision_single_video": bool(data.get("revision_single_video", True)),
        "downloader_filter": bool(data.get("downloader_filter", True)),
        "special_rename": bool(data.get("special_rename", True)),
        "tmdb_info": bool(data.get("tmdb_info", True)),
    }
    HFZY_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HFZY_CONFIG_PATH, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, indent=4, ensure_ascii=False)
    return normalized


def apply_revision_policy(settings_obj, policy: str) -> None:
    """Copy the misc choice onto the renamer setting it already reads."""
    manage = getattr(settings_obj, "bangumi_manage", None)
    if manage is None or not hasattr(manage, "revision_conflict_policy"):
        return
    manage.revision_conflict_policy = normalize_revision_policy(policy)


def _bind_hfzy_settings(settings_obj, cfg: HfzySettings) -> None:
    inner = getattr(settings_obj, "__dict__", None)
    if isinstance(inner, dict):
        inner["hfzy"] = cfg
    else:
        object.__setattr__(settings_obj, "hfzy", cfg)
    apply_revision_policy(settings_obj, cfg.revision_conflict_policy)


def attach_hfzy_settings(settings_obj) -> None:
    _bind_hfzy_settings(settings_obj, HfzySettings.model_validate(load_hfzy_dict()))


def reload_hfzy_settings(settings_obj=None) -> HfzySettings:
    cfg = HfzySettings.model_validate(load_hfzy_dict())
    if settings_obj is not None:
        _bind_hfzy_settings(settings_obj, cfg)
    else:
        try:
            from module.conf import settings

            _bind_hfzy_settings(settings, cfg)
        except ImportError:
            pass
    return cfg


def get_hfzy_settings() -> HfzySettings:
    try:
        from module.conf import settings

        cfg = getattr(settings, "hfzy", None)
        if cfg is not None:
            return cfg
    except ImportError:
        pass
    return HfzySettings.model_validate(load_hfzy_dict())
