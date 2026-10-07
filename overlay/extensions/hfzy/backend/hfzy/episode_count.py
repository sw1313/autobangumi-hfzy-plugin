"""Count RSS items left after the bangumi exclude filter."""

from __future__ import annotations

import re

# Episode tokens only. Resolution like [1080P] stays, because the trailing
# letter keeps it out of the bracket pattern, and 1080 is more than 3 digits.
_EPISODE_MARK = re.compile(
    r"\[(?:e|ep)?0*\d{1,3}(?:v\d+)?\]"
    r"|【0*\d{1,3}(?:v\d+)?】"
    r"|第\s*0*\d{1,3}\s*[集话話]"
    r"|s\d{1,2}\s*e\s*0*\d{1,3}"
    r"|(?<![\d])(?:e|ep)\s*0*\d{1,3}(?![\d])"
    r"|\s+-\s+0*\d{1,3}(?:v\d+)?(?=\s|\[|$)",
    re.IGNORECASE,
)
# The last episode often gains [END]/[Fin]/[完结]. That is still the same release.
_FINISH_MARK = re.compile(
    r"\[(?:end|fin|final|完结|完結|完)\]|【(?:end|fin|final|完结|完結|完)】",
    re.IGNORECASE,
)
# A revision such as [v2] or a trailing ".mp4.torrent" is not a new release.
_REVISION_MARK = re.compile(
    r"\[v\d+\]|【v\d+】|(?<![\w\[])v\d+(?!\w)",
    re.IGNORECASE,
)
_FILE_SUFFIX = re.compile(
    r"(?:\.(?:mp4|mkv|avi))?\.torrent$|\.(?:mp4|mkv|avi)$",
    re.IGNORECASE,
)


class RssUnavailable(Exception):
    """The feed could not be downloaded or parsed."""


def exclude_pattern(filter_value) -> str:
    """Match ``SeasonCollector``: comma-separated terms become one regex."""
    if filter_value is None:
        return ""
    if isinstance(filter_value, (list, tuple)):
        text = ",".join(str(item) for item in filter_value)
    else:
        text = str(filter_value)
    return text.replace(",", "|")


def compile_exclude(pattern: str) -> re.Pattern[str] | None:
    if not pattern:
        return None
    return re.compile(pattern)


def filter_terms(filter_value) -> list[str]:
    if filter_value is None:
        return []
    if isinstance(filter_value, (list, tuple)):
        return [str(item) for item in filter_value if str(item).strip()]
    return [part for part in str(filter_value).split(",") if part.strip()]


def matched_filter_terms(titles: list[str], filter_value) -> list[str]:
    """Filter terms that match at least one RSS title.

    Each term is compiled on its own, the same way the joined exclude regex
    treats it. A term that matches nothing is left unmarked.
    """
    hits: list[str] = []
    seen: set[str] = set()
    for term in filter_terms(filter_value):
        if term in seen:
            continue
        try:
            regex = re.compile(term)
        except re.error:
            continue
        if any(regex.search(title) for title in titles):
            seen.add(term)
            hits.append(term)
    return hits


def version_key(title: str) -> str:
    """Identity of a release with episode, finale, and revision marks removed."""
    stripped = _FILE_SUFFIX.sub("", title.strip())
    stripped = _FINISH_MARK.sub(" ", stripped)
    stripped = _REVISION_MARK.sub(" ", stripped)
    stripped = _EPISODE_MARK.sub(" ", stripped)
    stripped = re.sub(r"\[\s*\]|【\s*】", " ", stripped)
    return re.sub(r"\s+", " ", stripped).strip().casefold()


def ab_can_download(title: str) -> bool:
    """False for batches and collections AutoBangumi will not add.

    A title the parser cannot read is kept, so an unknown name is not hidden.
    """
    from module.parser.analyser.selector import parse_configured_release_title
    from module.parser.release_policy import persistence_target

    release = parse_configured_release_title(title)
    if release is None:
        return True
    return persistence_target(release) is not None


def summarize_releases(
    titles: list[str], pattern: str, *, keep=None
) -> dict[str, int]:
    """Versions are distinct releases; videos are items left after filters.

    Two subtitle types of the same episode stay two versions. A finale marked
    ``[END]`` stays with the weekly episodes. ``keep`` drops titles the caller
    will not download, such as a season collection.
    """
    regex = compile_exclude(pattern)
    kept = []
    for title in titles:
        if regex is not None and regex.search(title):
            continue
        if keep is not None and not keep(title):
            continue
        kept.append(title)
    versions = {version_key(title) for title in kept}
    return {"versions": len(versions), "videos": len(kept)}


async def count_rss_episodes(url: str, filter_value) -> dict:
    pattern = exclude_pattern(filter_value)
    compile_exclude(pattern)
    from module.network import RequestContent
    from module.network.site import rss_parser

    async with RequestContent() as req:
        soup = await req.get_xml(url)
    if soup is None:
        raise RssUnavailable(url)
    titles = [title for title, _torrent_url, _homepage in rss_parser(soup)]
    summary = summarize_releases(titles, pattern, keep=ab_can_download)
    return {
        **summary,
        "hits": matched_filter_terms(titles, filter_value),
    }
