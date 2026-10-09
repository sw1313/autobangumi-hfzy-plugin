from types import SimpleNamespace

from hfzy.config import apply_revision_policy, normalize_revision_policy


def test_unknown_policy_stays_on_hold():
    assert normalize_revision_policy("replace") == "replace"
    assert normalize_revision_policy(" HOLD ") == "hold"
    assert normalize_revision_policy("nope") == "hold"
    assert normalize_revision_policy(None) == "hold"


def test_apply_copies_policy_onto_bangumi_manage():
    settings = SimpleNamespace(
        bangumi_manage=SimpleNamespace(revision_conflict_policy="hold")
    )
    apply_revision_policy(settings, "replace")
    assert settings.bangumi_manage.revision_conflict_policy == "replace"
    apply_revision_policy(settings, "bogus")
    assert settings.bangumi_manage.revision_conflict_policy == "hold"
