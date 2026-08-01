#!/usr/bin/env bash
# infra/local/build-linux.sh
#
# Wrapper around `packer build` for the two native-ARM64 Linux images
# (attacker01 via Kali preseed, siem01 via Ubuntu cloud-init). Generates the
# shared lab SSH keypair once (both hosts use the same operator key — this
# is a single-operator lab, see docs/adr/0001-deploy-target.md), publishes
# the public half to whichever host's provisioning mechanism needs it, and
# invokes the matching Packer template.
#
# Usage: infra/local/build-linux.sh <attacker01|siem01>
#
# Requires packer + qemu on PATH; see README.md Prerequisites.

set -euo pipefail

VM_NAME="${1:?Usage: infra/local/build-linux.sh <attacker01|siem01>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_DIR="$SCRIPT_DIR/build/ssh"
KEY_PATH="$SSH_DIR/lab_ed25519"
HTTP_LINUX_DIR="$SCRIPT_DIR/packer/http-linux"

mkdir -p "$SSH_DIR"
if [ ! -f "$KEY_PATH" ]; then
  ssh-keygen -t ed25519 -N "" -C "eadadl-lab" -f "$KEY_PATH"
  chmod 600 "$KEY_PATH"
fi
PUBLIC_KEY="$(cat "${KEY_PATH}.pub")"

# Both .pkr.hcl files' efi_firmware_code/efi_firmware_vars variables
# default to a hardcoded /opt/homebrew/... path, since that's where
# Homebrew installs QEMU's UEFI firmware alongside the qemu-system-*
# binaries. That default breaks for any non-Homebrew QEMU install (e.g. a
# from-source build in a custom prefix — see BUILD_LOG.md session 4).
# Derive both instead from wherever qemu-system-aarch64 actually resolves
# on PATH, which generalizes to both.
QEMU_BIN="$(command -v qemu-system-aarch64)" || {
  echo "qemu-system-aarch64 not found on PATH" >&2
  exit 1
}
QEMU_PREFIX="$(cd "$(dirname "$QEMU_BIN")/.." && pwd)"
EFI_CODE="$QEMU_PREFIX/share/qemu/edk2-aarch64-code.fd"
EFI_VARS="$QEMU_PREFIX/share/qemu/edk2-arm-vars.fd"
[ -f "$EFI_CODE" ] || {
  echo "Expected UEFI CODE firmware at $EFI_CODE (derived from qemu-system-aarch64's location) but it's not there." >&2
  exit 1
}
[ -f "$EFI_VARS" ] || {
  echo "Expected UEFI VARS template at $EFI_VARS (derived from qemu-system-aarch64's location) but it's not there." >&2
  exit 1
}

case "$VM_NAME" in
  attacker01)
    # kali-attacker.pkr.hcl's preseed.cfg late_command fetches
    # authorized_keys from Packer's own ephemeral HTTP server — see that
    # file's comments for why it's resolved from the installer's boot
    # cmdline rather than hardcoded.
    printf '%s\n' "$PUBLIC_KEY" > "$HTTP_LINUX_DIR/authorized_keys"

    : "${KALI_ISO_URL:?Set KALI_ISO_URL — see kali-attacker.pkr.hcl variable description}"
    : "${KALI_ISO_CHECKSUM:?Set KALI_ISO_CHECKSUM (sha256:<hash>)}"

    packer init "$SCRIPT_DIR/packer/kali-attacker.pkr.hcl"
    packer build \
      -var "iso_url=${KALI_ISO_URL}" \
      -var "iso_checksum=${KALI_ISO_CHECKSUM}" \
      -var "admin_ssh_public_key=${PUBLIC_KEY}" \
      -var "efi_firmware_code=${EFI_CODE}" \
      -var "efi_firmware_vars=${EFI_VARS}" \
      "$SCRIPT_DIR/packer/kali-attacker.pkr.hcl"
    ;;

  siem01)
    RENDERED="$HTTP_LINUX_DIR/user-data"
    trap 'rm -f "$RENDERED"' EXIT
    # cloud-init's SSH key needs literal newline-free embedding; escape any
    # '&' or '\' before sed substitution to avoid corrupting the key.
    ESCAPED_KEY="$(printf '%s' "$PUBLIC_KEY" | sed -e 's/[&\\]/\\&/g')"
    sed "s|__SSH_PUBLIC_KEY__|${ESCAPED_KEY}|" \
      "$HTTP_LINUX_DIR/user-data.tmpl" > "$RENDERED"

    : "${UBUNTU_IMG_CHECKSUM:?Set UBUNTU_IMG_CHECKSUM (sha256:<hash>) — see ubuntu-siem.pkr.hcl variable description}"

    packer init "$SCRIPT_DIR/packer/ubuntu-siem.pkr.hcl"
    packer build \
      -var "base_image_checksum=${UBUNTU_IMG_CHECKSUM}" \
      -var "efi_firmware_code=${EFI_CODE}" \
      -var "efi_firmware_vars=${EFI_VARS}" \
      "$SCRIPT_DIR/packer/ubuntu-siem.pkr.hcl"
    ;;

  *)
    echo "Unknown VM '$VM_NAME' — expected attacker01 or siem01" >&2
    exit 1
    ;;
esac
