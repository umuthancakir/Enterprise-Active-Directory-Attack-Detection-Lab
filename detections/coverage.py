"""Builds the attack -> detection coverage matrix.

Pure data transform (TechniqueCoverage list in, matrix dict out) so
detections/test_runner.py's file I/O and this module's structure can be
tested independently — same pattern as scripts/sync_scope.py and
config/inventory/lab_scope_inventory.py's pure-function refactor earlier
this session. Feeds the Phase 5 platform's ATT&CK Navigator-style heatmap
(not built yet — see ROADMAP.md).
"""

from __future__ import annotations

import dataclasses
import datetime
from typing import Any


@dataclasses.dataclass(frozen=True)
class TechniqueCoverage:
    technique_id: str
    attack_id: str
    sigma_rule_path: str | None
    rule_title: str | None
    matching_passed: int
    matching_total: int
    non_matching_passed: int
    non_matching_total: int

    @property
    def covered(self) -> bool:
        return (
            self.sigma_rule_path is not None
            and self.matching_total > 0
            and self.matching_passed == self.matching_total
            and self.non_matching_passed == self.non_matching_total
        )


def build_coverage_matrix(coverages: list[TechniqueCoverage]) -> dict[str, Any]:
    covered = [c for c in coverages if c.covered]
    total = len(coverages)
    return {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "techniques": [
            {
                "technique_id": c.technique_id,
                "attack_id": c.attack_id,
                "sigma_rule": c.sigma_rule_path,
                "rule_title": c.rule_title,
                "fixture_tests": {
                    "matching_passed": c.matching_passed,
                    "matching_total": c.matching_total,
                    "non_matching_passed": c.non_matching_passed,
                    "non_matching_total": c.non_matching_total,
                },
                "covered": c.covered,
            }
            for c in coverages
        ],
        "summary": {
            "total_techniques": total,
            "covered": len(covered),
            "coverage_pct": round(100 * len(covered) / total, 1) if total else 0.0,
        },
    }
