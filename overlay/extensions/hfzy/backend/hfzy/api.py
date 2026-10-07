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
from module.api.deps import get_context
from module.core import AppContext
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
