from module.manager.revision_policy import is_strict_upgrade

from hfzy.revision_identity import count_episode_videos, identity_with_bracket_group

_V2 = "[Nekomoe kissaten][KILL BLUE][09][1080p][JPSC][v2].mp4"
_V1 = "[Nekomoe kissaten][KILL BLUE][09][1080p][JPSC].mp4"


def test_spaced_group_v2_is_a_strict_upgrade():
    old = identity_with_bracket_group(_V1, bangumi_id=42, default_season=1)
    new = identity_with_bracket_group(_V2, bangumi_id=42, default_season=1)
    assert old is not None and new is not None
    assert old.revision == 1
    assert new.revision == 2
    assert old.group == new.group
    assert is_strict_upgrade(old, new)


def test_subtitle_archive_does_not_add_an_episode():
    files = [
        {"name": "episode.mp4"},
        {"name": "[ASS+Fonts].zip"},
        {"name": "episode.ass"},
    ]
    assert count_episode_videos(files, enabled=True) == 1
    assert count_episode_videos(files, enabled=False) == 3


def test_several_videos_stay_multi_file():
    files = [
        {"name": "01.mp4"},
        {"name": "02.mkv"},
        {"name": "[ASS+Fonts].zip"},
    ]
    assert count_episode_videos(files, enabled=True) == 2
