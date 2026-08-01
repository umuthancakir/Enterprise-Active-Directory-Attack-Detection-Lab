# Windows Event Forwarding

`dc01` is the WEF collector; `mem01` forwards to it. See
[ADR 0006](../../docs/adr/0006-telemetry-architecture.md) for why WEF was
chosen over per-host Winlogbeat.

## Setup (currently manual — see "Not done" below)

**On the collector (`dc01`):**

```powershell
wecutil qc /q                                   # enable + start the Windows Event Collector service
wecutil cs telemetry\wef\subscription.xml       # create the subscription from this directory's XML
```

**On every source host (`mem01`)**, via Group Policy (Computer
Configuration > Policies > Administrative Templates > Windows Components >
Event Forwarding > "Configure target Subscription Manager", linked to
`OU=LabComputers` — the same OU `config/dc/tasks/misconfigs.yml`'s item 6
GPO targets, though this should be a *separate* GPO, not reusing that
deliberately-misconfigured one):

```
Server=http://dc01.eadadl.lab:5985/wsman/SubscriptionManager/WEC,Refresh=60
```

Source hosts also need the "Windows Remote Management (HTTP-In)" firewall
rule enabled (already true — `infra/local/packer/http-windows/bootstrap.ps1`
opens 5985 for WinRM, and WEF-over-HTTP reuses that same port/rule) and the
`Network Service` account needs read access to the Security log, granted
via:

```powershell
wevtutil sl Security /ca:O:BAG:SYD:(A;;0x1;;;S-1-5-20)(A;;0x5;;;BA)(A;;0x1;;;SO)(A;;0x1;;;S-1-5-32-573)
```

(`S-1-5-20` is the well-known SID for `NT AUTHORITY\NETWORK SERVICE` — not
templated, safe to use as-is.)

## Verifying it's working

```powershell
# On dc01, after mem01 has had a few minutes to check in:
wecutil gr eadadl-lab-forwarding
Get-WinEvent -LogName ForwardedEvents -MaxEvents 5
```

## Status

`subscription.xml` is written and well-formed XML, but nothing here has
been applied to a real collector/source pair — no lab exists yet (see
ROADMAP.md).

## Not done / follow-up

- None of the setup above is in `config/dc`/`config/member`'s Ansible
  roles yet — it's a manual, documented procedure for now. Turning it into
  Ansible tasks (feature/WriteDacl on the Security log's SDDL, GPO
  creation via the same pattern `config/dc/tasks/misconfigs.yml` item 6
  uses, `wecutil` invocations) is tracked as Phase 2 follow-up work.
