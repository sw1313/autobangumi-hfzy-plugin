import posixpath
from datetime import timedelta
from pathlib import Path, PurePosixPath

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from module.downloader import DownloadClient
from module.security.api import get_current_user
from module.security.jwt import create_access_token, verify_token

from hfzy.config import get_hfzy_settings

router = APIRouter(prefix="/extensions/player", tags=["extensions-player"])

MEDIA_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
    ".m4v",
    ".ts",
    ".flv",
    ".wmv",
}


class PlayerMediaFile(BaseModel):
    name: str
    path: str
    url: str
    size: int = 0


class PlayerMediaResponse(BaseModel):
    files: list[PlayerMediaFile]


def _ensure_player_enabled() -> None:
    if not get_hfzy_settings().player_enable:
        raise HTTPException(status_code=404, detail="Player is disabled")


def _join_media_path(save_path: str, file_name: str) -> str:
    if file_name.startswith("/"):
        return posixpath.normpath(file_name)
    return posixpath.normpath(
        posixpath.join(save_path.replace("\\", "/").rstrip("/"), file_name)
    )


def _is_media_file(path: str) -> bool:
    return PurePosixPath(path).suffix.lower() in MEDIA_EXTENSIONS


def _stream_token(torrent_hash: str, path: str) -> str:
    return create_access_token(
        {"sub": "player_stream", "hash": torrent_hash, "path": path},
        expires_delta=timedelta(hours=6),
    )


def _verify_stream_token(token: str, torrent_hash: str, path: str) -> None:
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid stream token")
    if (
        payload.get("sub") != "player_stream"
        or payload.get("hash") != torrent_hash
        or payload.get("path") != path
    ):
        raise HTTPException(status_code=403, detail="Stream token mismatch")


def _stream_url(torrent_hash: str, index: int, path: str) -> str:
    token = _stream_token(torrent_hash, path)
    return (
        f"/api/v1/extensions/player/torrents/{torrent_hash}/media/"
        f"{index}/stream?token={token}"
    )


async def _media_files_for_hash(torrent_hash: str) -> list[PlayerMediaFile]:
    torrent_hash = torrent_hash.lower()
    async with DownloadClient() as client:
        torrents = await client.get_torrent_info(
            category="Bangumi", status_filter=None
        )
        torrent = next(
            (t for t in torrents if str(t.get("hash", "")).lower() == torrent_hash),
            None,
        )
        if torrent is None:
            raise HTTPException(status_code=404, detail="Torrent not found")

        save_path = str(torrent.get("save_path") or "")
        files = await client.get_torrent_files(torrent_hash)

    media_files: list[PlayerMediaFile] = []
    for file_info in files:
        name = str(file_info.get("name") or "")
        if not name or not _is_media_file(name):
            continue
        full_path = _join_media_path(save_path, name)
        media_files.append(
            PlayerMediaFile(
                name=PurePosixPath(name).name,
                path=full_path,
                url="",
                size=int(file_info.get("size") or 0),
            )
        )

    media_files.sort(key=lambda item: item.size, reverse=True)
    for index, media_file in enumerate(media_files):
        media_file.url = _stream_url(torrent_hash, index, media_file.path)
    return media_files


@router.get(
    "/torrents/{torrent_hash}/media",
    response_model=PlayerMediaResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_torrent_media(torrent_hash: str):
    _ensure_player_enabled()
    return PlayerMediaResponse(files=await _media_files_for_hash(torrent_hash))


@router.get("/torrents/{torrent_hash}/media/{index}/stream")
async def stream_torrent_media(
    torrent_hash: str,
    index: int,
    token: str = Query(...),
):
    _ensure_player_enabled()
    media_files = await _media_files_for_hash(torrent_hash)
    if index < 0 or index >= len(media_files):
        raise HTTPException(status_code=404, detail="Media file not found")

    media_file = media_files[index]
    _verify_stream_token(token, torrent_hash.lower(), media_file.path)

    path = Path(media_file.path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found on disk")
    return FileResponse(path)
