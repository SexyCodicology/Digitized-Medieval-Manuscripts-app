"""Tests for scripts/apply_link_status.py.

The report fixtures below copy the shape of a real lychee run (see issue #70:
1,232 links checked, 78 errors, 58 timeouts), because the whole point of this
script is to tell the few conclusive failures apart from the many that say
nothing about whether a collection still exists.

No test reaches the network or invokes lychee.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "apply_link_status", REPO_ROOT / "scripts" / "apply_link_status.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


script = _load_script()

SUMMARY = """# Summary

| Status         | Count |
|----------------|-------|
| 🔍 Total       | 1232  |
| 🔗 Unique      | 744   |
| ✅ Successful  | 1096  |
| ⏳ Timeouts    | 58    |
| 🔀 Redirected  | 151   |
| 👻 Excluded    | 0     |
| ❓ Unknown     | 0     |
| 🚫 Errors      | 78    |
| ⛔ Unsupported | 0     |

## Errors per input

### Errors in ./docs/assets/data.json

"""

DETAILS = """* [404] <https://dead.example.org/manuscripts> (at 4864:21) | Rejected status code: 404 Not Found
* [410] <https://gone.example.org/manuscripts> (at 1234:21) | Rejected status code: 410 Gone
* [403] <https://blocked.example.org/manuscripts> (at 7694:21) | Rejected status code: 403 Forbidden
* [429] <https://ratelimited.example.org/manuscripts> (at 100:21) | Too many requests
* [503] <https://down.example.org/manuscripts> (at 200:21) | Rejected status code: 503
* [TIMEOUT] <https://slow.example.org/manuscripts> (at 300:21) | Timeout
* [ERROR] <https://unreachable.example.org/manuscripts> (at 522:21) | Connection failed
"""

REPORT = SUMMARY + DETAILS


def record(record_id: int, website: str, **extra) -> dict:
    return {
        "id": record_id,
        "nation": "Nation",
        "city": "City",
        "library": f"Library {record_id}",
        "quantity": "Few",
        "website": website,
        "copyright": "Unknown",
        "iiif": False,
        "is_free_cultural_works_license": False,
        "aggregators": [],
        **extra,
    }


# ── Parsing ───────────────────────────────────────────────────────────────


def test_parse_report_reads_the_summary_and_every_detail_line():
    by_url, summary = script.parse_report(REPORT)

    assert summary["total"] == 1232
    assert summary["errors"] == 78
    assert len(by_url) == 7
    assert by_url["https://dead.example.org/manuscripts"] == {"404"}
    assert by_url["https://slow.example.org/manuscripts"] == {"TIMEOUT"}


def test_a_report_with_no_summary_table_is_rejected():
    with pytest.raises(script.ReportError, match="no summary table"):
        script.parse_report(DETAILS)


def test_a_report_claiming_problems_with_no_parseable_detail_is_rejected():
    """The failure this guards against: a format change that silently turns
    every run into "nothing to report" instead of failing."""
    with pytest.raises(script.ReportError, match="no detail line"):
        script.parse_report(SUMMARY)


def test_a_clean_report_with_no_problems_parses_to_nothing():
    clean = SUMMARY.replace("| ⏳ Timeouts    | 58    |", "| ⏳ Timeouts    | 0     |").replace(
        "| 🚫 Errors      | 78    |", "| 🚫 Errors      | 0     |"
    )

    by_url, summary = script.parse_report(clean)

    assert by_url == {}
    assert summary["errors"] == 0


def test_an_empty_report_is_rejected_rather_than_read_as_all_clear():
    with pytest.raises(script.ReportError):
        script.parse_report("")


# ── Deciding what to change ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    ["https://dead.example.org/manuscripts", "https://gone.example.org/manuscripts"],
)
def test_a_conclusively_dead_link_is_marked_broken(url):
    records = [record(1, url)]
    by_url, _ = script.parse_report(REPORT)

    disabled, restored = script.plan_changes(records, by_url, "2026-08-02")

    assert records[0]["is_disabled"] is True
    assert records[0]["last_checked"] == "2026-08-02"
    assert len(disabled) == 1
    assert restored == []


@pytest.mark.parametrize(
    "url",
    [
        "https://blocked.example.org/manuscripts",     # 403
        "https://ratelimited.example.org/manuscripts", # 429
        "https://down.example.org/manuscripts",        # 503
        "https://slow.example.org/manuscripts",        # timeout
        "https://unreachable.example.org/manuscripts", # connection error
    ],
)
def test_an_inconclusive_failure_never_marks_a_record_broken(url):
    records = [record(1, url)]
    by_url, _ = script.parse_report(REPORT)

    disabled, restored = script.plan_changes(records, by_url, "2026-08-02")

    assert "is_disabled" not in records[0]
    assert "last_checked" not in records[0]
    assert (disabled, restored) == ([], [])


def test_a_healthy_link_is_left_untouched():
    records = [record(1, "https://fine.example.org/manuscripts")]
    before = copy.deepcopy(records)
    by_url, _ = script.parse_report(REPORT)

    script.plan_changes(records, by_url, "2026-08-02")

    assert records == before


def test_a_link_that_works_again_is_restored():
    records = [
        record(1, "https://fine.example.org/manuscripts",
               is_disabled=True, last_checked="2026-01-01")
    ]
    by_url, _ = script.parse_report(REPORT)

    disabled, restored = script.plan_changes(records, by_url, "2026-08-02")

    assert "is_disabled" not in records[0]
    assert records[0]["last_checked"] == "2026-08-02"
    assert len(restored) == 1


def test_a_still_dead_link_only_has_its_date_refreshed():
    records = [
        record(1, "https://dead.example.org/manuscripts",
               is_disabled=True, last_checked="2026-01-01")
    ]
    by_url, _ = script.parse_report(REPORT)

    disabled, restored = script.plan_changes(records, by_url, "2026-08-02")

    assert records[0]["is_disabled"] is True
    assert records[0]["last_checked"] == "2026-08-02"
    # Not re-reported: it was already known broken.
    assert (disabled, restored) == ([], [])


def test_an_inconclusive_failure_does_not_restore_a_broken_record():
    """A timeout is not evidence the collection came back."""
    records = [
        record(1, "https://slow.example.org/manuscripts",
               is_disabled=True, last_checked="2026-01-01")
    ]
    by_url, _ = script.parse_report(REPORT)

    disabled, restored = script.plan_changes(records, by_url, "2026-08-02")

    assert records[0]["is_disabled"] is True
    assert records[0]["last_checked"] == "2026-01-01", "no evidence, so no update"
    assert (disabled, restored) == ([], [])


def test_a_dead_aggregator_url_does_not_disable_the_library():
    """The aggregator being down says nothing about this collection."""
    records = [
        record(1, "https://fine.example.org/manuscripts",
               aggregators=[{"name": "Dead", "url": "https://dead.example.org/manuscripts"}])
    ]
    by_url, _ = script.parse_report(REPORT)

    script.plan_changes(records, by_url, "2026-08-02")

    assert "is_disabled" not in records[0]


def test_a_record_with_a_non_string_website_is_skipped():
    records = [record(1, None)]
    by_url, _ = script.parse_report(REPORT)

    script.plan_changes(records, by_url, "2026-08-02")

    assert "is_disabled" not in records[0]


# ── End to end ────────────────────────────────────────────────────────────


def _run(tmp_path, report_text, records):
    report = tmp_path / "lychee-report.md"
    report.write_text(report_text, encoding="utf-8")
    data = tmp_path / "data.json"
    data.write_text(json.dumps(records, indent=4), encoding="utf-8")
    code = script.main(
        ["--report", str(report), "--today", "2026-08-02", "--data", str(data)]
    )
    return code, json.loads(data.read_text(encoding="utf-8"))


def test_main_writes_the_proposed_change(tmp_path):
    code, written = _run(
        tmp_path, REPORT, [record(1, "https://dead.example.org/manuscripts")]
    )

    assert code == 0
    assert written[0]["is_disabled"] is True
    assert written[0]["last_checked"] == "2026-08-02"


def test_main_leaves_the_file_alone_when_nothing_is_conclusive(tmp_path):
    records = [record(1, "https://slow.example.org/manuscripts")]
    code, written = _run(tmp_path, REPORT, records)

    assert code == 0
    assert written == records


def test_main_fails_loudly_on_an_unparseable_report(tmp_path):
    code, written = _run(tmp_path, "garbage, not a report", [record(1, "https://x.example")])

    assert code == 1, "an unreadable report must fail, not write an all-clear"
    assert "is_disabled" not in written[0]


def test_main_fails_loudly_when_the_report_is_missing(tmp_path):
    data = tmp_path / "data.json"
    data.write_text(json.dumps([record(1, "https://x.example")]), encoding="utf-8")

    code = script.main(
        ["--report", str(tmp_path / "nope.md"), "--today", "2026-08-02", "--data", str(data)]
    )

    assert code == 1


def test_the_written_file_still_validates(tmp_path):
    """A proposed change must not produce a dataset the validator rejects."""
    spec = importlib.util.spec_from_file_location(
        "validate_data", REPO_ROOT / "scripts" / "validate_data.py"
    )
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)

    _, written = _run(tmp_path, REPORT, [record(1, "https://dead.example.org/manuscripts")])
    schema = validator.load_json(REPO_ROOT / "schema.json")

    assert validator.validate(schema, written) == []
