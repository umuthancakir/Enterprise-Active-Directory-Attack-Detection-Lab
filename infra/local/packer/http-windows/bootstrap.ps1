# infra/local/packer/http-windows/bootstrap.ps1
#
# Run once via Autounattend.xml's FirstLogonCommands, before Packer's own
# WinRM communicator can connect. Only responsible for getting WinRM up —
# everything else (Windows Update, firewall rule cleanup) happens in
# windows-server.pkr.hcl's provisioner blocks, which run over WinRM once
# this succeeds.

winrm quickconfig -quiet -force
Enable-PSRemoting -Force -SkipNetworkProfileCheck
Set-Item -Path WSMan:\localhost\Service\AllowUnencrypted -Value $true
Set-Item -Path WSMan:\localhost\Service\Auth\Basic -Value $true

New-NetFirewallRule -Name "WinRM-Bootstrap" -DisplayName "WinRM (bootstrap)" `
  -Protocol TCP -LocalPort 5985 -Action Allow -Direction Inbound

Restart-Service WinRM
