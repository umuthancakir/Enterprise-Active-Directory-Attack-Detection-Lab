# Atomic Red Team integration

`atomic_red_team.py` parses test definitions in the public
[Atomic Red Team](https://github.com/redcanaryco/atomic-red-team)
project's YAML schema and renders their `#{argument}`-templated commands.
`atomic_runner.py` runs a parsed test in dry-run mode through the exact
same scope guard as [`attack/runner.py`](../runner.py).

## What this is — and isn't

This is a **parser for ART's schema**, not a vendored copy of the
upstream project (which is thousands of files under active,
independently-licensed development — pulling it in wholesale is a bigger
decision than this pass makes unilaterally). `atomics/` holds a **small,
hand-written local catalog**: 3 files, one technique each
(`T1087.002` domain admin enumeration, `T1069.002` domain group
enumeration, `T1018` domain computer enumeration) — all well-known,
extremely standard `net.exe` recon one-liners, written from general
knowledge rather than fetched from the live repository. They are modeled
on ART's real, publicly documented schema (`attack_technique`,
`display_name`, `atomic_tests[].{name, description, supported_platforms,
input_arguments, executor}`), not invented syntax.

If a fuller integration is wanted later: point `load_atomic_tests_from_yaml()`
at a real file from a cloned upstream `atomics/` directory — the parser
should handle it unmodified, since it targets the documented schema, not
just these 3 examples. That hasn't been attempted or verified here.

## Usage

```python
from attack.integrations.atomic_runner import run_atomic_test

finding = run_atomic_test("T1087.002")  # dry-run, gated by the real scope guard
print(finding.command)
```

Or via the CLI: `make attack-atomic TECHNIQUE=T1087.002`.

## Design

Same posture as [`ir/automation/responder.py`](../../ir/automation/README.md):
**dry-run only, no live-execution mode exists**. Unlike
`attack/techniques.py`'s hand-modeled techniques (which have an
unexercised-but-implemented `--live` path), atomic tests sourced from an
external, larger, less-curated catalog get a stricter boundary — this
integration proves the *plumbing* (parse a real schema, render a
templated command, resolve a target through the scope guard, emit a
`Finding`) without ever executing anything, live lab or not.

## Status

Tested — 10 passing tests in `tests/test_atomic_red_team.py` (parser,
command rendering including override-vs-default and missing-argument
error cases, and the scope-guard safety property). `ruff`/`mypy --strict`
clean. Never run against a real host, by design.
