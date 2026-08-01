#!/usr/bin/env python3
"""Ansible dynamic inventory sourced from inventory/lab-scope.yaml.

This is deliberate: lab-scope.yaml is the scope guard's single source of
truth (docs/adr/0002-scope-guard.md) for attack automation, and Ansible
provisioning should be constrained the same way — there is no separate,
independently-maintained Ansible inventory that could drift from what the
scope guard considers authorized. Only hosts with provisioned: true and a
non-null ip are emitted; everything else is (correctly) invisible to
Ansible, the same way it's invisible to the attack engine.

Implements the two-script-mode dynamic inventory contract: `--list` (used
by ansible-playbook) and `--host <name>` (required by the spec, unused here
since --list already returns full hostvars via _meta).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCOPE_FILE = REPO_ROOT / "inventory" / "lab-scope.yaml"

WINDOWS_ROLES = {"domain_controller", "member_server", "workstation"}


def build_inventory() -> dict:
    scope = yaml.safe_load(SCOPE_FILE.read_text())

    groups: dict[str, list[str]] = {
        "windows": [],
        "linux": [],
        "domain_controller": [],
        "member_server": [],
        "attacker": [],
        "siem": [],
    }
    hostvars: dict[str, dict] = {}

    for host in scope["hosts"]:
        if not host.get("provisioned") or not host.get("ip"):
            continue

        host_id = host["id"]
        role = host["role"]
        groups.setdefault(role, []).append(host_id)

        vars_: dict = {
            "ansible_host": host["ip"],
            "lab_role": role,
            "lab_hostname": host["hostname"],
        }

        if role in WINDOWS_ROLES:
            groups["windows"].append(host_id)
            vars_.update(
                {
                    "ansible_connection": "winrm",
                    "ansible_winrm_transport": "basic",
                    "ansible_winrm_server_cert_validation": "ignore",
                    "ansible_port": 5985,
                    "ansible_user": "{{ lab_admin_username }}",
                    "ansible_password": "{{ lab_admin_password }}",
                }
            )
        else:
            groups["linux"].append(host_id)
            vars_.update(
                {
                    "ansible_connection": "ssh",
                    "ansible_user": "{{ lab_admin_username }}",
                    "ansible_ssh_private_key_file": "infra/local/build/ssh/lab_ed25519",
                    "ansible_become": True,
                    "ansible_become_method": "sudo",
                }
            )

        hostvars[host_id] = vars_

    inventory = {
        group: {"hosts": members} for group, members in groups.items() if members
    }
    inventory["_meta"] = {"hostvars": hostvars}
    inventory["all"] = {"children": [g for g in groups if groups[g]]}
    return inventory


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--host")
    args = parser.parse_args()

    if not SCOPE_FILE.exists():
        print(f"ERROR: {SCOPE_FILE} not found", file=sys.stderr)
        sys.exit(1)

    if args.list:
        print(json.dumps(build_inventory()))
    else:
        print(json.dumps({}))


if __name__ == "__main__":
    main()
