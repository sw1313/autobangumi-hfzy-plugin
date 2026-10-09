from types import SimpleNamespace

from hfzy.rss_priority import preferred_query_title


def test_filled_name_is_preferred_for_single_rss():
    rss = SimpleNamespace(name="  自定义剧名  ", aggregate=False)
    assert (
        preferred_query_title(rss, "种子解析名", enabled=True) == "自定义剧名"
    )


def test_blank_or_aggregate_name_keeps_parsed_title():
    blank = SimpleNamespace(name="   ", aggregate=False)
    aggregate = SimpleNamespace(name="订阅源名称", aggregate=True)
    assert preferred_query_title(blank, "种子解析名", enabled=True) == "种子解析名"
    assert (
        preferred_query_title(aggregate, "种子解析名", enabled=True) == "种子解析名"
    )


def test_disabled_switch_keeps_parsed_title():
    rss = SimpleNamespace(name="自定义剧名", aggregate=False)
    assert preferred_query_title(rss, "种子解析名", enabled=False) == "种子解析名"
