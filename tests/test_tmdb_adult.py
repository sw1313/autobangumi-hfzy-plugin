from hfzy.tmdb_adult import AdultFlag, apply_include_adult

_URL = (
    "https://api.themoviedb.org/3/search/tv"
    "?api_key=x&page=1&query=%E5%89%A7&include_adult=false&language=zh-CN"
)


def test_enabled_switch_asks_tmdb_for_adult_titles():
    rewritten = apply_include_adult(_URL, True)
    assert "include_adult=true" in rewritten
    assert "include_adult=false" not in rewritten
    assert "api_key=x" in rewritten
    assert "language=zh-CN" in rewritten


def test_disabled_switch_keeps_adult_titles_out():
    rewritten = apply_include_adult(_URL, False)
    assert "include_adult=false" in rewritten
    assert "include_adult=true" not in rewritten


def test_flag_change_is_reported_once():
    flag = AdultFlag()
    assert flag.changed(True) is False
    assert flag.changed(True) is False
    assert flag.changed(False) is True
    assert flag.changed(False) is False
