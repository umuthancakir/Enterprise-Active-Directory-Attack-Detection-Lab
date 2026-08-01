"""Parses test definitions in the public Atomic Red Team project's YAML
schema (https://github.com/redcanaryco/atomic-red-team) and renders their
`#{argument}`-templated commands.

This is a parser for ART's schema, not a vendored copy of the upstream
project. `attack/integrations/atomics/` holds a small, hand-written local
catalog (3 files, one technique each) modeled on that public schema —
recon/discovery commands well-known and stable enough to write from
general knowledge, not fetched from the live repository. See
`attack/integrations/README.md` for why the catalog is small and how to
add real upstream test files if a full integration is ever wanted.

Every rendered command still goes through the exact same scope guard as
every other technique in this project — see `atomic_runner.py`. Atomic
Red Team is one of the tools SECURITY.md names as acceptable to
orchestrate; this module orchestrates its test *definitions*, not its
(separate, PowerShell-based) `Invoke-AtomicTest` execution runner.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from typing import Any

import yaml

ATOMICS_DIR = Path(__file__).resolve().parent / "atomics"

_ARG_PATTERN = re.compile(r"#\{(\w+)\}")


@dataclasses.dataclass(frozen=True)
class AtomicTest:
    technique_id: str
    display_name: str
    test_name: str
    description: str
    supported_platforms: tuple[str, ...]
    executor_name: str
    command: str
    input_arguments: dict[str, str]  # arg name -> default value

    def render_command(self, overrides: dict[str, str] | None = None) -> str:
        """Substitute #{arg_name} placeholders — ART's real templating syntax —
        with an override value if given, else the argument's declared default."""
        values = dict(self.input_arguments)
        values.update(overrides or {})

        def _substitute(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in values:
                raise KeyError(f"'{name}' has no default and no override was provided")
            return values[name]

        return _ARG_PATTERN.sub(_substitute, self.command)


def _parse_test(technique_id: str, display_name: str, raw_test: dict[str, Any]) -> AtomicTest:
    input_arguments = {
        arg_name: str(arg_spec.get("default", ""))
        for arg_name, arg_spec in raw_test.get("input_arguments", {}).items()
    }
    executor = raw_test["executor"]
    return AtomicTest(
        technique_id=technique_id,
        display_name=display_name,
        test_name=raw_test["name"],
        description=raw_test.get("description", "").strip(),
        supported_platforms=tuple(raw_test.get("supported_platforms", [])),
        executor_name=executor["name"],
        command=executor["command"].strip(),
        input_arguments=input_arguments,
    )


def load_atomic_tests_from_yaml(path: Path) -> list[AtomicTest]:
    """Parse one ART-schema YAML file (one technique, one or more atomic_tests)."""
    data = yaml.safe_load(path.read_text())
    technique_id = data["attack_technique"]
    display_name = data["display_name"]
    return [_parse_test(technique_id, display_name, t) for t in data["atomic_tests"]]


def load_local_catalog() -> dict[str, list[AtomicTest]]:
    """All tests under attack/integrations/atomics/, keyed by ATT&CK technique ID."""
    catalog: dict[str, list[AtomicTest]] = {}
    for yaml_path in sorted(ATOMICS_DIR.glob("*.yaml")):
        tests = load_atomic_tests_from_yaml(yaml_path)
        if tests:
            catalog[tests[0].technique_id] = tests
    return catalog
