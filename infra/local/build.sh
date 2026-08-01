#!/usr/bin/env bash
# infra/local/build.sh
#
# Thin wrapper around `packer build` for the two Windows images (dc01,
# mem01). Exists because Autounattend.xml's AdministratorPassword can't be
# templated by Packer's cd_files directly (those are copied verbatim onto
# the boot ISO) — this script renders a per-build copy with the real
# password substituted in, then cleans it up afterward so the plaintext
# password never lingers on disk longer than the build itself.
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
RENDERED_XML="$HTTP_WIN_DIR/.Autounattend.rendered.xml"

: "${ADMIN_PASSWORD:?Set ADMIN_PASSWORD (see .env.example LAB_ADMIN_PASSWORD)}"
: "${WIN_ISO_URL:?Set WIN_ISO_URL to your Windows Server 2022 evaluation ISO}"
: "${WIN_ISO_CHECKSUM:?Set WIN_ISO_CHECKSUM (sha256:<hash>) for WIN_ISO_URL}"

cleanup() { rm -f "$RENDERED_XML"; }
trap cleanup EXIT

sed "s|__ADMIN_PASSWORD__|${ADMIN_PASSWORD}|g" \
  "$HTTP_WIN_DIR/Autounattend.xml" > "$RENDERED_XML"

# Packer's cd_files list in windows-server.pkr.hcl points at
# Autounattend.xml literally, so swap the rendered copy in for the build
# and restore the placeholder version after (keeps the tracked file free of
# secrets even transiently).
cp "$HTTP_WIN_DIR/Autounattend.xml" "$HTTP_WIN_DIR/.Autounattend.orig.xml"
cp "$RENDERED_XML" "$HTTP_WIN_DIR/Autounattend.xml"
trap 'mv "$HTTP_WIN_DIR/.Autounattend.orig.xml" "$HTTP_WIN_DIR/Autounattend.xml"; cleanup' EXIT

packer init "$SCRIPT_DIR/packer/windows-server.pkr.hcl"
packer build \
  -var "vm_name=${VM_NAME}" \
  -var "iso_url=${WIN_ISO_URL}" \
  -var "iso_checksum=${WIN_ISO_CHECKSUM}" \
  -var "admin_password=${ADMIN_PASSWORD}" \
  "$SCRIPT_DIR/packer/windows-server.pkr.hcl"
