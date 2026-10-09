"""Rename specials as season 0 when the subscription type is special.

Core rename only skips the episode number for movies. A special such as
``TVSP`` has no ``[08]`` / ``- 01`` marker, so the stock rules return nothing
and the file keeps its release name. This patch stays in the plugin.
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_BRACKET_RE = re.compile(r"[\[\(（【].*?[\]\)）】]")
_SPECIAL_NUMBERED = re.compile(
    r"(?<![A-Za-z0-9])(TVSP|OVA|OAD|SP|Special)\s*[-_.]?\s*(\d{1,4})(?![A-Za-z0-9])",
    re.I,
)
_SPECIAL_MARKER = re.compile(
    r"(?<![A-Za-z0-9])(TVSP|OVA|OAD|SP|Special)(?![A-Za-z0-9])",
    re.I,
)
_SPECIAL_CJK = re.compile(r"番外篇?|特別篇|特别篇")


def special_episode_number(name: str) -> int | None:
    """Episode for a special marker, or None when the name is not a special.

    ``SP02`` and ``OVA 1`` keep that number. A bare ``TVSP`` / ``Special`` is
    the first special.
    """
    numbered = _SPECIAL_NUMBERED.search(name or "")
    if numbered:
        return int(numbered.group(2))
    if _SPECIAL_MARKER.search(name or "") or _SPECIAL_CJK.search(name or ""):
        return 1
    return None


def _special_title(name: str) -> str:
    stem = Path(name).stem
    title = _BRACKET_RE.sub(" ", stem)
    title = _SPECIAL_NUMBERED.sub(" ", title)
    title = _SPECIAL_MARKER.sub(" ", title)
    title = _SPECIAL_CJK.sub(" ", title)
    title = re.sub(r"\s+", " ", title).strip(" -/")
    return title or stem


def _with_special_season(parsed):
    if hasattr(parsed, "model_copy"):
        return parsed.model_copy(update={"season": 0, "episode_type": "special"})
    parsed.season = 0
    parsed.episode_type = "special"
    return parsed


def build_special_file(torrent_path: str, torrent_name: str | None, file_type: str):
    """Build a season-0 file from a special marker, or return None."""
    from module.models import EpisodeFile, SubtitleFile
    from module.parser.analyser.torrent_parser import get_group, get_subtitle_lang

    match_name = torrent_name if torrent_name is not None else Path(torrent_path).name
    episode = special_episode_number(match_name)
    if episode is None and torrent_name is not None:
        episode = special_episode_number(Path(torrent_path).name)
        if episode is not None:
            match_name = Path(torrent_path).name
    if episode is None:
        return None

    group, _title = get_group(match_name)
    title = _special_title(match_name)
    suffix = Path(torrent_path).suffix
    if file_type == "media":
        return EpisodeFile(
            media_path=torrent_path,
            group=group,
            title=title,
            season=0,
            episode=episode,
            suffix=suffix,
            episode_type="special",
        )
    if file_type == "subtitle":
        language = get_subtitle_lang(Path(torrent_path).name)
        if not language:
            return None
        return SubtitleFile(
            media_path=torrent_path,
            group=group,
            title=title,
            season=0,
            episode=episode,
            language=language,
            suffix=suffix,
            episode_type="special",
        )
    return None


def apply_special_rename(parsed, torrent_path: str, torrent_name, file_type: str):
    """Force season 0. Fall back to the special marker when core parsing failed."""
    if parsed is not None:
        return _with_special_season(parsed)
    return build_special_file(torrent_path, torrent_name, file_type)


def install_special_rename() -> None:
    from module.parser.title_parser import TitleParser

    if getattr(TitleParser, "_hfzy_special_patched", False):
        return
    raw = TitleParser.__dict__["torrent_parser"]
    original = raw.__func__ if isinstance(raw, staticmethod) else raw

    def torrent_parser(
        torrent_path: str,
        torrent_name: str | None = None,
        season: int | None = None,
        file_type: str = "media",
        episode_type: str = "episode",
    ):
        parsed = original(
            torrent_path, torrent_name, season, file_type, episode_type
        )
        if episode_type != "special":
            return parsed
        from hfzy.config import get_hfzy_settings

        if not get_hfzy_settings().special_rename:
            return parsed
        try:
            return apply_special_rename(
                parsed, torrent_path, torrent_name, file_type
            )
        except Exception:
            logger.exception("HFZY special rename failed for %s", torrent_path)
            return parsed

    TitleParser.torrent_parser = staticmethod(torrent_parser)
    TitleParser._hfzy_special_patched = True
