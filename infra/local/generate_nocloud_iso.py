#!/usr/bin/env python3
"""Build a clean NoCloud (cidata) seed ISO for ubuntu-siem.pkr.hcl.

See iso_builder.py's module docstring for why this exists (Packer's own
cd_files/cd_label is broken on macOS) rather than using Packer's built-in
mechanism.

Usage: generate_nocloud_iso.py <user-data> <meta-data> <output.iso>
"""

from __future__ import annotations

import sys
from pathlib import Path

from iso_builder import build_iso


def build_nocloud_iso(user_data_path: str, meta_data_path: str, output_path: str) -> None:
    build_iso(
        {"user-data": Path(user_data_path), "meta-data": Path(meta_data_path)},
        volume_id="cidata",
        output_path=Path(output_path),
    )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <user-data> <meta-data> <output.iso>", file=sys.stderr)
        sys.exit(1)
    build_nocloud_iso(sys.argv[1], sys.argv[2], sys.argv[3])
