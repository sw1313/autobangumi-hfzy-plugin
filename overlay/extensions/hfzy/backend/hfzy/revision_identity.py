"""Recognize a bracket revision when the release group was not parsed.

``[Nekomoe kissaten]...[v2]`` already yields revision 2. The identity is still
incomplete because the group name contains a space. The first bracket is used
as the group so it can be compared with the unmarked release.

A subtitle or font archive beside the only video is not a second episode.
"""

import re
import sys
from pathlib import PurePosixPath

_VIDEO_SUFFIXES = {".mp4", ".mkv", ".avi", ".m4v"}
_BRACKET_GROUP = re.compile(r"\[([^\[\]]+)\]")


def count_episode_videos(files: list[dict], *, enabled: bool) -> int:
    """Count videos when enabled, otherwise every torrent file."""

    if not enabled:
        return len(files or [])
    videos = [
        item
        for item in files or []
        if PurePosixPath(str(item.get("name") or "")).suffix.lower() in _VIDEO_SUFFIXES
    ]
    if not videos:
        return len(files or [])
    return len(videos)


def identity_with_bracket_group(
    torrent_name: str,
    *,
    bangumi_id: int | None,
    default_season: int,
    episode_offset: int = 0,
):
    """Build a revision identity, filling a missing group from the first bracket."""

    from module.manager.revision_policy import (
        RevisionIdentity,
        _adjust_episode,
        _normalize_label,
    )
    from module.parser.analyser.selector import parse_configured_release_title
    from module.parser.release_policy import preference_identity, preference_revision

    if bangumi_id is None:
        return None
    release = parse_configured_release_title(torrent_name)
    if release is None:
        return None
    identity = preference_identity(release, default_season=default_season)
    if identity is None:
        return None
    group = _normalize_label(release.group)
    if not group:
        match = _BRACKET_GROUP.search(torrent_name)
        group = _normalize_label(match.group(1) if match else "")
    resolution = _normalize_label(release.resolution)
    if not group or not resolution:
        return None
    media_type, season, episode = identity
    return RevisionIdentity(
        bangumi_id=bangumi_id,
        media_type=media_type,
        season=season,
        episode=_adjust_episode(episode, episode_offset),
        group=group,
        resolution=resolution,
        revision=preference_revision(release),
    )


def install_revision_identity() -> None:
    import module.manager.revision_policy as policy

    if getattr(policy, "_hfzy_revision_patched", False):
        return

    original_parse = policy.parse_revision_identity

    def parse_revision_identity(
        torrent_name: str,
        *,
        bangumi_id: int | None,
        default_season: int,
        episode_offset: int = 0,
    ):
        found = original_parse(
            torrent_name,
            bangumi_id=bangumi_id,
            default_season=default_season,
            episode_offset=episode_offset,
        )
        if found is not None:
            return found
        from hfzy.config import get_hfzy_settings

        if not get_hfzy_settings().revision_group_fallback:
            return None
        return identity_with_bracket_group(
            torrent_name,
            bangumi_id=bangumi_id,
            default_season=default_season,
            episode_offset=episode_offset,
        )

    def revision_file_count(files: list[dict]) -> int:
        from hfzy.config import get_hfzy_settings

        return count_episode_videos(
            files,
            enabled=bool(get_hfzy_settings().revision_single_video),
        )

    policy.parse_revision_identity = parse_revision_identity
    policy.revision_file_count = revision_file_count
    renamer = sys.modules.get("module.manager.renamer")
    if renamer is not None:
        renamer.parse_revision_identity = parse_revision_identity
        renamer.revision_file_count = revision_file_count
    policy._hfzy_revision_patched = True
