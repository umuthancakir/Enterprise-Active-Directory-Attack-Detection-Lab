# infra/local/packer/windows-server.pkr.hcl
#
# Builds a base Windows Server 2022 qcow2 image via QEMU's TCG (software)
# x86_64 emulation — this Mac is Apple Silicon with no hardware-acceleration
# path for an x86_64 guest, so the build is slow but genuine (see
# docs/adr/0004-revert-to-local-utm.md). Used for both dc01 and mem01 via
# separate `packer build -var vm_name=... -var-file=...` invocations — see
# infra/local/dc.pkrvars.hcl and infra/local/member.pkrvars.hcl.
#
# Network device is e1000 (Intel NIC, natively supported by Windows Server
# without extra drivers) rather than virtio, specifically to avoid needing
# a virtio driver ISO during unattended install — one less moving part.

packer {
  required_plugins {
    qemu = {
      source  = "github.com/hashicorp/qemu"
      version = "~> 1.1"
    }
    windows-update = {
      source  = "github.com/rgl/windows-update"
      version = "~> 0.16"
    }
  }
}

variable "vm_name" {
  type        = string
  description = "dc01 or mem01 — used for the output image filename and Autounattend ComputerName."
}

variable "iso_url" {
  type        = string
  description = "Local path or URL to the Windows Server 2022 evaluation ISO. Download from https://www.microsoft.com/evalcenter/download-windows-server-2022 — no default, must be supplied (see README.md Prerequisites)."
}

variable "iso_checksum" {
  type        = string
  description = "sha256:<hash> for iso_url. Get this from the same Evaluation Center download page — never skip verifying it."
}

variable "admin_password" {
  type      = string
  sensitive = true
}

variable "output_directory" {
  type    = string
  default = "infra/local/build/images"
}

source "qemu" "windows_server" {
  iso_url          = var.iso_url
  iso_checksum     = var.iso_checksum
  output_directory = "${var.output_directory}/${var.vm_name}"
  vm_name          = "${var.vm_name}.qcow2"
  format           = "qcow2"

  qemu_binary = "qemu-system-x86_64"
  accelerator = "tcg" # no HVF for a foreign-arch (x86_64) guest on Apple Silicon

  cpus      = 2
  memory    = 4096
  disk_size = "60000M"

  net_device     = "e1000"
  disk_interface = "ide"

  headless = true

  cd_files = ["${path.root}/http-windows/Autounattend.xml", "${path.root}/http-windows/bootstrap.ps1"]
  cd_label = "cidata"

  communicator   = "winrm"
  winrm_username = "labadmin"
  winrm_password = var.admin_password
  winrm_timeout  = "6h" # TCG-emulated Windows Server install is genuinely slow — see ADR 0004

  shutdown_command = "shutdown /s /t 10 /f /d p:4:1"
}

build {
  sources = ["source.qemu.windows_server"]

  provisioner "powershell" {
    inline = [
      "Set-ExecutionPolicy Unrestricted -Force",
      "winrm quickconfig -quiet",
      "Enable-PSRemoting -Force",
      "New-NetFirewallRule -Name WinRM-HostOnly -DisplayName 'WinRM (lab host-only)' -Protocol TCP -LocalPort 5985 -Action Allow"
    ]
  }

  provisioner "windows-update" {}
}
