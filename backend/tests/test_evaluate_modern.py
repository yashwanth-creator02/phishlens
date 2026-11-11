from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from app.features.common import NullDomainAge
from app.features.feature_vector import FEATURE_NAMES
from app.ml.registry import load_model_dir
from training.corpus import date_range, parse_cli_date
from training.evaluate_modern import (DEFAULT_PHISH_SINCE, DEFAULT_PHISH_UNTIL, fpr_with_ci, guard_leakage,
                                      ham_summary, in_window, leakage_check, parse_date, probability_summary,
                                      threshold_metrics)
from training.synthetic import Sample


def _sample(date: str) -> Sample:
    return Sample(raw=b"", label=0, group="legit-mailbox-example.com", profile=None,
                  domain_age=NullDomainAge(), date=date)


def test_parse_date_accepts_rfc2822_and_rejects_garbage():
    assert parse_date("Mon, 1 Jan 2024 10:00:00 +0000") == datetime(2024, 1, 1, 10, tzinfo=timezone.utc)
    assert parse_date("") is None
    assert parse_date("not a date") is None


def test_parse_cli_date_treats_naive_input_as_utc():
    assert parse_cli_date("2024-01-01") == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert parse_cli_date(None) is None


def test_in_window_keeps_dated_messages_and_drops_undated():
    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    until = datetime(2025, 1, 1, tzinfo=timezone.utc)
    assert in_window(_sample("Mon, 1 Jan 2024 10:00:00 +0000"), since, until)
    assert not in_window(_sample("Mon, 1 Jan 2023 10:00:00 +0000"), since, until)
    assert not in_window(_sample(""), since, until)


def test_date_range_counts_undated_messages():
    samples = [_sample("Mon, 1 Jan 2024 10:00:00 +0000"), _sample("")]
    result = date_range(samples)
    assert result["dated"] == 1
    assert result["undated"] == 1
    assert result["min"].startswith("2024-01-01")


def test_threshold_metrics_reports_probability_and_band_boundaries():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.10, 0.40, 0.60, 0.90])
    scores = np.array([10, 40, 60, 90])

    result = threshold_metrics(y, p, scores, low_max=29)

    assert result["at_probability_0_5"]["fpr"] == 0.0
    assert result["at_probability_0_5"]["recall"] == 1.0
    assert result["at_band_boundary"]["fpr"] == 0.5
    assert result["at_band_boundary"]["recall"] == 1.0


def test_ham_summary_breaks_down_auth_and_flagged_domains():
    X = np.zeros((2, len(FEATURE_NAMES)))
    X[:, FEATURE_NAMES.index("auth_missing")] = [1, 0]
    X[:, FEATURE_NAMES.index("spf_pass")] = [0, 1]
    p = np.array([0.10, 0.40])
    scores = np.array([10, 40])
    groups = np.array(["legit-mailbox-a.com", "legit-mailbox-b.com"])

    result = ham_summary(X, p, scores, groups, low_max=29, high_min=70)

    assert result["fpr_at_band_boundary"] == 0.5
    assert result["fpr_at_probability_0_29"] == 0.5
    assert result["fpr_at_probability_0_5"] == 0.0
    assert result["auth"]["auth_missing"] == 0.5
    assert result["top_false_positive_domains"][0]["domain"] == "b.com"


def test_fpr_with_ci_macro_is_unweighted_domain_mean():
    # 9 messages in one domain that is never flagged, 1 message in a domain that always is.
    flagged = np.array([0] * 9 + [1])
    groups = np.array(["legit-mailbox-big.com"] * 9 + ["legit-mailbox-small.com"])

    result = fpr_with_ci(flagged, groups, n_boot=200)

    assert result["pooled"] == pytest.approx(0.1)
    assert result["macro"] == pytest.approx(0.5)
    assert result["domains"] == 2
    assert result["pooled_ci95"][0] <= result["pooled"] <= result["pooled_ci95"][1]
    assert result["macro_ci95"][0] <= result["macro"] <= result["macro_ci95"][1]


def test_fpr_with_ci_is_deterministic_for_a_fixed_seed():
    flagged = np.array([0, 1, 1, 0, 1, 0, 0, 1])
    groups = np.array([f"legit-mailbox-{i % 3}.com" for i in range(8)])

    first = fpr_with_ci(flagged, groups, n_boot=100)
    second = fpr_with_ci(flagged, groups, n_boot=100)

    assert first == second


def test_leakage_check_detects_overlap_clear_and_unknown():
    trained_old = {"training": {"phish_min_date": "2004-01-01T00:00:00+00:00",
                                 "phish_max_date": "2013-12-31T00:00:00+00:00"}}
    trained_modern = {"training": {"phish_min_date": "2004-01-01T00:00:00+00:00",
                                   "phish_max_date": "2025-12-31T00:00:00+00:00"}}
    since = datetime(2015, 1, 1, tzinfo=timezone.utc)
    until = datetime(2024, 1, 1, tzinfo=timezone.utc)

    assert leakage_check(trained_old, since, until) == "clear"
    assert leakage_check(trained_modern, since, until) == "overlap"
    assert leakage_check({}, since, until) == "unknown"
    assert leakage_check({"training": {}}, since, until) == "unknown"


def test_guard_leakage_blocks_overlap_and_unknown_provenance():
    with pytest.raises(SystemExit):
        guard_leakage("overlap", "xgboost-corpus-test", allow_overlap=False)
    with pytest.raises(SystemExit):
        guard_leakage("unknown", "xgboost-corpus-test", allow_overlap=False)
    guard_leakage("overlap", "xgboost-corpus-test", allow_overlap=True)
    guard_leakage("unknown", "xgboost-corpus-test", allow_overlap=True, allow_unknown=True)
    guard_leakage("clear", "xgboost-corpus-test", allow_overlap=False)


def test_cli_date_reports_a_malformed_value_instead_of_crashing():
    from training.evaluate_modern import _cli_date

    assert _cli_date(None, "--phish-since") is None
    assert _cli_date("2024-01-01", "--phish-since") == datetime(2024, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(SystemExit):
        _cli_date("not-a-date", "--phish-since")


def test_probability_summary_reports_the_threshold_shares():
    summary = probability_summary([0.05, 0.30, 0.60, 0.95])

    assert summary["mean"] == pytest.approx(0.475)
    assert summary["share_above_0_29"] == pytest.approx(0.75)
    assert summary["share_above_0_5"] == pytest.approx(0.5)


def test_default_window_keeps_the_newest_archive_as_holdout():
    assert DEFAULT_PHISH_SINCE == "2015-01-01"
    assert DEFAULT_PHISH_UNTIL == "2024-01-01"


def test_phish_leakage_compares_archive_files_not_dates(tmp_path: Path):
    from training.evaluate_modern import phish_leakage

    train_dir = tmp_path / "train"
    train_dir.mkdir()
    (train_dir / "phishing-2023.mbox").write_text("")
    eval_dir = tmp_path / "holdout"
    eval_dir.mkdir()
    (eval_dir / "phishing-2024.mbox").write_text("")

    meta = {"training": {"phish_files": ["phishing-2023.mbox"], "phish_min_date": "1970-01-01T00:00:00+00:00",
                          "phish_max_date": "2038-01-01T00:00:00+00:00"}}

    status, overlap = phish_leakage(meta, str(eval_dir), None, None)
    assert status == "clear" and overlap == []

    meta["training"]["phish_files"] = ["phishing-2023.mbox", "phishing-2024.mbox"]
    status, overlap = phish_leakage(meta, str(eval_dir), None, None)
    assert status == "overlap" and overlap == ["phishing-2024.mbox"]


def test_ham_leakage_is_distinct_for_a_different_mailbox_file(tmp_path: Path):
    from training.evaluate_modern import ham_leakage

    meta = {"training": {"legit_mailbox": str(tmp_path / "trained.mbox"),
                          "legit_mailbox_min_date": "2020-01-01T00:00:00+00:00",
                          "legit_mailbox_max_date": "2023-12-31T00:00:00+00:00"}}
    other = tmp_path / "other.mbox"
    other.write_text("")

    assert ham_leakage(meta, str(other), None, None) == "distinct"
    assert ham_leakage(meta, str(tmp_path / "trained.mbox"), None, None) == "overlap"
    assert ham_leakage({}, str(other), None, None) == "unknown"


def test_activation_refuses_a_personal_data_model_without_acknowledgement():
    from training.train import check_activation_allowed

    with pytest.raises(SystemExit):
        check_activation_allowed({"contains_personal_data": True}, allow_personal_data=False)
    check_activation_allowed({"contains_personal_data": True}, allow_personal_data=True)
    check_activation_allowed({"contains_personal_data": False}, allow_personal_data=False)


def test_activation_keeps_the_previous_model_servable_when_the_copy_fails(tmp_path: Path):
    from training.train import activate

    active = tmp_path / "active"
    active.mkdir()
    (active / "meta.json").write_text("{}")

    with pytest.raises(Exception):
        activate(tmp_path / "does-not-exist", active)

    assert (active / "meta.json").exists(), "a failed promotion must not remove the serving model"


def test_activation_swaps_the_candidate_in_and_keeps_the_previous(tmp_path: Path):
    from training.train import activate

    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "meta.json").write_text('{"version_tag": "new"}')
    active = tmp_path / "active"
    active.mkdir()
    (active / "meta.json").write_text('{"version_tag": "old"}')

    activate(candidate, active)

    assert json.loads((active / "meta.json").read_text())["version_tag"] == "new"
    assert json.loads((active.with_name("active.prev") / "meta.json").read_text())["version_tag"] == "old"


def test_training_writes_a_candidate_model_and_provenance_without_activating(tmp_path: Path):
    from training import train

    out = tmp_path / "models"
    reports = tmp_path / "reports"
    train.main(["--source", "synthetic", "--n", "60", "--out", str(out), "--reports", str(reports)])

    assert not (out / "active").exists(), "an offline training run must not replace the serving model"
    tags = [d for d in out.iterdir() if d.is_dir()]
    assert len(tags) == 1

    meta = json.loads((tags[0] / "meta.json").read_text())
    assert "training" in meta
    assert meta["training"]["phish_until"] is None
    assert load_model_dir(tags[0]).version_tag == meta["version_tag"]


def test_training_activates_only_when_asked(tmp_path: Path):
    from training import train

    out = tmp_path / "models"
    reports = tmp_path / "reports"
    train.main(["--source", "synthetic", "--n", "60", "--out", str(out), "--reports", str(reports),
                "--activate"])

    assert (out / "active" / "meta.json").exists()
