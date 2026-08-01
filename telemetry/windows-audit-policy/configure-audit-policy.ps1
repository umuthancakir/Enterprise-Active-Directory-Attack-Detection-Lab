# telemetry/windows-audit-policy/configure-audit-policy.ps1
#
# Enables the Advanced Audit Policy subcategories this lab's detections
# depend on. Sysmon (telemetry/sysmon/) cannot see Kerberos ticket
# operations or AD object access/replication — these Windows Security
# channel events are the ONLY source for detecting Kerberoasting (item 1),
# AS-REP roasting (item 2), and DCSync. See ADR 0006 and
# telemetry/windows-audit-policy/README.md for the full mapping.
#
# Run on dc01 (and mem01, for local logon/account-management coverage).
# In a larger environment this belongs in a GPO
# (Computer Configuration > Policies > Windows Settings > Security
# Settings > Advanced Audit Policy Configuration) rather than a per-host
# script — noted as a Phase 2 follow-up (this lab's small enough that a
# script applied by config/dc is a reasonable substitute for now, once
# wired into Ansible — see ROADMAP.md).
#
# STATUS: written, not run against a real host — see ROADMAP.md.

$categories = @(
    # Kerberos Authentication Service: event 4768 (TGT issued) — needed to
    # spot AS-REP roasting (item 2): a 4768 with the "Pre-Authentication
    # Type" field absent/0 is the AS-REP-roastable signature.
    "Kerberos Authentication Service",

    # Kerberos Service Ticket Operations: event 4769 (service ticket
    # requested) — needed for Kerberoasting (item 1): a 4769 requesting an
    # RC4 (0x17) ticket for a service account SPN is the classic signature.
    "Kerberos Service Ticket Operations",

    # Directory Service Access: event 4662 (an operation was performed on
    # an AD object) — needed for DCSync (requires a SACL on the domain NC,
    # see configure-dcsync-sacl.ps1) and for catching abuse of the
    # GenericAll grant in item 4 (requires a SACL on Domain-Backups, see
    # configure-object-sacls.ps1).
    "Directory Service Access",

    # Directory Service Changes: event 5136 (an AD object was modified) —
    # complements 4662 with a human-readable before/after for ACL and
    # attribute changes, including the GPO edit-rights abuse in item 6.
    "Directory Service Changes",

    # Security Group Management: events 4728/4732/4756 etc — group
    # membership changes, relevant if any technique adds an account to a
    # privileged group as part of privilege escalation.
    "Security Group Management",

    # User Account Management: events 4720/4724/4738 etc — account
    # creation/password reset, relevant to item 4's password-reset abuse
    # path and to any credential-based persistence a chain establishes.
    "User Account Management",

    # File System: event 4663 (an attempt was made to access an object) —
    # needed for item 7 (plaintext creds planted in SYSVOL): only fires on
    # files with a SACL, see configure-sysvol-file-sacl.ps1. Distinct from
    # "Directory Service Access" above, which covers AD objects, not the
    # filesystem.
    "File System"
)

foreach ($category in $categories) {
    auditpol /set /subcategory:"$category" /success:enable /failure:enable
}

Write-Output "Configured $($categories.Count) audit subcategories. Verify with: auditpol /get /category:*"
