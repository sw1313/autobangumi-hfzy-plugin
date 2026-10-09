import re

import pytest
from hfzy.episode_count import (
    compile_exclude,
    exclude_pattern,
    matched_filter_terms,
    summarize_releases,
    version_key,
)


def test_exclude_pattern_matches_collector_join():
    assert exclude_pattern(["720", r"\d+-\d+"]) == r"720|\d+-\d+"
    assert exclude_pattern("720,\\d+-\\d+") == r"720|\d+-\d+"
    assert exclude_pattern(None) == ""
    assert exclude_pattern("") == ""


def test_compile_exclude_blank_keeps_everything():
    assert compile_exclude("") is None


def test_matched_filter_terms_mark_only_patterns_that_hit_a_title():
    titles = [
        "[LoliHouse] Show - 01 [1080p][简繁内封字幕]",
        "[LoliHouse] Show [01-12][1080p][简繁内封字幕]",
    ]
    assert matched_filter_terms(titles, ["720", "简繁内封", r"\d+-\d+"]) == [
        "简繁内封",
        r"\d+-\d+",
    ]


def test_compile_exclude_rejects_broken_regex():
    with pytest.raises(re.error):
        compile_exclude("[")


def test_resolution_is_not_treated_as_an_episode():
    first = version_key("[樱都字幕组] Show [01][1080P][简繁内封]")
    second = version_key("[樱都字幕组] Show [12][1080P][简繁内封]")
    assert first == second
    assert "1080p" in first


def test_two_subtitle_types_are_two_versions_and_twenty_four_videos():
    titles = []
    for episode in range(1, 13):
        number = f"{episode:02d}"
        titles.append(f"[樱都字幕组] Show [{number}][1080P][简繁内封]")
        titles.append(f"[樱都字幕组] Show [{number}][1080P][简体内嵌]")
        titles.append(f"[樱都字幕组] Show [{number}][1080P][繁体内嵌]")
    pattern = exclude_pattern(["720", r"\d+-\d+", "繁体内嵌"])
    assert summarize_releases(titles, pattern) == {"versions": 2, "videos": 24}


def test_v2_and_torrent_suffix_stay_one_version():
    titles = [
        "[樱桃花字幕组] Show - 05 [1080p][简日内嵌]",
        "[樱桃花字幕组] Show - 05v2 [1080p][简日内嵌]",
        "[樱桃花字幕组] Show - 04 [1080p][简日内嵌][v2]",
        "[樱桃花字幕组] Show - 01 [1080p][简日内嵌].mp4.torrent",
    ]
    assert summarize_releases(titles, "") == {"versions": 1, "videos": 4}


def test_finale_mark_does_not_create_another_version():
    titles = [
        "[LoliHouse] Show - 01 [WebRip 1080p HEVC-10bit AAC][简繁内封字幕]",
        "[LoliHouse] Show - 12 [WebRip 1080p HEVC-10bit AAC][简繁内封字幕][END]",
    ]
    assert summarize_releases(titles, "") == {"versions": 1, "videos": 2}


def test_collection_is_left_out_when_it_cannot_be_downloaded():
    titles = [
        "[LoliHouse] Show - 01 [1080p][简繁内封字幕]",
        "[LoliHouse] Show [01-12 合集][1080p][简繁内封字幕][Fin]",
    ]
    result = summarize_releases(
        titles, "", keep=lambda title: "合集" not in title
    )
    assert result == {"versions": 1, "videos": 1}


def test_dash_episode_numbers_share_one_version():
    titles = [
        "[Group] Show - 01 [1080p][简体内嵌]",
        "[Group] Show - 02 [1080p][简体内嵌]",
    ]
    assert summarize_releases(titles, "") == {"versions": 1, "videos": 2}
