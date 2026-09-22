"""Check name-evidence gates without relying on live institutional sites."""

from scripts.validate_name_evidence import validate
from scripts.verify_name_history import compare


def decision(field, value, *, status="verified", language=""):
    """Return a complete source-backed test decision."""
    return {
        "record_id": "1", "field": field, "value": value,
        "language": language, "status": status,
        "source_url": "https://library.example.org/about",
        "checked_on": "2026-09-20", "note": "Official site names this resource.",
    }


def test_pending_legacy_name_is_allowed_but_new_fields_need_evidence():
    record = {"id": 1, "library": "Example Library"}
    pending = decision("library", "Example Library", status="pending")
    assert validate([record], [pending]) == []
    assert validate([{**record, "access_point_title": "Portal"}], [pending]) == [
        "record 1: access_point_title lacks verified evidence"
    ]


def test_verified_alternate_name_requires_exact_language_and_source():
    record = {
        "id": 1, "library": "Bibliothèque exemple",
        "library_alternate_names": [{"name": "Example Library", "language": "en"}],
    }
    rows = [decision("library", "Bibliothèque exemple"),
            decision("library_alternate_names", "Example Library", language="en")]
    assert validate([record], rows) == []
    rows[1]["language"] = "fr"
    assert "record 1: alternate name language differs from evidence" in validate([record], rows)


def test_changed_names_require_matching_verified_decisions():
    previous = [{"id": 1, "library": "Old label"}]
    current = [{"id": 1, "library": "Official Library", "access_point_title": "Portal"}]
    rows = [decision("library", "Official Library"), decision("access_point_title", "Portal")]

    assert compare(previous, current, rows) == []
    rows[1]["status"] = "pending"
    assert compare(previous, current, rows) == [
        "record 1: changed access_point_title 'Portal' lacks verified name evidence"
    ]
