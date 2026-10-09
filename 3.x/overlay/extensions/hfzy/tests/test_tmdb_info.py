import pytest

from hfzy.tmdb_info import (
    apply_tmdb_record,
    bangumi_from_tmdb,
    normalize_tmdb_hint,
    title_source,
)


def test_empty_id_is_optional():
    assert normalize_tmdb_hint("tv", "") is None
    assert normalize_tmdb_hint("tv", "  ") is None


def test_numeric_id_keeps_the_type():
    assert normalize_tmdb_hint("movie", " 129 ") == ("movie", "129")


def test_unknown_type_is_rejected():
    with pytest.raises(ValueError):
        normalize_tmdb_hint("person", "129")


def test_non_numeric_id_is_rejected():
    with pytest.raises(ValueError):
        normalize_tmdb_hint("tv", "tt129")


def test_lookup_order_is_id_then_name_then_filename():
    assert title_source("129", "天气之子") == "tmdb"
    assert title_source("", "天气之子") == "name"
    assert title_source("  ", "  ") == "auto"


def test_unparsed_feed_still_uses_the_tmdb_id():
    data = bangumi_from_tmdb(
        {"name": "天气之子", "first_air_date": "2019-07-19"},
        "tv",
        "https://example.test/rss",
    )
    assert data.official_title == "天气之子"
    assert data.year == "2019"
    assert data.rss_link == "https://example.test/rss"
    assert data.title_raw == "天气之子"


def test_movie_record_sets_title_year_and_type():
    class Bangumi:
        official_title = "parsed"
        year = None
        poster_link = None
        episode_type = "episode"

    updated = apply_tmdb_record(
        Bangumi(),
        "movie",
        {
            "title": "天气之子",
            "release_date": "2019-07-19",
            "_poster_link": "/posters/weather.jpg",
        },
    )
    assert updated.official_title == "天气之子"
    assert updated.year == "2019"
    assert updated.poster_link == "/posters/weather.jpg"
    assert updated.episode_type == "movie"
