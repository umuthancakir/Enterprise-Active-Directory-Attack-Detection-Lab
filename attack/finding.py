"""The normalized result schema every technique run produces.

One Finding per (technique, target) pair, regardless of whether the run
was a dry-run (mock fixture data, no tool actually invoked) or live
(real tool output). Downstream consumers — the Phase 4 detection-coverage
matrix, the Phase 5 platform's run history API — depend on this shape
staying stable and identical across both modes, so a scenario run in
dry-run mode today looks like exactly what a live run will look like once
a lab exists to run it against.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

Mode = Literal["dry_run", "live"]
Status = Literal["would_run", "success", "failed"]


@dataclasses.dataclass(frozen=True)
class Finding:
    scenario: str
    technique_id: str
    attack_id: str
    attack_url: str
    target_host_id: str
    target_ip: str
    tool: str
    command: list[str]
    mode: Mode
    status: Status
    summary: str
    raw_output: Any
    timestamp: str = dataclasses.field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def write_run(findings: list[Finding], results_dir: Path, run_id: str) -> Path:
    """Persist a scenario run's findings as JSON. attack/results/ is gitignored (Phase 0
    .gitignore) — these are run artifacts, not source."""
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / f"{run_id}.json"
    out_path.write_text(json.dumps([f.to_dict() for f in findings], indent=2))
    return out_path
