# telemetry/windows-audit-policy/configure-object-sacls.ps1
#
# Adds a SACL to Domain-Backups (the target of docs/vulnerabilities.md
# item 4's GenericAll grant to helpdesk-jsmith) so that exercising the ACL
# abuse produces a 4662/5136 event, rather than being silently invisible
# the way an un-audited object's ACL abuse would be. This is what turns
# "we granted GenericAll" into "we can detect someone using it."
#
# Requires the Directory Service Access audit subcategory enabled first —
# see configure-audit-policy.ps1.
#
# STATUS: written, not run against a real domain — see ROADMAP.md.

Import-Module ActiveDirectory

$targetGroup = Get-ADGroup -Identity "Domain-Backups"
$acl = Get-Acl -Path "AD:\$($targetGroup.DistinguishedName)"

$everyone = [System.Security.Principal.SecurityIdentifier]"S-1-1-0"

# WriteDacl + WriteProperty cover both "someone changed who can do what to
# this object" (the ACL-abuse setup itself, if it were ever repeated) and
# "someone used their granted rights to change an attribute" (e.g. a
# password reset via the GenericAll grant) — item 4's actual exploitation
# path.
$rights = [System.DirectoryServices.ActiveDirectoryRights]"WriteDacl, WriteProperty, GenericAll"

$auditRule = New-Object System.DirectoryServices.ActiveDirectoryAuditRule(
    $everyone,
    $rights,
    [System.Security.AccessControl.AuditFlags]"Success,Failure"
)
$acl.AddAuditRule($auditRule)

Set-Acl -Path "AD:\$($targetGroup.DistinguishedName)" -AclObject $acl

Write-Output "SACL applied to Domain-Backups ($($targetGroup.DistinguishedName))."
