"""Faithfulness and stability of the explanations.

The reasons are the product: a sentence that names a warning sign the model did not use is worse than no
sentence. These tests measure that against the model that actually ships.

The deletion test is read with its control. Deleting features always moves a score a little, so the only
question that matters is whether the features the reasons *name* move it more than a random set of the same
size. Where the model is saturated the test has no power at all, and the result says so instead of
reporting a pass.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.explain.faithfulness import band_of, cited_features, deletion_check, stability_check
from app.explain.reasons import build_reasons
from app.explain.shap_engine import contributions
from app.features.common import ExtractionContext, ProfileData
from app.features.feature_vector import FEATURE_NAMES, extract_all
from app.ingestion.email_parser import parse_email
from app.ml.registry import ModelNotAvailable, load_model_dir

BACKEND = Path(__file__).resolve().parents[1]
SAMPLES = BACKEND / "data" / "sample_emails"
RELEASE = BACKEND / "release" / "model"


@pytest.fixture(scope="module")
def release_model():
    if not (RELEASE / "meta.json").exists():
        pytest.skip("no released model to check")
    try:
        return load_model_dir(RELEASE)
    except ModelNotAvailable as exc:
        pytest.skip(str(exc))


def _score(bundle, raw: bytes):
    parsed = parse_email(raw)
    fx = extract_all(parsed, ExtractionContext(profile=ProfileData()))
    vector = [float(fx.values[n]) for n in FEATURE_NAMES]
    reasons = build_reasons(contributions(bundle, vector), fx.values, fx.evidence)
    return vector, reasons


def _with_blank_line(raw: bytes) -> bytes:
    head, _, body = raw.partition(b"\r\n\r\n")
    return head + b"\r\n\r\n" + body.replace(b"\r\n", b"\r\n\r\n", 1)


def _with_reordered_headers(raw: bytes) -> bytes:
    head, sep, body = raw.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    first, rest = lines[0], lines[1:]
    rest = sorted(rest, key=lambda ln: ln.split(b":", 1)[0].lower())
    return b"\r\n".join([first] + rest) + sep + body


def test_the_reasons_name_features_that_matter_more_than_a_random_pick(release_model):
    """A non-saturated phishing message: deleting what the reasons name must move the score more than
    deleting a random set of the same size."""
    bundle = release_model
    raw = (SAMPLES / "phish_invoice_forwarded_inline.eml").read_bytes()
    vector, reasons = _score(bundle, raw)
    cited = cited_features(reasons)
    assert cited, "the phishing sample should produce reasons"

    result = deletion_check(bundle, vector, cited)
    assert result["has_power"], f"the test needs an unsaturated score to say anything: {result}"
    assert result["drop"] > result["random_drop_max"], (
        f"the cited features {cited} account for {result['drop']:.6f} of the score, "
        f"a random set of the same size accounts for up to {result['random_drop_max']:.6f}")


def test_a_saturated_score_reports_that_the_test_cannot_say_anything(release_model):
    """The released model saturates on obvious phishing, so the comparison has no power there. The check
    has to say so rather than let a near-zero number read as a pass."""
    bundle = release_model
    raw = (SAMPLES / "phish_paypal_direct.eml").read_bytes()
    vector, reasons = _score(bundle, raw)
    result = deletion_check(bundle, vector, cited_features(reasons))
    if result["raw_before"] < 0.99:
        pytest.skip("this model no longer saturates on the sample; the power check applies instead")
    assert not result["has_power"]
    assert result["drop"] <= result["random_drop_max"], (
        "a saturated score cannot be moved by the cited features, so they say nothing either way")


def test_reformatting_the_message_does_not_change_the_verdict(release_model):
    """A message that is the same message: a blank line in the body, headers in another order. The band,
    the score and the reasons must not move."""
    bundle = release_model
    for name in ("legit_bank_alert.eml", "phish_invoice_forwarded_inline.eml", "phish_paypal_direct.eml"):
        raw = (SAMPLES / name).read_bytes()
        vector, reasons = _score(bundle, raw)
        band, score = band_of(bundle, vector)
        for label, mutate in (("blank line", _with_blank_line),
                              ("reordered headers", _with_reordered_headers)):
            mutated_vector, mutated_reasons = _score(bundle, mutate(raw))
            result = stability_check(bundle, vector, mutated_vector)
            assert result["same_band"], f"{name} changed band under {label}: {result}"
            assert result["score_before"] == result["score_after"], f"{name} changed score under {label}"
            assert [r.rule_key for r in reasons] == [r.rule_key for r in mutated_reasons], \
                f"{name} changed reasons under {label}"


def test_scoring_the_same_message_twice_gives_the_same_answer(release_model):
    bundle = release_model
    raw = (SAMPLES / "phish_paypal_direct.eml").read_bytes()
    first, first_reasons = _score(bundle, raw)
    second, second_reasons = _score(bundle, raw)
    assert first == second
    assert [r.sentence for r in first_reasons] == [r.sentence for r in second_reasons]
