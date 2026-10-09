from hfzy.season_priority import prefer_form_season


def test_matching_release_is_kept():
    assert prefer_form_season(True, False, False) is True


def test_season_mismatch_is_kept_when_switch_is_on():
    assert prefer_form_season(False, True, True) is True


def test_season_mismatch_is_dropped_when_switch_is_off():
    assert prefer_form_season(False, False, True) is False


def test_other_mismatches_stay_dropped():
    assert prefer_form_season(False, True, False) is False
