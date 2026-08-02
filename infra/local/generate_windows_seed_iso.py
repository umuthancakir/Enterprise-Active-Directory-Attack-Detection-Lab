#!/usr/bin/env python3
"""Build a clean answer-file seed ISO for windows-server.pkr.hcl.

See iso_builder.py's module docstring for why this exists (Packer's own
cd_files/cd_label is broken on macOS) rather than using Packer's built-in
mechanism — for this build specifically, `D:\\bootstrap.ps1` (delivered
this way, run via Autounattend.xml's FirstLogonCommands to enable WinRM)
never actually ran, leaving WinRM stuck offering only Negotiate auth
forever, no matter how long a real build was left running — observed
directly by probing the WinRM endpoint's WWW-Authenticate header on a
real build. See BUILD_LOG.md session 4.

Usage: generate_windows_seed_iso.py <Autounattend.xml> <bootstrap.ps1> <output.iso>
"""

from __future__ import annotations

import sys
from pathlib import Path

from iso_builder import build_iso


def build_windows_seed_iso(autounattend_path: str, bootstrap_path: str, output_path: str) -> None:
    build_iso(
        {"Autounattend.xml": Path(autounattend_path), "bootstrap.ps1": Path(bootstrap_path)},
        volume_id="cidata",
        output_path=Path(output_path),
    )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} <Autounattend.xml> <bootstrap.ps1> <output.iso>",
            file=sys.stderr,
        )
        sys.exit(1)
    build_windows_seed_iso(sys.argv[1], sys.argv[2], sys.argv[3])
