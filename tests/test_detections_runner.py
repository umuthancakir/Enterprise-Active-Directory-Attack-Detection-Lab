"""Tests for detections/test_runner.py and detections/coverage.py.

Includes a real integration check against this repo's actual
detections/sigma/ + detections/fixtures/ content (not just synthetic
fixtures) — this is the same "prove the real registry works, not just a
mock of it" pattern used in tests/test_attack_runner.py for attack/.
"""

from __future__ import annotations

from attack.techniques import TECHNIQUES, Technique
from detections.coverage import TechniqueCoverage, build_coverage_matrix
from detections.test_runner import evaluate_technique

# --- Integration: every real technique has a working rule + fixtures ----


def test_every_real_technique_is_covered():
    uncovered = []
    for technique in TECHNIQUES.values():
        coverage = evaluate_technique(technique)
        if not coverage.covered:
            uncovered.append(technique.id)
    assert uncovered == [], f"Techniques missing a passing Sigma rule: {uncovered}"


def test_every_real_technique_has_at_least_one_matching_and_one_non_matching_fixture():
    # A rule that only has "matching" fixtures could trivially match
    # everything and still pass — the non_matching cases are what prove
    # the rule's filters/specificity actually work, not just its happy path.
    for technique in TECHNIQUES.values():
        coverage = evaluate_technique(technique)
        assert coverage.matching_total >= 1, f"{technique.id}: no matching fixture"
        assert coverage.non_matching_total >= 1, f"{technique.id}: no non_matching fixture"


# --- Missing-rule path -----------------------------------------------------


def test_evaluate_technique_reports_uncovered_when_no_rule_exists():
    fake_technique = Technique(
        id="not_a_real_technique_xyz",
        name="fake",
        attack_id="T9999",
        attack_url="https://attack.mitre.org/techniques/T9999/",
        tool="none",
        target_role="domain_controller",
        kill_chain_phase="test",
        command_template=("echo", "test"),
        mock_fixture="unused.json",
    )

    coverage = evaluate_technique(fake_technique)

    assert coverage.sigma_rule_path is None
    assert not coverage.covered


# --- build_coverage_matrix (pure function) ---------------------------------


def test_coverage_matrix_summary_counts():
    coverages = [
        TechniqueCoverage(
            technique_id="a",
            attack_id="T1",
            sigma_rule_path="detections/sigma/a.yml",
            rule_title="A",
            matching_passed=1,
            matching_total=1,
            non_matching_passed=1,
            non_matching_total=1,
        ),
        TechniqueCoverage(
            technique_id="b",
            attack_id="T2",
            sigma_rule_path=None,
            rule_title=None,
            matching_passed=0,
            matching_total=0,
            non_matching_passed=0,
            non_matching_total=0,
        ),
    ]

    matrix = build_coverage_matrix(coverages)

    assert matrix["summary"] == {"total_techniques": 2, "covered": 1, "coverage_pct": 50.0}
    assert matrix["techniques"][0]["covered"] is True
    assert matrix["techniques"][1]["covered"] is False


def test_coverage_requires_all_fixtures_to_pass_not_just_some():
    partial = TechniqueCoverage(
        technique_id="a",
        attack_id="T1",
        sigma_rule_path="detections/sigma/a.yml",
        rule_title="A",
        matching_passed=1,
        matching_total=2,  # one matching fixture failed to match
        non_matching_passed=1,
        non_matching_total=1,
    )
    assert not partial.covered
