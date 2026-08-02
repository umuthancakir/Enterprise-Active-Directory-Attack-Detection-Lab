#!/usr/bin/env bash
# infra/local/build.sh
#
# Thin wrapper around `packer build` for the two Windows images (dc01,
# mem01). Exists because Autounattend.xml's AdministratorPassword needs the
# real password substituted in before it reaches the guest, and because
# Packer's own cd_files/cd_label mechanism for delivering it (and
# bootstrap.ps1) is broken on macOS — see
# infra/local/generate_windows_seed_iso.py's docstring. This script renders
# the password into infra/local/build/ (gitignored), builds a clean seed
# ISO from that + bootstrap.ps1, and passes both to packer via -var.
#
# This used to swap the rendered copy IN PLACE over the tracked
# Autounattend.xml and restore the placeholder via a bash EXIT trap once
# the build finished. That trap depends on this script actually exiting
# normally — killing the underlying qemu/packer process directly instead
# (e.g. while debugging a stuck build) skips it entirely, leaving a real
# plaintext password sitting in a tracked file indefinitely. That's
# exactly what happened once this session: a real password got committed
# and pushed before it was caught (see BUILD_LOG.md session 4). Rendering
# to a gitignored path instead makes that failure mode structurally
# impossible rather than just unlikely — there's no tracked file to leave
# in a bad state no matter how the build gets interrupted.
#
# Usage: infra/local/build.sh <dc01|mem01>
#
# Requires ADMIN_PASSWORD, WIN_ISO_URL, WIN_ISO_CHECKSUM in the environment
# (source .env first — see .env.example). Requires packer + qemu on PATH;
# see README.md Prerequisites.

set -euo pipefail

VM_NAME="${1:?Usage: infra/local/build.sh <dc01|mem01>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTTP_WIN_DIR="$SCRIPT_DIR/packer/http-windows"
# Filenames must be exactly Autounattend.xml/bootstrap.ps1 — Windows Setup
# and D:\bootstrap.ps1 (run via FirstLogonCommands) both look for these
# exact names at the seed disc's root.
RENDERED_DIR="$SCRIPT_DIR/build/http-windows-rendered"
RENDERED_XML="$RENDERED_DIR/Autounattend.xml"
SEED_ISO="$SCRIPT_DIR/build/dc-mem-seed.iso"

: "${ADMIN_PASSWORD:?Set ADMIN_PASSWORD (see .env.example LAB_ADMIN_PASSWORD)}"
: "${WIN_ISO_URL:?Set WIN_ISO_URL to your Windows Server 2022 evaluation ISO}"
: "${WIN_ISO_CHECKSUM:?Set WIN_ISO_CHECKSUM (sha256:<hash>) for WIN_ISO_URL}"

mkdir -p "$RENDERED_DIR"
trap 'rm -f "$RENDERED_XML" "$SEED_ISO"' EXIT

sed "s|__ADMIN_PASSWORD__|${ADMIN_PASSWORD}|g" \
  "$HTTP_WIN_DIR/Autounattend.xml" > "$RENDERED_XML"

# NOT Packer's own cd_files/cd_label — see
# infra/local/generate_windows_seed_iso.py's docstring for why.
python3 "$SCRIPT_DIR/generate_windows_seed_iso.py" \
  "$RENDERED_XML" "$HTTP_WIN_DIR/bootstrap.ps1" "$SEED_ISO"

packer init "$SCRIPT_DIR/packer/windows-server.pkr.hcl"
packer build \
  -var "vm_name=${VM_NAME}" \
  -var "iso_url=${WIN_ISO_URL}" \
  -var "iso_checksum=${WIN_ISO_CHECKSUM}" \
  -var "admin_password=${ADMIN_PASSWORD}" \
  -var "rendered_autounattend=${RENDERED_XML}" \
  -var "seed_iso=${SEED_ISO}" \
  "$SCRIPT_DIR/packer/windows-server.pkr.hcl"
