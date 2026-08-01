"""Validates every Sigma rule and proves it fires against fixture telemetry.

Usage: `make detections-test` or `python3 -m detections.test_runner`.

Deliberately does NOT depend on network access (sigma-cli's `sigma check`
fetches MITRE ATT&CK tactic data from GitHub for tag validation, which
would make this fail offline or in an egress-restricted CI runner) —
validation here is pySigma's local parser (real schema/syntax checking)
plus this module's own lightweight semantic checks (references cites the
technique's ATT&CK URL, tags cite its ATT&CK ID). See
attack/runner.py's module docstring for the same "testable without
external dependencies" design goal applied to the attack engine.

For each technique in attack.techniques.TECHNIQUES:
  1. Look for detections/sigma/{technique_id}.yml. Missing = uncovered.
  2. Parse it with pySigma; validate references/tags cite the right ATT&CK ID.
  3. Load detections/fixtures/{technique_id}.json and run every "matching"
     event through detections.matcher.rule_matches_event (must match) and
     every "non_matching" event (must NOT match).
  4. Record a TechniqueCoverage entry either way.
Writes detections/coverage_matrix.json (feeds the Phase 5 heatmap) and
exits non-zero if any technique is uncovered or any fixture assertion fails.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sigma.exceptions import SigmaError
from sigma.rule import SigmaRule

from attack.techniques import TECHNIQUES, Technique
from detections.coverage import TechniqueCoverage, build_coverage_matrix
from detections.matcher import rule_matches_event

SIGMA_DIR = Path(__file__).resolve().parent / "sigma"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
COVERAGE_MATRIX_PATH = Path(__file__).resolve().parent / "coverage_matrix.json"


class RuleSemanticError(Exception):
    """The rule parses as valid Sigma but doesn't cite the technique it's meant to detect."""


def _validate_rule_semantics(rule: SigmaRule, technique: Technique) -> None:
    if technique.attack_url not in rule.references:
        raise RuleSemanticError(
            f"rule for '{technique.id}' does not cite {technique.attack_url} in its references"
        )
    expected_tag = f"attack.{technique.attack_id.lower()}"
    if not any(str(tag) == expected_tag for tag in rule.tags):
        raise RuleSemanticError(
            f"rule for '{technique.id}' is missing the '{expected_tag}' tag"
        )


def evaluate_technique(technique: Technique) -> TechniqueCoverage:
    rule_path = SIGMA_DIR / f"{technique.id}.yml"
    if not rule_path.exists():
        return TechniqueCoverage(
            technique_id=technique.id,
            attack_id=technique.attack_id,
            sigma_rule_path=None,
            rule_title=None,
            matching_passed=0,
            matching_total=0,
            non_matching_passed=0,
            non_matching_total=0,
        )

    rule = SigmaRule.from_yaml(rule_path.read_text())
    _ = rule.detection.parsed_condition  # force parse; raises SigmaError if malformed
    _validate_rule_semantics(rule, technique)

    fixture_path = FIXTURES_DIR / f"{technique.id}.json"
    fixtures = json.loads(fixture_path.read_text()) if fixture_path.exists() else {}
    matching_events = fixtures.get("matching", [])
    non_matching_events = fixtures.get("non_matching", [])

    matching_passed = sum(1 for e in matching_events if rule_matches_event(rule, e))
    non_matching_passed = sum(1 for e in non_matching_events if not rule_matches_event(rule, e))

    if rule_path.is_relative_to(Path.cwd()):
        rule_path_str = str(rule_path.relative_to(Path.cwd()))
    else:
        rule_path_str = str(rule_path)

    return TechniqueCoverage(
        technique_id=technique.id,
        attack_id=technique.attack_id,
        sigma_rule_path=rule_path_str,
        rule_title=rule.title,
        matching_passed=matching_passed,
        matching_total=len(matching_events),
        non_matching_passed=non_matching_passed,
        non_matching_total=len(non_matching_events),
    )


def main() -> int:
    coverages = []
    had_error = False

    for technique in TECHNIQUES.values():
        try:
            coverage = evaluate_technique(technique)
        except (SigmaError, RuleSemanticError) as exc:
            print(f"[{technique.id}] ERROR: {exc}", file=sys.stderr)
            had_error = True
            continue

        coverages.append(coverage)
        status = "OK" if coverage.covered else "FAIL"
        print(
            f"[{technique.id}] ({technique.attack_id}) {status} — "
            f"matching {coverage.matching_passed}/{coverage.matching_total}, "
            f"non_matching {coverage.non_matching_passed}/{coverage.non_matching_total}, "
            f"rule={coverage.sigma_rule_path or 'MISSING'}"
        )
        if not coverage.covered:
            had_error = True

    matrix = build_coverage_matrix(coverages)
    COVERAGE_MATRIX_PATH.write_text(json.dumps(matrix, indent=2))
    print(
        f"\nCoverage: {matrix['summary']['covered']}/{matrix['summary']['total_techniques']} "
        f"({matrix['summary']['coverage_pct']}%) — wrote {COVERAGE_MATRIX_PATH}"
    )

    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
