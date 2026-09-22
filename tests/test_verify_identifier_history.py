"""Protect published record identifiers and name-based URLs across PRs."""

from scripts.verify_identifier_history import compare_aliases


def test_history_allows_new_ids_and_aliases():
    previous = {"1": ["old-name-1"]}
    current = {"1": ["old-name-1", "new-name-1"], "2": ["second-2"]}

    assert compare_aliases(previous, current) == []


def test_history_rejects_removed_ids_and_aliases():
    previous = {"1": ["first-name-1", "renamed-1"], "2": ["second-2"]}
    current = {"1": ["renamed-1"]}

    assert compare_aliases(previous, current) == [
        "record 1 lost published alias first-name-1",
        "published record ID 2 was removed",
    ]


def test_history_rejects_malformed_registry():
    assert compare_aliases({"1": [["invalid"]]}, {"1": ["valid-1"]}) == [
        "record 1 has invalid alias lists"
    ]
