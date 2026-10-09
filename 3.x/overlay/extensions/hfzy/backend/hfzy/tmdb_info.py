"""Optional TMDB id lookup for the add-RSS form.

The stock analyser searches TMDB by the parsed title. When the form supplies
a type and id, that record replaces the title, year, and poster. Aggregate
RSS does not use this hint.
"""

import re

from module.conf import settings
from module.network import RequestContent
from module.parser.analyser.tmdb_parser import LANGUAGE, _api_key, _tmdb_url
from module.utils import save_image

TMDB_MEDIA_TYPES = ("tv", "movie")


def normalize_tmdb_hint(media_type: object, tmdb_id: object) -> tuple[str, str] | None:
    """Return ``(type, id)`` or None when the id was left empty.

    An empty id means the field is optional and the title search still runs.
    A non-numeric id or an unknown type is rejected.
    """
    text = str(tmdb_id or "").strip()
    if not text:
        return None
    if not text.isdigit():
        raise ValueError("id")
    kind = str(media_type or "tv").strip().lower()
    if kind not in TMDB_MEDIA_TYPES:
        raise ValueError("type")
    return kind, text


async def fetch_tmdb_record(media_type: str, tmdb_id: str) -> dict | None:
    language = LANGUAGE.get(settings.rss_parser.language, "zh-CN")
    url = (
        f"{_tmdb_url()}/3/{media_type}/{tmdb_id}"
        f"?api_key={_api_key()}&language={language}"
    )
    async with RequestContent() as req:
        info = await req.get_json(url)
        if not isinstance(info, dict) or not info.get("id"):
            return None
        poster_path = info.get("poster_path")
        poster_link = None
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w780{poster_path}"
            img = await req.get_content(poster_url)
            if img:
                poster_link = await save_image(img, "jpg", source_url=poster_url)
        info["_poster_link"] = poster_link
        return info


def title_source(tmdb_id: str, name: str | None) -> str:
    """Add-RSS lookup order: TMDB id, then the optional name, then the filename."""
    if str(tmdb_id or "").strip():
        return "tmdb"
    if str(name or "").strip():
        return "name"
    return "auto"


def bangumi_from_tmdb(info: dict, media_type: str, rss_url: str):
    """Build a subscription when the filename cannot be parsed."""
    from module.models import Bangumi

    data = Bangumi(rss_link=rss_url)
    apply_tmdb_record(data, media_type, info)
    if data.official_title and data.official_title != "official_title":
        data.title_raw = data.official_title
    return data


def apply_tmdb_record(data, media_type: str, info: dict):
    """Write the TMDB record onto a parsed bangumi or movie."""
    if media_type == "movie":
        title = info.get("title") or info.get("original_title") or ""
        year = (info.get("release_date") or "").split("-")[0]
    else:
        title = info.get("name") or info.get("original_name") or ""
        year = (info.get("first_air_date") or "").split("-")[0]
    title = re.sub(r"[/:.\\]", " ", title).strip()
    if title:
        data.official_title = title
    if year:
        movie_record = media_type == "movie" and not hasattr(data, "episode_type")
        if movie_record or isinstance(getattr(data, "year", None), int):
            try:
                data.year = int(year)
            except ValueError:
                pass
        else:
            data.year = year
    poster_link = info.get("_poster_link")
    if poster_link:
        data.poster_link = poster_link
    if media_type == "movie" and hasattr(data, "episode_type"):
        data.episode_type = "movie"
    return data
