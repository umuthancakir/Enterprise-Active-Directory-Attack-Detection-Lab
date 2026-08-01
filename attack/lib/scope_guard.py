"""The single, shared chokepoint every attack entry point must resolve targets through.

See docs/adr/0002-scope-guard.md. Every technique/chain invocation in
attack/, and later the FastAPI runner endpoint in platform/backend/, MUST
call ScopeGuard.resolve_target() before invoking any external offensive
tool. There is no override/bypass parameter anywhere in this module —
that is a deliberate design constraint, not an oversight. A target is only
ever resolved if it (a) exists in the scope file, (b) has a role not in
non_attackable_roles, (c) is marked provisioned, and (d) has a recorded IP.
Any other case raises ScopeViolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_SCOPE_FILE = Path(__file__).resolve().parents[2] / "inventory" / "lab-scope.yaml"

_REQUIRED_TOP_LEVEL_KEYS = ("version", "lab", "hosts")
_REQUIRED_HOST_FIELDS = ("id", "role", "provisioned")


class ScopeFileError(Exception):
    """The scope file itself is missing, unreadable, or malformed.

    Distinct from ScopeViolation: this means the scope guard couldn't even
    establish what's in scope, as opposed to establishing it and refusing a
    specific target. Callers should treat both as fatal — the distinction
    exists for clearer error messages and tests, not different handling.
    """


class ScopeViolation(Exception):
    """A target was refused. Never caught-and-continued past — see ADR 0002."""


@dataclass(frozen=True)
class Host:
    """A resolved, attackable host. Constructing one outside ScopeGuard.resolve_target() is not
    itself dangerous, but nothing in attack/ should ever do so — resolve_target() is the only
    sanctioned source of a Host that's actually safe to point tooling at.
    """

    id: str
    role: str
    hostname: str
    ip: str
    os: str


def _load_scope_data(scope_file: Path) -> dict[str, Any]:
    if not scope_file.exists():
        raise ScopeFileError(f"scope file not found: {scope_file}")

    try:
        raw = scope_file.read_text()
    except OSError as exc:
        raise ScopeFileError(f"could not read scope file {scope_file}: {exc}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ScopeFileError(f"scope file {scope_file} is not valid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ScopeFileError(
            f"scope file {scope_file} root must be a mapping, got {type(data).__name__}"
        )

    for key in _REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            raise ScopeFileError(f"scope file {scope_file} missing required top-level key: '{key}'")

    if not isinstance(data["hosts"], list):
        raise ScopeFileError(f"scope file {scope_file}: 'hosts' must be a list")

    seen_ids: set[str] = set()
    for host in data["hosts"]:
        if not isinstance(host, dict):
            raise ScopeFileError(
                f"scope file {scope_file}: each host entry must be a mapping, got {host!r}"
            )
        for field in _REQUIRED_HOST_FIELDS:
            if field not in host:
                raise ScopeFileError(
                    f"scope file {scope_file}: host entry missing required field "
                    f"'{field}': {host!r}"
                )
        if host["id"] in seen_ids:
            raise ScopeFileError(f"scope file {scope_file}: duplicate host id '{host['id']}'")
        seen_ids.add(host["id"])

    return data


class ScopeGuard:
    """Loads inventory/lab-scope.yaml once and answers "can I attack this host?" — nothing else.

    Deliberately has no method to add, modify, or mark a host provisioned:
    that would make this the kind of "helper" that quietly grows a bypass
    path over time. Scope changes happen by editing lab-scope.yaml (a
    reviewable, version-controlled change — ADR 0002), not through this API.
    """

    def __init__(self, scope_file: Path | str = DEFAULT_SCOPE_FILE) -> None:
        self._scope_file = Path(scope_file)
        self._scope = _load_scope_data(self._scope_file)
        self._hosts_by_id: dict[str, dict[str, Any]] = {h["id"]: h for h in self._scope["hosts"]}

    @property
    def non_attackable_roles(self) -> frozenset[str]:
        return frozenset(self._scope.get("non_attackable_roles", []))

    def resolve_target(self, host_id: str) -> Host:
        """Resolve host_id to an attackable Host, or raise ScopeViolation.

        This is the ONLY function in this codebase that should ever be
        called immediately before invoking an offensive tool against a
        specific host. If you find yourself wanting to skip it "just this
        once," that is exactly the failure mode ADR 0002 exists to prevent.
        """
        host = self._hosts_by_id.get(host_id)
        if host is None:
            raise ScopeViolation(
                f"'{host_id}' is not present in {self._scope_file} — refusing to target it. "
                "Add it to inventory/lab-scope.yaml first (a reviewable change), "
                "there is no override."
            )

        if host["role"] in self.non_attackable_roles:
            raise ScopeViolation(
                f"'{host_id}' has role '{host['role']}', which is in non_attackable_roles — "
                "refusing to target it (e.g. the attacker box and SIEM host are never "
                "valid targets)."
            )

        if not host.get("provisioned"):
            raise ScopeViolation(
                f"'{host_id}' is in scope but not provisioned (provisioned: false/missing) — "
                "refusing to target it. Run `make sync-scope` after the lab is actually up."
            )

        ip = host.get("ip")
        if not ip:
            raise ScopeViolation(
                f"'{host_id}' is provisioned but has no recorded IP — refusing to target it."
            )

        return Host(
            id=host["id"],
            role=host["role"],
            hostname=host.get("hostname", ""),
            ip=ip,
            os=host.get("os", ""),
        )

    def list_attackable_hosts(self) -> list[Host]:
        """All hosts that would currently pass resolve_target() — used by attack/runner.py to
        validate a scenario's targets up front, not as an alternate resolution path."""
        result: list[Host] = []
        for host_id in self._hosts_by_id:
            try:
                result.append(self.resolve_target(host_id))
            except ScopeViolation:
                continue
        return result
