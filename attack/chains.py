"""Stitched attack chains: ordered technique sequences, each mapped to the
recon -> initial access -> credential access -> lateral movement -> domain
dominance narrative from the project brief.
"""

from __future__ import annotations

import dataclasses

from attack.techniques import TECHNIQUES


@dataclasses.dataclass(frozen=True)
class Chain:
    id: str
    description: str
    technique_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        unknown = [t for t in self.technique_ids if t not in TECHNIQUES]
        if unknown:
            raise ValueError(f"Chain '{self.id}' references unknown technique id(s): {unknown}")


CHAINS: dict[str, Chain] = {
    "credential_harvest": Chain(
        id="credential_harvest",
        description=(
            "Recon, then credential access via Kerberoasting + AS-REP roasting "
            "(docs/vulnerabilities.md items 1-2)."
        ),
        technique_ids=("bloodhound_collect", "kerberoasting", "asrep_roasting"),
    ),
    "domain_dominance": Chain(
        id="domain_dominance",
        description=(
            "Full recon -> privilege escalation (ACL abuse) -> lateral movement "
            "(unconstrained delegation coercion) -> domain dominance (DCSync). "
            "docs/vulnerabilities.md items 3-4."
        ),
        technique_ids=(
            "bloodhound_collect",
            "acl_genericall_abuse",
            "unconstrained_delegation_coerce",
            "dcsync",
        ),
    ),
    "gpo_and_sysvol_abuse": Chain(
        id="gpo_and_sysvol_abuse",
        description=(
            "Recon, then abuse granted GPO edit rights for persistence and read "
            "plaintext credentials planted in SYSVOL. docs/vulnerabilities.md "
            "items 6-7 — independent of the domain_dominance chain, since items "
            "6/7 don't depend on items 3/4's delegation/ACL setup."
        ),
        technique_ids=(
            "bloodhound_collect",
            "gpo_edit_abuse",
            "sysvol_credential_read",
        ),
    ),
}
