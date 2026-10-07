"""Let the season typed in Add RSS win over the season in the filename."""

import sys
from types import SimpleNamespace


def prefer_form_season(matched: bool, enabled: bool, aligned_ok: bool) -> bool:
    """Keep a release when the typed season is the only mismatch."""
    if matched:
        return True
    return enabled and aligned_ok


def _aligned_release_ok(torrent_name: str, bangumi) -> bool:
    from module.database import bangumi as bangumi_mod
    from module.parser.analyser.selector import parse_configured_release_title

    release = parse_configured_release_title(torrent_name)
    if release is None or release.season is None:
        return False
    aligned = SimpleNamespace(
        episode_type=getattr(bangumi, "episode_type", "episode"),
        season=release.season,
    )
    return bangumi_mod._release_matches_bangumi(release, aligned)


def install_form_season() -> None:
    from module.database import bangumi as bangumi_mod

    if getattr(bangumi_mod, "_hfzy_form_season_patched", False):
        return

    original = bangumi_mod.release_fits_bangumi

    def release_fits_bangumi(torrent_name: str, bangumi) -> bool:
        from hfzy.config import get_hfzy_settings

        matched = original(torrent_name, bangumi)
        enabled = bool(get_hfzy_settings().rss_form_season)
        aligned_ok = False
        if not matched and enabled:
            aligned_ok = _aligned_release_ok(torrent_name, bangumi)
        return prefer_form_season(matched, enabled, aligned_ok)

    bangumi_mod.release_fits_bangumi = release_fits_bangumi
    for mod_name in ("module.manager.collector", "module.rss.engine"):
        mod = sys.modules.get(mod_name)
        if mod is not None and getattr(mod, "release_fits_bangumi", None) is original:
            mod.release_fits_bangumi = release_fits_bangumi
    bangumi_mod._hfzy_form_season_patched = True
