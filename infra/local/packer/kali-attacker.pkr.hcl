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

variable "efi_firmware_code" {
  type        = string
  default     = "/opt/homebrew/share/qemu/edk2-aarch64-code.fd"
  description = "UEFI CODE firmware for qemu-system-aarch64 (installed alongside qemu, at <qemu prefix>/share/qemu/edk2-aarch64-code.fd — /opt/homebrew for a Homebrew install). infra/local/build-linux.sh derives and overrides this from wherever qemu-system-aarch64 actually resolves on PATH. Uses Packer's efi_boot mechanism (-drive if=pflash), not the legacy `firmware` field (-bios) — the latter forces Packer to inject `-boot once=d`, which QEMU's aarch64 virt machine genuinely does not support ('no function defined to set boot device list for this architecture', see BUILD_LOG.md session 4). ARM64 has no legacy BIOS boot path."
}

variable "efi_firmware_vars" {
  type        = string
  default     = "/opt/homebrew/share/qemu/edk2-arm-vars.fd"
  description = "UEFI VARS template pairing efi_firmware_code — note this is edk2-arm-vars.fd (not edk2-aarch64-vars.fd, which QEMU does not ship; the ARM vars template is shared across 32-bit ARM and aarch64)."
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

  qemu_binary       = "qemu-system-aarch64"
  accelerator       = "hvf" # native arm64 guest on Apple Silicon host
  machine_type      = "virt"
  efi_firmware_code = var.efi_firmware_code
  efi_firmware_vars = var.efi_firmware_vars
  cpu_model         = "host"

  cpus      = 2
  memory    = 4096
  disk_size = "40000M"

  net_device     = "virtio-net"
  disk_interface = "virtio"

  headless = true

  # QEMU's aarch64 "virt" machine has NO default GPU or input controller
  # (unlike "pc", which wires up a VGA-compatible display and a PS/2
  # keyboard automatically) — without these, VNC has no guest framebuffer
  # to show and no guest input device to deliver keystrokes to, so
  # boot_command's keypresses go nowhere (observed: they got swallowed by
  # QEMU's own monitor instead — see BUILD_LOG.md session 4). virtio-gpu
  # gives VNC something to render; the USB keyboard/tablet (behind an XHCI
  # controller, since "virt" has no built-in USB host controller either)
  # gives it something to type into.
  qemuargs = [
    ["-device", "virtio-gpu-pci"],
    ["-device", "qemu-xhci"],
    ["-device", "usb-kbd"],
    ["-device", "usb-tablet"],
  ]

  # Kali's arm64 netinst boots via GRUB (not an ISOLINUX-style "boot:"
  # prompt — aarch64 has no legacy BIOS boot path, see the efi_firmware_code
  # variable above), so the installer boot params can't be typed directly
  # at a prompt. Instead: 'e' opens GRUB's edit view on the highlighted
  # "Install" entry, <down><down> moves from the "setparams" line to the
  # "linux ..." line, <end> reaches the end of that (visually wrapped but
  # logically single) line, then the params are appended directly to the
  # kernel command line and <f10> boots the edited entry (equivalent to
  # Ctrl-x — both are shown on GRUB's own edit-mode help text). Verified
  # interactively via VNC screenshots against this exact ISO before being
  # encoded here — see BUILD_LOG.md session 4.
  boot_command = [
    "<wait10>",
    "e",
    "<down><down><end>",
    " auto=true priority=critical url=http://{{ .HTTPIP }}:{{ .HTTPPort }}/preseed.cfg hostname=attacker01 domain=eadadl.lab",
    "<f10>"
  ]
  boot_wait = "10s"

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
