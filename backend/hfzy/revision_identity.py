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


def _videos_or_all(files: list[dict]) -> list[dict]:
    videos = [
        item
        for item in files or []
        if PurePosixPath(str(item.get("name") or "")).suffix.lower() in _VIDEO_SUFFIXES
    ]
    return videos or list(files or [])


async def _reopen_stale_conflict(
    renamer,
    *,
    info: dict,
    files: list[dict],
    media_path: str,
    bangumi_name: str,
    season: int,
    method: str,
    episode_offset: int,
    episode_type: str,
    season_offset: int = 0,
    **_ignored,
) -> None:
    """Drop a hold that a later parser or policy can decide again."""

    import json

    from module.conf import settings
    from module.database import Database
    from module.database.bangumi import normalize_save_path
    from module.manager.revision_policy import is_strict_upgrade, parse_revision_identity

    import inspect

    prepare_kwargs = {
        "torrent_name": info["name"],
        "media_path": media_path,
        "bangumi_name": bangumi_name,
        "method": method,
        "season": season,
        "episode_offset": episode_offset,
        "episode_type": episode_type,
        "season_offset": season_offset,
    }
    accepted = inspect.signature(renamer._prepare_media_rename).parameters
    prepared = renamer._prepare_media_rename(
        **{key: value for key, value in prepare_kwargs.items() if key in accepted}
    )
    if prepared is None:
        return
    save_path = normalize_save_path(info.get("save_path", ""))
    async with Database() as db:
        active = await db.rename_operation.get_by_target(
            downloader_type=renamer._downloader_type(),
            save_path=save_path,
            target_path=prepared.target_path,
        )
    if active is None or active.state != "conflict":
        return
    if active.new_task_id != info.get("hash"):
        return
    reopen = False
    if (
        active.last_error == "revision conflict policy is hold"
        and settings.bangumi_manage.revision_conflict_policy == "replace"
    ):
        reopen = True
    else:
        bangumi_id = renamer._parse_bangumi_id_from_tags(info.get("tags"))
        if active.last_error == "revision identity is incomplete":
            new_identity = parse_revision_identity(
                info.get("name", ""),
                bangumi_id=bangumi_id,
                default_season=season,
                episode_offset=episode_offset,
            )
            old_name = ""
            try:
                old_name = (
                    json.loads(active.revision_metadata or "{}").get("old_torrent_name")
                    or ""
                )
            except json.JSONDecodeError:
                old_name = ""
            old_identity = (
                parse_revision_identity(
                    old_name,
                    bangumi_id=bangumi_id,
                    default_season=season,
                    episode_offset=episode_offset,
                )
                if old_name
                else None
            )
            reopen = bool(
                new_identity
                and old_identity
                and is_strict_upgrade(old_identity, new_identity)
            )
        elif active.last_error == "automatic replacement requires two single-file torrents":
            if active.old_task_id:
                from hfzy.config import get_hfzy_settings

                def counted(items: list[dict]) -> list[dict]:
                    if get_hfzy_settings().revision_single_video:
                        return _videos_or_all(items)
                    return list(items or [])

                old_files = await renamer.client.get_torrent_files(active.old_task_id)
                reopen = len(counted(files)) == 1 and len(counted(old_files)) == 1
    if not reopen:
        return
    async with Database() as db:
        await db.rename_operation.delete(active.id)


def _install_renamer_guards() -> None:
    """Count videos and reopen stale holds without editing renamer.py."""

    import module.manager.renamer as renamer

    if getattr(renamer.Renamer, "_hfzy_process_patched", False):
        return
    original_process = renamer.Renamer._process_single_torrent
    original_find = renamer.Renamer._find_revision_owners

    async def _find_revision_owners(self, *args, **kwargs):
        identity, owners = await original_find(self, *args, **kwargs)
        from hfzy.config import get_hfzy_settings

        if not get_hfzy_settings().revision_single_video:
            return identity, owners
        narrowed = [
            renamer.RevisionOwner(
                info=owner.info,
                files=_videos_or_all(owner.files),
                identity=owner.identity,
            )
            for owner in owners
        ]
        return identity, narrowed

    async def _process_single_torrent(self, **kwargs):
        from hfzy.config import get_hfzy_settings

        if get_hfzy_settings().revision_single_video and "files" in kwargs:
            kwargs["files"] = _videos_or_all(kwargs["files"])
        try:
            await _reopen_stale_conflict(self, **kwargs)
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.exception("HFZY could not reopen a stale revision hold")
        return await original_process(self, **kwargs)

    renamer.Renamer._find_revision_owners = _find_revision_owners
    renamer.Renamer._process_single_torrent = _process_single_torrent
    renamer.Renamer._hfzy_process_patched = True


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

    policy.parse_revision_identity = parse_revision_identity
    renamer = sys.modules.get("module.manager.renamer")
    if renamer is not None:
        renamer.parse_revision_identity = parse_revision_identity
    policy._hfzy_revision_patched = True
    _install_renamer_guards()
