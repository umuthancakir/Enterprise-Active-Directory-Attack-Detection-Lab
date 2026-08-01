#!/usr/bin/env python3
"""Generate .utm VM bundles for the lab from infra/local/hosts.yaml.

UTM has no CLI or API to declaratively create a VM from a spec, and its
.utm bundle format (a directory containing config.plist + disk images) is
undocumented — see docs/adr/0004-revert-to-local-utm.md's "alternatives
considered" for why this rules out a Terraform-style approach here. Instead
of reverse-engineering the full plist schema, this script starts from a
"blank" .utm bundle the operator creates once via the UTM GUI (see
infra/local/README.md "One-time setup") and mutates only the handful of
keys this project understands: VM name, disk image path, CPU/memory, and
network mode. Everything else in the template is left untouched.

STATUS: written but not run-tested against a real UTM installation — this
machine's account lacks the admin rights needed to have UTM's CLI tooling
fully set up for scripted testing (see BUILD_LOG.md). The plist key names
below are best-effort based on UTM's publicly known QEMU-backend bundle
structure; verify against a real config.plist (e.g. `plutil -p config.plist`
on a GUI-created VM) before trusting this against real hardware.

Usage:
    python3 infra/local/generate_bundles.py [--vm-dir ~/path/to/utm/vms]

Requires: PyYAML.
"""

from __future__ import annotations

import argparse
import json
import plistlib
import shutil
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_DIR = REPO_ROOT / "infra" / "local"
HOSTS_FILE = LOCAL_DIR / "hosts.yaml"
STATE_FILE = LOCAL_DIR / "state.json"

# UTM's default VM library location on macOS. Bundles placed here are
# auto-discovered by the UTM app.
DEFAULT_UTM_VM_DIR = (
    Path.home()
    / "Library"
    / "Containers"
    / "com.utmapp.UTM"
    / "Data"
    / "Documents"
)


def load_hosts() -> dict:
    return yaml.safe_load(HOSTS_FILE.read_text())


def build_bundle(host: dict, network_iface: str, vm_dir: Path) -> Path:
    template = REPO_ROOT / host["template"]
    image = REPO_ROOT / host["image"]

    if not template.exists():
        print(
            f"ERROR: template bundle {template} not found. Create it once "
            f"via the UTM GUI — see infra/local/README.md 'One-time setup'.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not image.exists():
        print(
            f"ERROR: built image {image} not found. Run "
            f"infra/local/build.sh or build-linux.sh for '{host['id']}' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    dest = vm_dir / f"{host['id']}.utm"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(template, dest)

    config_path = dest / "config.plist"
    with open(config_path, "rb") as f:
        config = plistlib.load(f)

    # Best-effort key names — see module docstring's STATUS note.
    config.setdefault("Information", {})["Name"] = host["id"]
    config.setdefault("System", {})["CPUCount"] = host["cpus"]
    config["System"]["MemorySize"] = host["memory_mb"]

    drives = config.setdefault("Drive", [])
    if drives:
        drives[0]["ImagePath"] = str(image)
    else:
        drives.append(
            {
                "ImagePath": str(image),
                "ImageType": "Disk",
                "Interface": "virtio" if host["arch"] == "arm64" else "ide",
            }
        )

    networks = config.setdefault("Network", [])
    if networks:
        networks[0]["Mode"] = "Host"
        networks[0]["HostInterface"] = network_iface
    else:
        networks.append({"Mode": "Host", "HostInterface": network_iface})

    with open(config_path, "wb") as f:
        plistlib.dump(config, f)

    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vm-dir",
        type=Path,
        default=DEFAULT_UTM_VM_DIR,
        help="UTM VM library directory (default: UTM's standard macOS location)",
    )
    args = parser.parse_args()

    args.vm_dir.mkdir(parents=True, exist_ok=True)

    spec = load_hosts()
    network_iface = spec["network"]["utm_host_only_interface"]

    state = {"hosts": {}}
    for host in spec["hosts"]:
        bundle = build_bundle(host, network_iface, args.vm_dir)
        state["hosts"][host["id"]] = {
            "bundle_path": str(bundle),
            "role": host["role"],
            "ip": None,  # populated by scripts/sync_scope.py after boot + DHCP lease lookup
            "provisioned": True,
        }
        print(f"Generated {bundle}")

    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"Wrote {STATE_FILE}. Start each VM in UTM, then run:")
    print("  python3 scripts/sync_scope.py")
    print(
        "to record DHCP-assigned IPs into inventory/lab-scope.yaml once the "
        "hosts have booted."
    )


if __name__ == "__main__":
    main()
