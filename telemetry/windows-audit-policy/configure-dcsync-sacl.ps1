# telemetry/windows-audit-policy/configure-dcsync-sacl.ps1
#
# Adds a SACL (audit ACE) on the domain naming context for the two
# extended rights DCSync actually uses, so a DCSync attempt (the last
# technique in attack/chains.py's domain_dominance chain) produces a 4662
# event with those rights' GUIDs in it — this is the only way DCSync is
# detectable; there is no dedicated "DCSync happened" event otherwise.
#
# The two GUIDs below (DS-Replication-Get-Changes and
# DS-Replication-Get-Changes-All) are the widely-published values for
# these extended rights. VERIFY against a live AD schema
# (Get-ADObject -SearchBase (Get-ADRootDSE).schemaNamingContext -Filter
# "objectClass -eq 'controlAccessRight'" -Properties rightsGuid | Where
# Name -like "*Replicating*") before relying on this — this script has not
# been run against a real domain (see ROADMAP.md).
#
# Requires the Directory Service Access audit subcategory enabled first —
# see configure-audit-policy.ps1.

Import-Module ActiveDirectory

$domainDN = (Get-ADDomain).DistinguishedName

$dsReplicationGetChanges    = [GUID]"1131f6aa-9c07-11d1-f79f-00c04fc2dcd2"
$dsReplicationGetChangesAll = [GUID]"1131f6ad-9c07-11d1-f79f-00c04fc2dcd2"

$acl = Get-Acl -Path "AD:\$domainDN"

# Audit "Everyone" (S-1-1-0) attempting these rights — a legitimate DC's
# own replication traffic uses a different security context (the DC
# computer account performing normal intra-forest replication is expected
# and should be filtered out at the Sigma-rule stage in Phase 4, not here);
# this SACL's job is just to make the attempt visible at all.
$everyone = [System.Security.Principal.SecurityIdentifier]"S-1-1-0"

foreach ($rightGuid in @($dsReplicationGetChanges, $dsReplicationGetChangesAll)) {
    $auditRule = New-Object System.DirectoryServices.ActiveDirectoryAuditRule(
        $everyone,
        [System.DirectoryServices.ActiveDirectoryRights]::ExtendedRight,
        [System.Security.AccessControl.AuditFlags]"Success,Failure",
        $rightGuid
    )
    $acl.AddAuditRule($auditRule)
}

Set-Acl -Path "AD:\$domainDN" -AclObject $acl

Write-Output "DCSync SACL applied to $domainDN."
