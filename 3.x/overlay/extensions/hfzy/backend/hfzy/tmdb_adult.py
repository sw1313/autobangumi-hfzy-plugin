"""Include adult TMDB titles when the misc switch is on."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def apply_include_adult(url: str, enabled: bool) -> str:
    """Rewrite a TMDB search URL's include_adult flag."""
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key != "include_adult"
    ]
    query.append(("include_adult", "true" if enabled else "false"))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    )


class AdultFlag:
    """Remember the last flag so a toggle can drop stale TMDB results."""

    def __init__(self) -> None:
        self.value: bool | None = None

    def changed(self, enabled: bool) -> bool:
        if self.value is None:
            self.value = enabled
            return False
        if self.value == enabled:
            return False
        self.value = enabled
        return True


_adult_flag = AdultFlag()


def _tmdb_module():
    """Return the TMDB parser module.

    ``analyser/__init__.py`` does ``from .tmdb_parser import tmdb_parser``, so
    the package attribute is the function and a normal import binds that
    function instead of the module.
    """
    import sys

    name = "module.parser.analyser.tmdb_parser"
    module = sys.modules.get(name)
    if module is not None and hasattr(module, "search_url"):
        return module
    import importlib

    imported = importlib.import_module(name)
    if hasattr(imported, "search_url"):
        return imported
    module = sys.modules.get(name)
    if module is None or not hasattr(module, "search_url"):
        raise RuntimeError("TMDB parser module is not loaded")
    return module


def install_tmdb_adult() -> None:
    tmdb = _tmdb_module()

    if getattr(tmdb, "_hfzy_tmdb_adult_patched", False):
        return

    original_search = tmdb.search_url
    original_movie = tmdb.search_movie_url

    def _enabled() -> bool:
        from hfzy.config import get_hfzy_settings

        return bool(get_hfzy_settings().tmdb_include_adult)

    def _prepare(url: str) -> str:
        enabled = _enabled()
        if _adult_flag.changed(enabled):
            tmdb.reset_cache()
        return apply_include_adult(url, enabled)

    def search_url(title, key="zh"):
        return _prepare(original_search(title, key))

    def search_movie_url(title, key="zh"):
        return _prepare(original_movie(title, key))

    tmdb.search_url = search_url
    tmdb.search_movie_url = search_movie_url
    tmdb._hfzy_tmdb_adult_patched = True
