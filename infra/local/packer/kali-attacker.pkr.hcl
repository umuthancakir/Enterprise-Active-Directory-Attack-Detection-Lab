# infra/local/packer/kali-attacker.pkr.hcl
#
# Builds attacker01 as native ARM64 Kali Linux — no emulation, uses HVF
# (Apple Hypervisor.framework) acceleration since guest arch matches host
# arch. See docs/adr/0004-revert-to-local-utm.md for why this host is
# native while dc01/mem01 are emulated.
#
# Automated via Debian-installer preseed (Kali is Debian-derived and uses
# the same d-i preseed mechanism) — see http-linux/preseed.cfg. Packer
# serves http-linux/ over its built-in ephemeral HTTP server; boot_command
# points the installer at it via the kernel append line.

packer {
  required_plugins {
    qemu = {
      source  = "github.com/hashicorp/qemu"
      version = "~> 1.1"
    }
  }
}

variable "iso_url" {
  type        = string
  description = "Kali Linux ARM64 installer ISO. Get the current 'installer-netinst' arm64 image and its sha256sum from https://www.kali.org/get-kali/#kali-installer-images — no default, must be supplied (URLs/checksums change with each Kali release)."
}

variable "iso_checksum" {
  type        = string
  description = "sha256:<hash> for iso_url, from the same Kali download page."
}

variable "admin_username" {
  type    = string
  default = "labadmin"
}

variable "admin_ssh_public_key" {
  type        = string
  description = "SSH public key installed for admin_username (private key is Terraform-style generated in infra/local/generate_bundles.py output — see that script)."
}

variable "firmware" {
  type        = string
  default     = "/opt/homebrew/share/qemu/edk2-aarch64-code.fd"
  description = "UEFI firmware for qemu-system-aarch64 (installed alongside qemu via Homebrew). ARM64 has no legacy BIOS boot path."
}

variable "output_directory" {
  type    = string
  default = "infra/local/build/images/attacker01"
}

source "qemu" "kali_attacker" {
  iso_url          = var.iso_url
  iso_checksum     = var.iso_checksum
  output_directory = var.output_directory
  vm_name          = "attacker01.qcow2"
  format           = "qcow2"

  qemu_binary  = "qemu-system-aarch64"
  accelerator  = "hvf" # native arm64 guest on Apple Silicon host
  machine_type = "virt"
  firmware     = var.firmware
  cpu_model    = "host"

  cpus      = 2
  memory    = 4096
  disk_size = "40000M"

  net_device     = "virtio-net"
  disk_interface = "virtio"

  headless = true

  http_directory = "${path.root}/http-linux"

  boot_command = [
    "<esc><wait>",
    "install auto=true priority=critical ",
    "url=http://{{ .HTTPIP }}:{{ .HTTPPort }}/preseed.cfg ",
    "hostname=attacker01 domain=eadadl.lab ",
    "<enter>"
  ]
  boot_wait = "5s"

  communicator = "ssh"
  ssh_username = var.admin_username
  ssh_password = null
  # Private key path is written by infra/local/generate_bundles.py before
  # this build runs — see infra/local/README (Prerequisites section of the
  # root README.md links here). Packer needs the matching private key on
  # disk to complete the build's SSH-based provisioning step.
  ssh_private_key_file = "infra/local/build/ssh/lab_ed25519"
  ssh_timeout          = "1h"

  shutdown_command = "sudo -S shutdown -P now"
}

build {
  sources = ["source.qemu.kali_attacker"]

  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get install -y qemu-guest-agent",
      "sudo systemctl enable qemu-guest-agent"
    ]
  }
}
