import asyncio
import logging
import re

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from hfzy.config import (
    get_hfzy_settings,
    load_hfzy_dict,
    reload_hfzy_settings,
    save_hfzy_dict,
)
from hfzy.episode_count import RssUnavailable, count_rss_episodes
from hfzy.tmdb_info import (
    apply_tmdb_record,
    bangumi_from_tmdb,
    fetch_tmdb_record,
    normalize_tmdb_hint,
)
from module.api.deps import get_context
from module.api.response import u_response
from module.core import AppContext
from module.models import RSSItem
from module.models.response import ResponseModel
from module.rss.analyser import RSSAnalyser
from module.security.api import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extensions/hfzy", tags=["hfzy-extension"])


class RssEpisodeCountBody(BaseModel):
    rss_link: str = ""
    rss_filter: str | list | None = Field(default=None, alias="filter")
    season: int = 1
    episode_type: str = "episode"

    model_config = {"populate_by_name": True}


@router.get("/config", dependencies=[Depends(get_current_user)])
async def get_hfzy_config():
    return load_hfzy_dict()


@router.patch("/config", dependencies=[Depends(get_current_user)])
async def update_hfzy_config(
    body: dict = Body(...),
    ctx: AppContext = Depends(get_context),
):
    try:
        await asyncio.to_thread(save_hfzy_dict, body)
        reload_hfzy_settings(ctx.settings)
        return JSONResponse(
            status_code=200,
            content={
                "msg_en": "Misc features updated.",
                "msg_zh": "杂项功能已更新。",
            },
        )
    except Exception as exc:
        logger.warning("[HFZY] Config update failed: %s", exc)
        return JSONResponse(
            status_code=406,
            content={
                "msg_en": "Misc features update failed.",
                "msg_zh": "杂项功能更新失败。",
            },
        )


@router.post("/rss-episode-count", dependencies=[Depends(get_current_user)])
async def rss_episode_count(body: RssEpisodeCountBody):
    settings = get_hfzy_settings()
    if not settings.rss_episode_count and not settings.rss_filter_hit:
        raise HTTPException(status_code=404, detail="RSS episode count is disabled")
    url = body.rss_link.strip()
    if not url:
        return JSONResponse(
            status_code=400,
            content={
                "msg_en": "RSS link is empty.",
                "msg_zh": "RSS 链接为空。",
            },
        )
    try:
        return await count_rss_episodes(url, body.rss_filter)
    except re.error:
        return JSONResponse(
            status_code=400,
            content={
                "msg_en": "Invalid filter.",
                "msg_zh": "过滤规则无效。",
            },
        )
    except RssUnavailable:
        return JSONResponse(
            status_code=406,
            content={
                "msg_en": "Failed to read the RSS feed.",
                "msg_zh": "读取 RSS 失败。",
            },
        )


class TmdbRssAnalysisBody(BaseModel):
    url: str = ""
    name: str | None = None
    aggregate: bool = False
    parser: str = "tmdb"
    tmdb_media_type: str = "tv"
    tmdb_id: str = ""


@router.post("/rss-analysis", dependencies=[Depends(get_current_user)])
async def rss_analysis(body: TmdbRssAnalysisBody):
    """Parse an RSS link, then replace the title with a chosen TMDB id."""
    if not get_hfzy_settings().tmdb_info:
        raise HTTPException(status_code=404, detail="TMDB info is disabled")
    if body.aggregate:
        return JSONResponse(
            status_code=400,
            content={
                "msg_en": "Aggregate RSS does not use a TMDB id.",
                "msg_zh": "聚合 RSS 不使用 TMDB 信息。",
            },
        )
    try:
        hint = normalize_tmdb_hint(body.tmdb_media_type, body.tmdb_id)
    except ValueError as exc:
        invalid_id = str(exc) == "id"
        return JSONResponse(
            status_code=400,
            content={
                "msg_en": "TMDB id must be a number."
                if invalid_id
                else "Unknown TMDB type.",
                "msg_zh": "TMDB 编号需要是数字。" if invalid_id else "不认识的 TMDB 类型。",
            },
        )
    if hint is None:
        return JSONResponse(
            status_code=400,
            content={
                "msg_en": "TMDB id is empty.",
                "msg_zh": "没有填写 TMDB 编号。",
            },
        )
    media_type, tmdb_id = hint
    info = await fetch_tmdb_record(media_type, tmdb_id)
    if info is None:
        return JSONResponse(
            status_code=406,
            content={
                "msg_en": "TMDB id was not found.",
                "msg_zh": "没有找到这个 TMDB 编号。",
            },
        )
    rss = RSSItem(
        url=body.url.strip(),
        name=body.name,
        aggregate=False,
        parser=body.parser or "tmdb",
    )
    # The id is the title source. A filled name, then the filename, only fill
    # the group, season, and filter when the feed can be parsed.
    data = await RSSAnalyser().link_to_data(rss)
    if isinstance(data, ResponseModel):
        return bangumi_from_tmdb(info, media_type, rss.url)
    if not getattr(data, "rss_link", None):
        data.rss_link = rss.url
    return apply_tmdb_record(data, media_type, info)
