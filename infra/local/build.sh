#!/usr/bin/env bash
# infra/local/build.sh
#
# Thin wrapper around `packer build` for the two Windows images (dc01,
# mem01). Exists because Autounattend.xml's AdministratorPassword can't be
# templated by Packer's cd_files directly (those are copied verbatim onto
# the boot ISO) — this script renders a copy with the real password
# substituted in in infra/local/build/ (gitignored) and passes that to
# packer via -var rendered_autounattend.
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
# Filename must be exactly Autounattend.xml — cd_files publishes each
# path's basename verbatim onto the boot ISO, and Windows Setup only
# looks for that exact name at removable media's root.
RENDERED_DIR="$SCRIPT_DIR/build/http-windows-rendered"
RENDERED_XML="$RENDERED_DIR/Autounattend.xml"

: "${ADMIN_PASSWORD:?Set ADMIN_PASSWORD (see .env.example LAB_ADMIN_PASSWORD)}"
: "${WIN_ISO_URL:?Set WIN_ISO_URL to your Windows Server 2022 evaluation ISO}"
: "${WIN_ISO_CHECKSUM:?Set WIN_ISO_CHECKSUM (sha256:<hash>) for WIN_ISO_URL}"

mkdir -p "$RENDERED_DIR"
trap 'rm -f "$RENDERED_XML"' EXIT

sed "s|__ADMIN_PASSWORD__|${ADMIN_PASSWORD}|g" \
  "$HTTP_WIN_DIR/Autounattend.xml" > "$RENDERED_XML"

packer init "$SCRIPT_DIR/packer/windows-server.pkr.hcl"
packer build \
  -var "vm_name=${VM_NAME}" \
  -var "iso_url=${WIN_ISO_URL}" \
  -var "iso_checksum=${WIN_ISO_CHECKSUM}" \
  -var "admin_password=${ADMIN_PASSWORD}" \
  -var "rendered_autounattend=${RENDERED_XML}" \
  "$SCRIPT_DIR/packer/windows-server.pkr.hcl"
