"""Shared helper: build a clean ISO9660+Joliet+Rock Ridge image with pycdlib.

Exists because Packer's own `cd_files`/`cd_label` mechanism is broken on
macOS: its SDK unconditionally shells out to `hdiutil makehybrid -hfs
-joliet -iso ...` (see packer-plugin-sdk's step_create_cdrom.go), which
wraps the ISO9660 filesystem in an HFS+ hybrid layer. Two real,
independent failures traced back to this on this project:

  - siem01 (Ubuntu/cloud-init): the guest kernel saw the disk as a
    partitioned (Apple partition map) block device rather than a plain
    ISO9660 volume, and cloud-init's NoCloud datasource never found the
    seed at all ("Datasource DataSourceNone").
  - dc01 (Windows Server): WinRM stayed Negotiate-only forever —
    `D:\\bootstrap.ps1` (delivered the same way, via cd_files) never ran,
    consistent with Windows' normal-runtime CDFS driver (used once fully
    booted, for FirstLogonCommands) not reading the same hybrid image
    cleanly, even though the WinPE-era Autounattend.xml discovery (a
    different, earlier code path) tolerated it fine.

This is a known, still-open upstream bug —
https://github.com/hashicorp/packer-plugin-qemu/issues/133. Packer's SDK
would prefer `xorriso` or `mkisofs` over `hdiutil` if either were on
PATH (both avoid the bug), but neither has a non-Homebrew install path on
this machine and conda-forge doesn't package them for osx-arm64 either
(checked). pycdlib (pure Python, pip --user installable) sidesteps the
problem entirely by writing ISO9660+Joliet+Rock Ridge directly, with no
HFS+ layer.

Used by infra/local/generate_nocloud_iso.py (siem01) and
infra/local/generate_windows_seed_iso.py (dc01/mem01) in place of Packer's
cd_files/cd_label for exactly the files each build needs read back at
runtime (not the primary install/boot media, which macOS's ISO9660
handling reads fine either way — only cd_files-generated discs hit this).
"""

from __future__ import annotations

import io
from pathlib import Path

import pycdlib


def build_iso(files: dict[str, Path], volume_id: str, output_path: Path) -> None:
    """Write an ISO9660+Joliet+Rock Ridge image containing `files` at its root.

    `files` maps the exact filename each guest-side reader expects
    (e.g. "user-data", "Autounattend.xml") to the local path of its
    real content. Rock Ridge is what makes that exact, non-8.3,
    mixed-case name show up correctly — plain ISO9660 alone only offers
    uppercase 8.3-truncated names.
    """
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, rock_ridge="1.09", vol_ident=volume_id)
    for name, path in files.items():
        data = path.read_bytes()
        # ISO9660 Level 3 "8.3" identifier is only ever used as a
        # same-length-or-shorter fallback; Joliet/Rock Ridge carry the
        # real name. It just needs to be unique and validly formatted
        # (D1 charset only: A-Z, 0-9, _ — no '.', '-', etc), not
        # meaningful.
        safe = "".join(c if c.isalnum() else "_" for c in name.upper())
        iso_name = f"/{safe[:8]}.;1"
        iso.add_fp(io.BytesIO(data), len(data), iso_name, joliet_path=f"/{name}", rr_name=name)
    iso.write(str(output_path))
    iso.close()
