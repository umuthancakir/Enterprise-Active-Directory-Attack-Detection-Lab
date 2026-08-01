# telemetry/windows-audit-policy/configure-gpo-sacl.ps1
#
# Adds a SACL to the Lab-Workstation-Baseline GPO's AD object (a
# groupPolicyContainer, stored under CN=Policies,CN=System,<domain DN>) so
# that a modification made via the deliberate item 6 GPO edit-rights grant
# (config/dc/tasks/misconfigs.yml) produces a 4662/5136 event instead of
# being silently invisible.
#
# Requires the Directory Service Access / Directory Service Changes audit
# subcategories enabled first — see configure-audit-policy.ps1.
#
# STATUS: written, not run against a real domain — see ROADMAP.md.

Import-Module ActiveDirectory
Import-Module GroupPolicy

$gpo = Get-GPO -Name "Lab-Workstation-Baseline"
$gpoDN = "CN={$($gpo.Id.ToString().ToUpper())},CN=Policies,CN=System,$((Get-ADDomain).DistinguishedName)"

$acl = Get-Acl -Path "AD:\$gpoDN"
$everyone = [System.Security.Principal.SecurityIdentifier]"S-1-1-0"

# WriteProperty (any attribute change, including GPO content pointers) +
# WriteDacl (permission changes on the GPO object itself) — mirrors
# configure-object-sacls.ps1's rights choice for the same reasoning.
$rights = [System.DirectoryServices.ActiveDirectoryRights]"WriteProperty, WriteDacl"

$auditRule = New-Object System.DirectoryServices.ActiveDirectoryAuditRule(
    $everyone,
    $rights,
    [System.Security.AccessControl.AuditFlags]"Success,Failure"
)
$acl.AddAuditRule($auditRule)

Set-Acl -Path "AD:\$gpoDN" -AclObject $acl

Write-Output "SACL applied to GPO 'Lab-Workstation-Baseline' ($gpoDN)."
