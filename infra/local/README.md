# infra/local — UTM/QEMU deploy target

See [docs/adr/0004-revert-to-local-utm.md](../../docs/adr/0004-revert-to-local-utm.md)
and [docs/adr/0005-local-network-isolation.md](../../docs/adr/0005-local-network-isolation.md)
for why this exists and how isolation is enforced. This file is the
practical "how to actually run it" companion to those ADRs.

## One-time setup

### 1. Tooling (requires admin/sudo — see root README.md Prerequisites)

```bash
brew install packer qemu ansible
```

UTM.app itself (already installed on this machine) provides the VM
runtime; Packer + QEMU build the disk images UTM's VMs boot from.

### 2. Blank UTM bundle templates

UTM has no CLI to create a VM from a spec — `generate_bundles.py` mutates a
handful of known keys in an existing bundle's `config.plist` rather than
authoring the format from scratch (see that script's docstring for why).
Create the two blank templates it needs, once, via the UTM GUI:

1. Open UTM → **File → New**.
2. **Virtualize** (native, for the arm64 template) or **Emulate** (for the
   x86_64 template, since this is an Apple Silicon host — accept the "this
   will be slow" warning, that's expected, see ADR 0004).
3. Architecture: `ARM64` for one template, `x86_64` for the other. Give
   each 2 CPU / 4096 MB (matches `hosts.yaml` — `generate_bundles.py`
   overwrites these anyway, but starting close avoids surprises if you
   inspect the template directly).
4. Skip attaching an ISO or disk image — leave it as empty/minimal as UTM
   allows. `generate_bundles.py` replaces the drive entry.
5. Don't boot it. Save, then quit UTM.
6. Find the resulting bundle under
   `~/Library/Containers/com.utmapp.UTM/Data/Documents/*.utm` and copy it to:
   - `infra/local/templates/arm64-blank.utm`
   - `infra/local/templates/x86_64-blank.utm`

(`infra/local/templates/` is gitignored — these are machine-specific binary
bundles, not something to commit.)

### 3. Verify the plist key names this project assumes

`generate_bundles.py` was written without a real UTM install to test
against (see BUILD_LOG.md) — its key names (`Information.Name`,
`System.CPUCount`, `Drive[0].ImagePath`, `Network[0].Mode`, etc.) are
best-effort. Before relying on it:

```bash
plutil -p infra/local/templates/arm64-blank.utm/config.plist
```

and diff what you see against the keys the script writes. Adjust
`generate_bundles.py` to match reality if they differ.

## Build → generate → boot → sync

```bash
source .env   # ADMIN_PASSWORD, WIN_ISO_URL, WIN_ISO_CHECKSUM, KALI_ISO_URL, KALI_ISO_CHECKSUM, UBUNTU_IMG_CHECKSUM

infra/local/build.sh dc01
infra/local/build.sh mem01
infra/local/build-linux.sh attacker01
infra/local/build-linux.sh siem01

python3 infra/local/generate_bundles.py

# Open UTM, start each of the 4 generated VMs (dc01, mem01, attacker01,
# siem01), wait for them to finish booting.

python3 scripts/sync_scope.py   # records DHCP-assigned IPs into inventory/lab-scope.yaml
```

`make up` (once wired to `DEPLOY_TARGET=local` in a future session — see
ROADMAP.md) will drive this sequence end-to-end instead of running each
script by hand.

## Teardown

Delete each `.utm` bundle from UTM's VM library (or `rm -rf` the bundle
directories UTM reported in `generate_bundles.py`'s output / `state.json`),
then remove `infra/local/build/` to reclaim the built qcow2 images. This is
the local equivalent of `terraform destroy` — see SECURITY.md #4
(ephemeral).
