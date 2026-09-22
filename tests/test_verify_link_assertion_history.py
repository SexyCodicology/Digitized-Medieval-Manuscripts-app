"""Protect the audit boundary for authority and IIIF links."""

from scripts.verify_link_assertion_history import compare_links


def test_unchanged_grandfathered_link_needs_no_approval():
    record = {"id": 1, "wikidata_qid": "Q123"}

    assert compare_links([record], [record], set()) == []


def test_new_or_changed_link_needs_exact_approval():
    previous = [{"id": 1, "wikidata_qid": "Q123"}]
    current = [{"id": 1, "wikidata_qid": "Q456"}]

    assert compare_links(previous, current, set()) == [
        "new or changed 1/wikidata_qid lacks maintainer approval"
    ]
    assert compare_links(
        previous,
        current,
        {("1", "wikidata_qid", "Q456")},
    ) == []


def test_new_record_link_needs_approval():
    current = [{"id": 2, "isil": "GB-Example"}]

    assert compare_links([], current, set()) == [
        "new or changed 2/isil lacks maintainer approval"
    ]


def test_removing_a_link_does_not_invent_an_approval_requirement():
    previous = [{"id": 1, "geonames_id": 2640729}]

    assert compare_links(previous, [{"id": 1}], set()) == []


def test_non_record_structures_fail_closed():
    assert compare_links({}, [], set()) == [
        "both data files must contain lists of records"
    ]
    assert compare_links(["record"], [], set()) == [
        "both data files must contain record objects"
    ]
