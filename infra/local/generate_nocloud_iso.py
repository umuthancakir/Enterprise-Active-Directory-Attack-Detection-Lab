#!/usr/bin/env python3
"""Build a clean NoCloud (cidata) seed ISO for ubuntu-siem.pkr.hcl.

Exists because Packer's own `cd_files`/`cd_label` mechanism is broken on
macOS: its SDK unconditionally shells out to `hdiutil makehybrid -hfs
-joliet -iso ...` (see packer-plugin-sdk's step_create_cdrom.go), which
wraps the ISO9660 filesystem in an HFS+ hybrid layer. cloud-init's guest
kernel then sees the disk as a partitioned (Apple partition map) block
device rather than a plain ISO9660 volume and never finds the NoCloud
seed at all — confirmed on a real build via the guest's serial console:
"Datasource DataSourceNone... Used fallback datasource", no SSH key ever
installed. This is a known, still-open upstream bug — see
https://github.com/hashicorp/packer-plugin-qemu/issues/133. Packer's SDK
would prefer `xorriso` or `mkisofs` over `hdiutil` if either were on
PATH (both avoid the bug), but neither has a non-Homebrew install path
on this machine (see BUILD_LOG.md session 4 for the same investigation
pattern already applied to Packer/QEMU/gh themselves). pycdlib (pure
Python, pip --user installable) sidesteps the problem entirely by
writing ISO9660+Joliet+Rock Ridge directly, with no HFS+ layer.

Usage: generate_nocloud_iso.py <user-data> <meta-data> <output.iso>
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pycdlib


def build_nocloud_iso(user_data_path: str, meta_data_path: str, output_path: str) -> None:
    user_data = Path(user_data_path).read_bytes()
    meta_data = Path(meta_data_path).read_bytes()

    iso = pycdlib.PyCdlib()
    # Rock Ridge is required for the lowercase, non-8.3 filenames
    # ("user-data", "meta-data") cloud-init's NoCloud datasource looks
    # for by exact name — plain ISO9660 alone only offers uppercase
    # 8.3-truncated names (USERDATA.;1) that it won't recognize.
    iso.new(interchange_level=3, joliet=3, rock_ridge="1.09", vol_ident="cidata")
    iso.add_fp(
        io.BytesIO(user_data),
        len(user_data),
        "/USERDATA.;1",
        joliet_path="/user-data",
        rr_name="user-data",
    )
    iso.add_fp(
        io.BytesIO(meta_data),
        len(meta_data),
        "/METADATA.;1",
        joliet_path="/meta-data",
        rr_name="meta-data",
    )
    iso.write(output_path)
    iso.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <user-data> <meta-data> <output.iso>", file=sys.stderr)
        sys.exit(1)
    build_nocloud_iso(sys.argv[1], sys.argv[2], sys.argv[3])
