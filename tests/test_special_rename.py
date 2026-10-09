from types import SimpleNamespace

from hfzy.special_rename import apply_special_rename, special_episode_number


TVSP = (
    "[LoliHouse] Iseleve - TVSP [WebRip 1080p HEVC-10bit AAC SRTx2].mkv"
)


def test_bare_tvsp_is_the_first_special():
    assert special_episode_number(TVSP) == 1


def test_numbered_sp_keeps_its_number():
    assert special_episode_number("[Sub] Show SP02 [1080p].mkv") == 2


def test_ordinary_episode_is_not_a_special_marker():
    assert special_episode_number("[Sub] Show - 08 [1080p].mkv") is None


def test_tvsp_builds_season_zero_when_core_parse_fails():
    parsed = apply_special_rename(None, TVSP, TVSP, "media")
    assert parsed is not None
    assert parsed.season == 0
    assert parsed.episode == 1
    assert parsed.episode_type == "special"
    assert parsed.suffix == ".mkv"


def test_existing_episode_number_moves_to_season_zero():
    parsed = SimpleNamespace(season=1, episode=8, episode_type="episode")
    updated = apply_special_rename(parsed, "Show [08].mp4", "Show [08].mp4", "media")
    assert updated.season == 0
    assert updated.episode == 8
    assert updated.episode_type == "special"


def test_unmarked_name_stays_unparsed():
    assert apply_special_rename(None, "notes.txt", "notes.txt", "media") is None
