# telemetry/windows-audit-policy/configure-sysvol-file-sacl.ps1
#
# Adds an NTFS SACL to the plaintext-credential script item 7 plants in
# SYSVOL (config/dc/tasks/misconfigs.yml deploys
# map-network-drive.ps1 via config/dc/templates/map-network-drive.ps1.j2)
# so that reading it produces a 4663 event. Without this, item 7 is
# completely invisible at read-time — there is no other event source for
# "someone opened this specific file."
#
# This is a FILESYSTEM SACL (System.Security.AccessControl.FileSystemAuditRule
# via the filesystem provider), not an AD object SACL — distinct from
# configure-gpo-sacl.ps1/configure-object-sacls.ps1/configure-dcsync-sacl.ps1,
# which all use the AD: PSDrive. Requires the "File System" audit
# subcategory enabled first — see configure-audit-policy.ps1.
#
# STATUS: written, not run against a real host — see ROADMAP.md.

$scriptPath = "C:\Windows\SYSVOL\domain\scripts\map-network-drive.ps1"

$acl = Get-Acl -Path $scriptPath
$everyone = [System.Security.Principal.SecurityIdentifier]"S-1-1-0"

# ReadData specifically — this is a "did someone read the planted
# credentials" detector, not a general file-integrity monitor. Success
# only: a failed read attempt still didn't expose the credential, and
# failure auditing here would mostly just capture routine ACL-check noise
# from unrelated processes enumerating SYSVOL.
$auditRule = New-Object System.Security.AccessControl.FileSystemAuditRule(
    $everyone,
    [System.Security.AccessControl.FileSystemRights]"ReadData",
    [System.Security.AccessControl.AuditFlags]"Success"
)
$acl.AddAuditRule($auditRule)

Set-Acl -Path $scriptPath -AclObject $acl

Write-Output "SACL applied to $scriptPath."
