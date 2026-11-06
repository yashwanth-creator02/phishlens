from __future__ import annotations

from pathlib import Path
import pytest
from training.evaluate import run_evaluation
from training.synthetic import build_samples


def _write_fixtures(tmp_path):
    phish_dir = tmp_path / "phish"
    ham_dir = tmp_path / "ham"
    phish_dir.mkdir()
    ham_dir.mkdir()

    samples = build_samples(n=40, seed=42)
    for i, s in enumerate(samples):
        if s.label == 1:
            (phish_dir / f"phish_{i}.eml").write_bytes(s.raw)
        else:
            (ham_dir / f"ham_{i}.eml").write_bytes(s.raw)
    return phish_dir, ham_dir


def test_evaluation_uses_grouped_split(tmp_path):
    phish_dir, ham_dir = _write_fixtures(tmp_path)

    report = run_evaluation(phish_dir, ham_dir, tmp_path / "reports")
    assert report["n_test"] > 0
    assert "cold_start_f1" in report
    assert "cold_start_n" in report
    assert report["split_unit"] == "campaign_or_sender"
    assert "random_split_f1" in report
    assert "random_split_pr_auc" in report
    assert (tmp_path / "reports" / "evaluation.json").exists()
    assert (tmp_path / "reports" / "evaluation.md").exists()


def test_evaluation_no_cwd_reports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    phish_dir, ham_dir = _write_fixtures(tmp_path)

    out_dir = tmp_path / "custom_reports"
    report = run_evaluation(phish_dir, ham_dir, out_dir)
    assert report["n_test"] > 0
    assert not (tmp_path / "reports").exists()
    assert (out_dir / "evaluation.json").exists()
    assert (out_dir / "evaluation.md").exists()


def test_evaluation_rejects_missing_corpora(tmp_path):
    empty_phish = tmp_path / "empty_phish"
    empty_ham = tmp_path / "empty_ham"
    empty_phish.mkdir()
    empty_ham.mkdir()

    with pytest.raises(ValueError, match="No emails found"):
        run_evaluation(empty_phish, empty_ham, tmp_path / "reports")
