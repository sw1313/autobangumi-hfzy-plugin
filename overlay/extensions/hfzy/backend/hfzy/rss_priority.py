"""Prefer a filled RSS name when looking up non-aggregate TMDB titles."""


def preferred_query_title(rss, fallback: str, *, enabled: bool) -> str:
    if not enabled:
        return fallback
    name = (getattr(rss, "name", None) or "").strip()
    if name and not bool(getattr(rss, "aggregate", False)):
        return name
    return fallback


def install_rss_name_priority() -> None:
    import module.rss.analyser as analyser_mod

    analyser_cls = analyser_mod.RSSAnalyser
    if getattr(analyser_cls, "_hfzy_rss_name_priority_patched", False):
        return

    original_bangumi = analyser_cls.official_title_parser
    original_movie = getattr(analyser_cls, "official_title_parser_movie", None)

    async def official_title_parser(
        self, bangumi, rss, torrent, fetch_poster: bool = True
    ):
        from hfzy.config import get_hfzy_settings

        original_title = bangumi.official_title
        use_custom = fetch_poster and getattr(rss, "parser", None) == "tmdb"
        if use_custom:
            bangumi.official_title = preferred_query_title(
                rss,
                original_title,
                enabled=get_hfzy_settings().rss_name_priority,
            )
        await original_bangumi(
            self,
            bangumi=bangumi,
            rss=rss,
            torrent=torrent,
            fetch_poster=fetch_poster,
        )

    analyser_cls.official_title_parser = official_title_parser

    if original_movie is not None:

        async def official_title_parser_movie(
            self, movie, rss, torrent, fetch_poster: bool = True
        ):
            from hfzy.config import get_hfzy_settings

            original_title = movie.official_title
            use_custom = fetch_poster and getattr(rss, "parser", None) == "tmdb"
            if use_custom:
                movie.official_title = preferred_query_title(
                    rss,
                    original_title,
                    enabled=get_hfzy_settings().rss_name_priority,
                )
            await original_movie(
                self,
                movie=movie,
                rss=rss,
                torrent=torrent,
                fetch_poster=fetch_poster,
            )

        analyser_cls.official_title_parser_movie = official_title_parser_movie

    analyser_cls._hfzy_rss_name_priority_patched = True
