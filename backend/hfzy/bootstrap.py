"""Runtime bootstrap for the misc plugin. Does not edit upstream source."""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_INSTALLED = False


def _ensure_path() -> None:
    app_dir = Path(os.environ.get("AB_APP_DIR", "/app"))
    if app_dir.is_dir():
        app_str = str(app_dir)
        if app_str not in sys.path:
            sys.path.insert(0, app_str)

    roots = [Path("/extensions/hfzy/backend")]
    try:
        roots.append(Path(__file__).resolve().parents[1])
    except IndexError:
        pass
    for root in roots:
        if (root / "hfzy" / "__init__.py").is_file():
            root_str = str(root)
            if root_str not in sys.path:
                sys.path.insert(0, root_str)
            return
    logger.warning(
        "HFZY extension backend not found; checked: %s",
        ", ".join(str(root) for root in roots),
    )


def _patch_app_context_build() -> None:
    import module.core.context as ctx_mod

    original = ctx_mod.AppContext.build.__func__

    @classmethod
    def build(cls, settings_obj):
        from hfzy.config import attach_hfzy_settings

        attach_hfzy_settings(settings_obj)
        return original(cls, settings_obj)

    ctx_mod.AppContext.build = build  # type: ignore[method-assign]


def _patch_settings_reload() -> None:
    import module.core.context as ctx_mod

    original = ctx_mod.AppContext._reload_settings_unlocked

    async def _reload_settings_unlocked(self):
        await original(self)
        from hfzy.config import attach_hfzy_settings

        attach_hfzy_settings(self.settings)

    ctx_mod.AppContext._reload_settings_unlocked = _reload_settings_unlocked


def _install_page_script() -> None:
    """每个页面都加载界面脚本。4.0 只在首页小组件挂载时才会加载它。"""
    import sys

    from fastapi.responses import FileResponse, HTMLResponse

    app = getattr(sys.modules.get("__main__"), "app", None)
    if app is None:
        return
    tag = '<script type="module" src="/api/v1/plugins/hfzy/web/ui.js"></script>'
    index = Path(os.environ.get("AB_APP_DIR", "/app")) / "dist" / "index.html"
    for route in app.router.routes:
        endpoint = getattr(route, "endpoint", None)
        dependant = getattr(route, "dependant", None)
        current = getattr(dependant, "call", None) or endpoint
        if getattr(current, "__name__", "") != "html":
            continue
        if getattr(current, "_hfzy_script", False):
            return
        previous = current

        def html(request, path: str = "", _previous=previous, _index=index):
            result = _previous(request, path)
            if isinstance(result, FileResponse):
                return result
            if isinstance(result, HTMLResponse):
                body = result.body.decode("utf-8")
            else:
                body = _index.read_text(encoding="utf-8")
            if tag not in body and "</head>" in body:
                body = body.replace("</head>", f"{tag}</head>", 1)
            return HTMLResponse(
                body, headers={"Content-Security-Policy": "script-src 'self'"}
            )

        html.__name__ = "html"
        html._hfzy_script = True
        route.endpoint = html
        if dependant is not None:
            dependant.call = html
        logger.info("HFZY page script attached")
        return


def _register_api_routes() -> None:
    import module.api as api_mod
    from hfzy.api import router
    from hfzy.player_api import router as player_router

    api_mod.v1.include_router(router)
    api_mod.v1.include_router(player_router)


def is_installed() -> bool:
    return _INSTALLED


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _ensure_path()
    try:
        import hfzy  # noqa: F401
        from hfzy.config import attach_hfzy_settings
        from hfzy.revision_identity import install_revision_identity
        from hfzy.rss_priority import install_rss_name_priority
        from hfzy.season_priority import install_form_season
        from hfzy.special_rename import install_special_rename
        from hfzy.tmdb_adult import install_tmdb_adult
        from module.conf import settings
    except ImportError as exc:
        logger.error("HFZY extension not loaded: %s", exc)
        return
    try:
        _patch_app_context_build()
        _patch_settings_reload()
        attach_hfzy_settings(settings)
        install_rss_name_priority()
        try:
            install_revision_identity()
        except Exception:
            logger.exception("HFZY revision identity patch failed")
        try:
            install_tmdb_adult()
        except Exception:
            logger.exception("HFZY TMDB adult patch failed")
        try:
            install_form_season()
        except Exception:
            logger.exception("HFZY form season patch failed")
        try:
            install_special_rename()
        except Exception:
            logger.exception("HFZY special rename patch failed")
        _register_api_routes()
        try:
            _install_page_script()
        except Exception:
            logger.exception("HFZY page script injection failed")
    except Exception:
        logger.exception("HFZY bootstrap failed")
        return
    _INSTALLED = True
    logger.info("HFZY misc extension installed")
