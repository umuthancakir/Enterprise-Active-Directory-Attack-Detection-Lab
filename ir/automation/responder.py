"""SOAR-style response automation: maps a detection hit (a technique_id,
matching the ones in attack/techniques.py and detections/sigma/) to the
concrete containment/eradication actions from the corresponding
ir/playbooks/*.md.

Deliberately mirrors attack/runner.py's design: every action resolves its
target through the SAME scope guard attack techniques use
(attack.lib.scope_guard) before doing anything, and defaults to a dry-run
mode that prints what it would do without touching a real host. An
account-disable or password-reset action is exactly as blast-radius-heavy
as an offensive technique — it deserves the identical safety scaffolding,
not a separate, less-guarded path just because it's "defensive."

Not every response action is safely automatable. DCSync's real remediation
(krbtgt rotated TWICE, with a replication-convergence wait in between) is
multi-step and time-gated — modeling it as a single command would imply a
false one-shot guarantee. Those actions are marked `automatable=False` and
point back to the manual playbook instead of a command.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from attack.lib.scope_guard import Host, ScopeGuard


@dataclasses.dataclass(frozen=True)
class ResponseAction:
    action_id: str
    description: str
    target_role: str
    automatable: bool
    # Present only when automatable=True. Same templating convention as
    # attack.techniques.Technique.command_template — {ip}/{hostname}
    # substituted, credential placeholders left literal.
    command_template: tuple[str, ...] | None = None
    playbook: str = ""  # relative path under ir/playbooks/, always present

    def build_command(self, host: Host) -> list[str]:
        if not self.automatable or self.command_template is None:
            raise ValueError(
                f"'{self.action_id}' is not automatable — see {self.playbook} "
                "for the manual procedure"
            )
        return [
            part.format(ip=host.ip, hostname=host.hostname) for part in self.command_template
        ]


RESPONSE_PLAYBOOK: dict[str, list[ResponseAction]] = {
    "kerberoasting": [
        ResponseAction(
            action_id="reset_kerberoastable_account_password",
            description=(
                "Rotate the targeted service account's password to invalidate "
                "the captured ticket."
            ),
            target_role="domain_controller",
            automatable=True,
            command_template=(
                "powershell.exe", "-Command",
                "Set-ADAccountPassword -Identity svc-sql -Reset "
                "-NewPassword (ConvertTo-SecureString '<new_random_password>' -AsPlainText -Force)",
            ),
            playbook="ir/playbooks/kerberoasting.md",
        ),
    ],
    "asrep_roasting": [
        ResponseAction(
            action_id="reset_asrep_roastable_account_password",
            description="Rotate the targeted account's password to invalidate the captured AS-REP.",
            target_role="domain_controller",
            automatable=True,
            command_template=(
                "powershell.exe", "-Command",
                "Set-ADAccountPassword -Identity svc-legacy -Reset "
                "-NewPassword (ConvertTo-SecureString '<new_random_password>' -AsPlainText -Force)",
            ),
            playbook="ir/playbooks/asrep-roasting.md",
        ),
    ],
    "acl_genericall_abuse": [
        ResponseAction(
            action_id="remove_unintended_acl_grant",
            description="Remove the GenericAll grant on the target object.",
            target_role="domain_controller",
            automatable=True,
            command_template=(
                "dsacls.exe", "<target_dn>", "/R", "EADADL\\helpdesk-jsmith",
            ),
            playbook="ir/playbooks/acl-abuse.md",
        ),
    ],
    "unconstrained_delegation_coerce": [
        ResponseAction(
            action_id="disable_unconstrained_delegation",
            description="Remove unconstrained delegation from the affected computer object.",
            target_role="domain_controller",
            automatable=True,
            command_template=(
                "powershell.exe", "-Command",
                "Set-ADComputer -Identity MEM01 -TrustedForDelegation $false",
            ),
            playbook="ir/playbooks/unconstrained-delegation.md",
        ),
    ],
    "dcsync": [
        ResponseAction(
            action_id="rotate_krbtgt_twice",
            description=(
                "krbtgt must be reset TWICE with a replication-convergence wait "
                "between resets to invalidate all outstanding tickets domain-wide. "
                "Multi-step and time-gated — not a single automatable command."
            ),
            target_role="domain_controller",
            automatable=False,
            playbook="ir/playbooks/dcsync.md",
        ),
    ],
}


@dataclasses.dataclass(frozen=True)
class ResponseRecord:
    technique_id: str
    action_id: str
    automatable: bool
    target_host_id: str | None
    command: list[str] | None
    status: str  # "would_run" | "manual_required"
    playbook: str


def respond_to_finding(
    technique_id: str,
    *,
    scope_file: Path | str | None = None,
) -> list[ResponseRecord]:
    """Dry-run only — see module docstring. There is no live-execution mode
    here; unlike attack/runner.py, automatically taking remediation action
    against a real domain without a human in the loop is a deliberately
    unbuilt capability, not an oversight."""
    actions = RESPONSE_PLAYBOOK.get(technique_id, [])
    if not actions:
        return []

    guard = ScopeGuard(scope_file) if scope_file is not None else ScopeGuard()
    records: list[ResponseRecord] = []

    for action in actions:
        if not action.automatable:
            records.append(
                ResponseRecord(
                    technique_id=technique_id,
                    action_id=action.action_id,
                    automatable=False,
                    target_host_id=None,
                    command=None,
                    status="manual_required",
                    playbook=action.playbook,
                )
            )
            continue

        candidates = [h for h in guard.list_attackable_hosts() if h.role == action.target_role]
        if not candidates:
            # Same fail-closed posture as attack/runner.py: no resolvable
            # target means no action, not a guess.
            continue
        host = candidates[0]
        records.append(
            ResponseRecord(
                technique_id=technique_id,
                action_id=action.action_id,
                automatable=True,
                target_host_id=host.id,
                command=action.build_command(host),
                status="would_run",
                playbook=action.playbook,
            )
        )

    return records
