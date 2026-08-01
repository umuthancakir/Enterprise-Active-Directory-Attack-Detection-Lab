# Build Log

Session-by-session record of what was actually done. Radical honesty: this
log records real actions taken, not intended future work (that's
[ROADMAP.md](ROADMAP.md)).

## 2026-08-01 — Session 1: Phase 0 scaffold

**Environment discovered:**

- Host: Apple Silicon (arm64) macOS, empty non-git directory.
- Installed: VirtualBox (`VBoxManage`), UTM.app. Not installed: Vagrant,
  Terraform, Ansible, Packer, Docker, Homebrew, Azure CLI.
- This account does **not** have sudo/admin rights on the machine — the
  Homebrew installer failed with "Need sudo access... needs to be an
  Administrator". Tooling install is deferred until an admin runs it; this
  does not block scaffolding code, only running `terraform apply` /
  `az login` locally later.

**Decisions made (with operator):**

- `DEPLOY_TARGET=azure` — chosen over local UTM/QEMU emulation or native
  ARM64 Windows Server, because VirtualBox doesn't reliably support Windows
  guests on arm64 hosts and Microsoft doesn't publish ARM64 Windows Server
  media through normal public channels. See
  [`docs/adr/0001-deploy-target.md`](docs/adr/0001-deploy-target.md).
- Azure auth: interactive `az login`, not a stored service-principal secret,
  for this single-operator stage.
- Operator asked to skip live Azure provisioning for now: scaffold all
  `infra/` Terraform and document the exact subscription/region/auth steps
  needed, but do not run `terraform apply` or require credentials yet.

**Work done:**

- git repo initialized (`main` branch).
- Directory scaffold created: `inventory/`, `infra/azure/`, `config/{dc,
  member,workstation,attacker,siem}/`, `telemetry/{sysmon,wef}/`,
  `attack/{techniques,chains,lib}/`, `detections/{sigma,tests}/`,
  `platform/{backend,frontend}/`, `ir/{playbooks,notebooks,automation}/`,
  `docs/adr/`, `.github/workflows/`.
- Governance docs written: `README.md`, `SECURITY.md`, `LICENSE` (MIT),
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`.
- `ROADMAP.md` and this `BUILD_LOG.md` created.

**Status:** Phase 0 in progress — scope guard, `.env.example`, Makefile, ADRs,
and CI skeleton not yet committed (in progress this same session, see
ROADMAP.md for current state).

**Not done / explicitly deferred:**

- No infrastructure has been provisioned. No Azure resources exist yet.
- No tests have been run (none exist yet).
- Homebrew/Terraform/Ansible/Packer/Azure CLI are not installed on this
  machine; an admin needs to run the installer before `make up` can actually
  execute against Azure.

## 2026-08-01 — Session 1 continued: Phase 1 Terraform scaffold

**Work done (per operator instruction: code only, no `terraform apply`, no
credentials required yet):**

- ADR 0003 written: defines the Azure network isolation model — no lab VM
  gets a public IP or an outbound route to the internet; Azure Bastion is
  the sole (inbound-only) management path; the mandatory Azure platform
  channel (168.63.129.16) is explicitly scoped out of the "no internet"
  invariant and documented as such so it isn't mistaken for a gap later.
- `infra/azure/` written: `versions.tf` (provider pins), `variables.tf`,
  `main.tf` (resource group + generated admin credential), `network.tf`
  (vnet, lab subnet, AzureBastionSubnet, NSG denying inbound/outbound
  Internet), `bastion.tf` (the only public IP in the deployment, locked to
  `var.operator_source_ips`), `dc.tf`/`member.tf`/`workstation.tf`
  (Windows Server 2022 / Windows 11 VMs), `attacker.tf` (Kali Linux
  marketplace image, SSH-key auth), `siem.tf` (Ubuntu 22.04, SSH-key auth),
  `outputs.tf`, `terraform.tfvars.example`.
- Linux hosts (attacker, SIEM) use `tls_private_key`-generated SSH keys
  rather than password auth — tightened this from an initial password-auth
  draft to match the project's least-privilege/secure-by-design standard.
- `scripts/sync_scope.py` written: reads `terraform output -json` and
  writes host IPs + provisioned state into `inventory/lab-scope.yaml`, the
  mechanism ADR 0002 depends on to keep the scope guard's allow-list from
  drifting from what's actually deployed.
- `docs/vulnerabilities.md` written as a **design document** — 8 planned
  deliberate misconfigurations mapped to ATT&CK technique IDs with
  reference links. None are implemented yet; that happens via the
  `config/dc/` and `config/member/` Ansible roles, which do not exist yet.

**Verification performed:** brace-balance check across all `.tf` files
(sanity only). **Not verified:** `terraform validate`/`terraform fmt` could
not be run — Terraform is not installed locally (see "Known blockers" in
ROADMAP.md). CI's `terraform-validate` job will be the first real validation
once this is pushed to GitHub.

**Not done / explicitly deferred:**

- No `terraform apply` has been run; no Azure resources exist.
- Domain promotion, OU/user/group creation, and all 8 deliberate
  misconfigurations in `docs/vulnerabilities.md` are unimplemented —
  `config/dc/`, `config/member/`, `config/workstation/` Ansible roles don't
  exist yet.
- NSG intra-lab rule (`allow-intra-lab` in `network.tf`) is a full mesh
  within the subnet rather than a scoped port matrix (AD/Kerberos/SMB/WinRM/
  SIEM-shipping ports specifically) — flagged as a Phase 1 hardening
  follow-up in ADR 0003, not yet done.

## 2026-08-01 — Session 1 continued: deploy target reverted to local UTM/QEMU

**Correction of a false premise:** the operator opened this segment
claiming Azure had errored (an AADSTS50058 error) and that a prior session
had already switched to UTM/QEMU. Verified before acting: `az` CLI was
still not on PATH, there was no credential error anywhere in this session's
actual history, and no UTM/QEMU files existed in the repo or git log. Flagged
this to the operator directly rather than acting on the false premise; the
operator then made an explicit, independent decision to switch to local
regardless (not because Azure had failed) — recorded as such in
[ADR 0004](docs/adr/0004-revert-to-local-utm.md) so this doesn't read as "we
hit a bug and worked around it" to a future reader.

**Work done (per operator instruction, still code-only — no packer/qemu
build has been run, this account still lacks the sudo access needed to
install them):**

- ADR 0004 (revert to local UTM/QEMU) and ADR 0005 (local network
  isolation model — UTM Host Only networking) written. ADR 0001 and ADR
  0003 marked superseded rather than deleted, so the Azure attempt stays
  in the record as a real, reasoned decision that was later reversed —
  not scrubbed from history.
- `infra/azure/` removed (`git rm -r`) — recoverable from git history at
  commit `67ce0f3`.
- `infra/local/` written: `packer/windows-server.pkr.hcl` (Windows Server
  2022, x86_64 TCG emulation, for `dc01`/`mem01`) with
  `http-windows/Autounattend.xml` + `bootstrap.ps1`; `packer/kali-attacker.pkr.hcl`
  (native arm64, Debian-installer preseed) with `http-linux/preseed.cfg`;
  `packer/ubuntu-siem.pkr.hcl` (native arm64, cloud-init/NoCloud) with
  `http-linux/user-data.tmpl` + `meta-data`; `build.sh` / `build-linux.sh`
  wrapper scripts (handle the password/SSH-key templating Packer's
  `cd_files` can't do on its own); `generate_bundles.py` (mutates a
  manually-created blank `.utm` template's `config.plist` via `plistlib`
  rather than authoring UTM's undocumented bundle format from scratch —
  see that script's docstring for why); `hosts.yaml` (4-host declarative
  list); `infra/local/README.md` (the honest "what's automated vs. manual"
  guide, including the one-time blank-template GUI step).
- Footprint trimmed from 5 to 4 hosts: `wks01` (workstation) dropped. Both
  `docs/vulnerabilities.md` (items 5 and 8, which depended on a 2nd non-DC
  Windows host) and the README architecture diagram updated to reflect
  this, with reintroducing `wks01` documented as an option rather than a
  silently dropped requirement.
- `scripts/sync_scope.py` rewritten: no more `terraform output`; reads
  `infra/local/state.json` (from `generate_bundles.py`) plus a
  **manually-maintained** `infra/local/discovered-ips.yaml` — UTM's
  host-only networking has no verified scriptable way to look up a guest's
  DHCP-assigned IP from the host side, so this was deliberately left
  manual rather than shipping an unverified auto-discovery mechanism.
- `Makefile`, `.env.example`, `README.md`, `.github/workflows/ci.yml`
  (`terraform-validate` → `packer-validate`), `CONTRIBUTING.md`,
  `inventory/lab-scope.yaml`, and ADR 0002 all updated to stop assuming a
  Terraform/Azure backend.

**Not done / explicitly deferred:**

- No Packer build has been run; no qcow2 images exist. This account still
  lacks sudo, so Homebrew (and therefore `packer`/`qemu`/`ansible`) still
  can't be installed locally — the local pivot removes the Azure
  credential/cost dependency, not this blocker (see ADR 0004
  Consequences).
- The one-time blank `.utm` template creation (manual, via UTM's GUI) has
  not been performed, and `generate_bundles.py`'s `config.plist` key
  assumptions are unverified against a real UTM bundle — see
  `infra/local/README.md` step 3.
- The Kali ARM64 installer preseed (`preseed.cfg`) is the least-proven
  artifact in this batch — Kali's ARM64 d-i preseed support is less
  commonly documented than Debian/Ubuntu's; flagged in ROADMAP.md rather
  than presented as equally solid to the Ubuntu cloud-init path.
- AD DS promotion, domain join, OU/user/group creation, and the 6
  (of 8, with 2 deferred) implementable misconfigurations remain
  unimplemented Ansible work — next up this session.

## 2026-08-01 — Session 1 continued: Ansible roles (config/dc, config/member)

**Work done (still code-only — no local `ansible` install, same sudo
blocker as Packer/QEMU; nothing here has run against a real host):**

- `config/ansible.cfg`, `config/requirements.yml` (ansible.windows,
  microsoft.ad, community.windows, ansible.posix collections),
  `config/inventory/lab_scope_inventory.py` (dynamic inventory sourced
  directly from `inventory/lab-scope.yaml` — deliberately the same file
  the scope guard reads, so Ansible can't provision a host the attack
  engine wouldn't be allowed to target, and vice versa), `config/group_vars/all.yml`
  (credentials from `.env`, never hardcoded).
- `config/dc/`: `tasks/promote_forest.yml` (AD DS + DNS feature install,
  `microsoft.ad.domain` forest promotion, DC points its own DNS at
  itself), `tasks/ou_structure.yml` + `tasks/users_and_groups.yml` (4 OUs,
  6 synthetic users, 2 groups — population for recon realism, not just the
  misconfig accounts), `tasks/misconfigs.yml` (implements
  `docs/vulnerabilities.md` items 1, 2, 4, 6, 7), `tasks/post_join_misconfigs.yml`
  (item 3 — unconstrained delegation on `mem01`, deliberately split out
  because it needs `mem01`'s AD computer object to exist first).
- `config/member/tasks/main.yml`: rename, point DNS at `dc01`
  (`hostvars['dc01']['ansible_host']`), `microsoft.ad.membership` domain
  join.
- `config/site.yml`: wires the ordering dependency explicitly — dc01 play,
  then mem01 play, then a third dc01 play for the post-join misconfig.
  Documented (in both the playbook and `post_join_misconfigs.yml`) that
  running roles individually with `--limit` skips real dependencies,
  rather than leaving that as a silent trap.
- `docs/vulnerabilities.md` updated: items 1/2/3/4/6/7 now say "Implemented
  ... — not run-tested" instead of "Planned", pointing at the specific
  task file each lives in.

**Verification performed:** YAML syntax check (`yaml.safe_load`) on every
new/changed file under `config/`, Jinja2 parse check on the SYSVOL script
template, a smoke-test import of `lab_scope_inventory.py`'s
`build_inventory()` against the current (unprovisioned) `lab-scope.yaml`
(returns an empty inventory, as expected — no host has `provisioned: true`
yet). **Not verified:** `ansible-lint`, and nothing has run against a real
Windows/WinRM target — there isn't one yet.

**Not done / explicitly deferred:**

- No Ansible run has happened; no domain exists.
- Misconfig 4's ACL-grant task uses inline PowerShell (`Get-Acl`/`Set-Acl`
  against the `AD:` PSProvider) rather than a dedicated Ansible module —
  flagged in ROADMAP.md as the piece most worth double-checking by hand,
  since it's hand-rolled idempotency logic (check for an existing matching
  ACE before adding) rather than a module's built-in state handling.
- Items 5 and 8 remain deferred pending `wks01` reintroduction (unchanged
  from the infra pivot).
- `config/attacker/` and `config/siem/` roles (installing offensive
  tooling and the Elastic/Wazuh stack, respectively) are still
  unwritten — Phase 2/3 work, not attempted this session.

## 2026-08-01 — Session 1 continued: real local test/lint tooling + scope guard

**User handed off a new continuation prompt** prioritizing work that's
implementable and CI-testable without a live lab (since Packer/QEMU/UTM
can't be provisioned here), starting with making the scope guard a real,
tested library.

**Capability discovery (changes the story for the rest of this build):**
this account can't run the Homebrew installer (no sudo), but `pip install
--user` needs no sudo at all and works fine. Installed `pytest`, `ruff`,
`mypy`, `types-PyYAML`, `ansible-core`, `ansible-lint`, and `certifi` (the
python.org framework build's default cert store couldn't verify
galaxy.ansible.com; fixed by pointing `SSL_CERT_FILE` at certifi's bundle)
this way. Also installed the `ansible.windows`, `microsoft.ad`,
`community.windows`, `ansible.posix` collections via `ansible-galaxy`. This
means the Python layer and all Ansible YAML can now be **actually run**
through real tooling, not just hand-reviewed — a meaningfully stronger
validation story than "written, not run-tested" for those two layers
specifically. It does not touch the Packer/QEMU/UTM blocker (those have no
pip install path).

**Immediately paid off:** ran `ansible-playbook --syntax-check` (passed
clean) and `ansible-lint config/` against last session's roles and found 6
real violations (all `name[template]`: Jinja templating in the middle of a
task name instead of at the end, plus one line-length overage) — fixed all
6 in `config/dc/tasks/misconfigs.yml`, re-ran, now clean at ansible-lint's
**production** profile (its strictest).

**Work done:**

- `pyproject.toml`: ruff/mypy/pytest config for the repo's shared Python
  (`attack/`, `scripts/`, `config/inventory/`); `mypy` strict mode.
- `attack/lib/scope_guard.py`: the shared chokepoint ADR 0002 describes —
  `ScopeGuard.resolve_target()` fail-closed on out-of-scope, non-attackable
  role, unprovisioned, or no-IP hosts; `ScopeFileError` for a malformed
  scope file (missing keys, wrong types, duplicate IDs, bad YAML). No
  override parameter anywhere.
- `tests/test_scope_guard.py`: 20 tests, hermetic (each writes its own
  `lab-scope.yaml` fixture into `tmp_path`), 15 of them negative cases.
  Includes a test that asserts via `inspect.signature()` that
  `resolve_target()` truly has no bypass parameter, not just "we didn't
  add one this time."
- Refactored `scripts/sync_scope.py` and
  `config/inventory/lab_scope_inventory.py` to split out pure functions
  (`merge_scope()`, `build_inventory()`) from their file I/O, specifically
  so they're unit-testable — added `tests/test_sync_scope.py` (6 tests) and
  `tests/test_lab_scope_inventory.py` (6 tests).
- `Makefile`'s `lint`/`test` targets replaced: real `ruff` + `mypy` +
  `ansible-lint` + (if installed) `packer fmt -check`, and real `pytest`.
  Degrades gracefully locally when a tool is missing; CI does not.
- `.github/workflows/ci.yml`: added a `python-quality` job (ruff + mypy +
  pytest) — previously there was no CI job for the Python layer at all.
- Fixed 4 real `mypy --strict` findings in
  `config/inventory/lab_scope_inventory.py` (bare `dict` instead of
  `dict[str, Any]`, one genuine type mismatch from an unannotated dict
  literal) surfaced while wiring this up.

**Verification performed (all actually run, not simulated):** `pytest` —
32/32 passing. `ruff check .` — clean. `mypy` (strict) — clean, 5 source
files. `ansible-lint config/` — clean at production profile.
`ansible-playbook --syntax-check config/site.yml` — passes.

**Not done / explicitly deferred:**

- Still no real WinRM/SSH target — none of the Ansible roles or the attack
  engine (not yet written) have executed against a live host.
- Packer/QEMU/UTM remain untested — this session's tooling unlock doesn't
  reach them (no pip install path for Homebrew-only tools).
- `attack/runner.py` (the engine that will actually use `scope_guard.py`)
  is next.

## 2026-08-01 — Session 1 continued: attack scenario engine (Phase 3, mock mode)

**Work done:**

- `attack/finding.py`: `Finding` dataclass (the normalized result schema —
  identical shape whether a run was dry-run or live), `write_run()`
  persists a scenario run to `attack/results/*.json` (gitignored).
- `attack/techniques.py`: 6-technique registry, each with an ATT&CK ID +
  `attack.mitre.org` reference URL, a `command_template` (what `--dry-run`
  prints verbatim), and a `mock_fixture` name. All 6 target `dc01`
  (`domain_controller` role) — including `unconstrained_delegation_coerce`,
  which is *conceptually* about `mem01` but sends its coercion RPC call to
  `dc01`; documented in the module docstring why "which host does the tool
  connect to" and "which host does this technique concern" aren't always
  the same host.
- `attack/chains.py`: 2 chains — `credential_harvest` (recon → credential
  access, exercises misconfigs 1-2) and `domain_dominance` (recon →
  privesc → lateral movement → domain dominance, exercises misconfigs
  3-4). `Chain.__post_init__` validates every referenced technique id
  actually exists in the registry.
- `attack/fixtures/*.json`: one mock-output fixture per technique, each
  with a `summary` + `details`. Any hash-shaped values are obvious
  placeholders (`<REDACTED_*_HASH_FIXTURE>`), not anything resembling real
  crackable output.
- `attack/runner.py`: `run_scenario(scenario, mode, scope_file)` — resolves
  every technique's target role through `ScopeGuard` **up front, before
  running anything**, so a chain either has every target available or
  refuses to start at all (no partial runs). `mode="dry_run"` (default)
  loads the fixture and never shells out; `mode="live"` builds the same
  command and actually runs it via `subprocess` — implemented for
  completeness per the continuation prompt's "real execution stays gated
  behind a provisioned lab" requirement, but **not exercised by any test**,
  since there's no live lab or installed offensive tooling here to run it
  against.
- `tests/test_attack_runner.py`: 11 tests — registry sanity (every chain
  references real techniques, every technique has an ATT&CK ID + fixture),
  dry-run resolution/command-building, chain ordering, and — the important
  ones — that an unprovisioned target or a chain where any technique can't
  resolve gets refused via `ScopeViolation`, not silently skipped.
- `Makefile`'s `attack` target rewritten: dry-run by default, `MODE=live`
  opt-in. CI (`python-quality` job) gained an explicit smoke-test step
  that runs the actual CLI against the real (unprovisioned)
  `inventory/lab-scope.yaml` and asserts it refuses — not just a unit
  test against a fixture, the real entry point against the real repo
  state.

**Verification performed (all actually run):** `pytest` — 43/43 passing
(11 new). `ruff`/`mypy --strict` — clean. Manually ran
`python3 -m attack.runner --scenario credential_harvest` against the real
`inventory/lab-scope.yaml` — correctly printed `REFUSED: No attackable
host with role 'domain_controller' found...` and exited 1. Manually ran
`run_scenario("domain_dominance", ...)` against a hand-built provisioned
fixture scope and confirmed the printed commands and summaries look right
end-to-end (captured in this session's transcript, not committed anywhere
— it's a manual sanity check, not a persisted artifact).

**Not done / explicitly deferred:**

- Live mode is implemented but genuinely untested — no real tool
  (`netexec`, `bloodhound-python`, `bloodyAD`, `petitpotam.py`,
  `secretsdump.py`) is installed here, and there's no lab to point them at.
- Only 6 hand-modeled techniques exist, chosen to match this lab's specific
  misconfigs — no Atomic Red Team or Caldera catalog integration yet.
- Telemetry (Phase 2) is still unwritten — next up, per the operator's
  stated priority order.

## 2026-08-01 — Session 1 continued: telemetry config (Phase 2), handbook.txt tracked

**Operator confirmed `handbook.txt`** (the mystery file flagged last
session) is theirs, placed from another source — tracked it as-is in one
commit, then synced its status sections (Phase 1 Ansible validation, Phase
3 dry-run engine) with actual current state in a second, since it had
predated that work. Operator also asked that `handbook.txt` be kept in
sync going forward whenever commands/setup steps change — noting this as
an ongoing habit for the rest of this build, not a one-time task.

**Work done (Phase 2, pure config — no execution needed to write any of
this, and none of it has run against a real host, since none exists):**

- `docs/adr/0006-telemetry-architecture.md`: WEF collector (`dc01`) +
  single Winlogbeat shipper design, chosen over per-host shippers.
  Documents explicitly that Sysmon cannot see Kerberos ticket operations
  or AD object access/replication — 4 of this lab's 6 implemented
  misconfigs (Kerberoasting, AS-REP roasting, ACL abuse, DCSync) are only
  detectable via Windows Security auditing, not Sysmon.
- `telemetry/sysmon/sysmon-config.xml` + README: narrow, purpose-built
  config (not a kitchen-sink community template) — every include/exclude
  rule traced back to a specific technique in `attack/techniques.py` or a
  `docs/vulnerabilities.md` item in the README's table.
- `telemetry/windows-audit-policy/`: 3 PowerShell scripts —
  `configure-audit-policy.ps1` (6 Advanced Audit Policy subcategories via
  named `auditpol` calls, not GUIDs, to avoid relying on values I couldn't
  verify), `configure-dcsync-sacl.ps1` (SACL on the domain NC for the
  `DS-Replication-Get-Changes[-All]` extended rights — the GUIDs are
  flagged for verification against a live schema, since I'm not fully
  certain of them from memory), `configure-object-sacls.ps1` (SACL on
  `Domain-Backups` so item 4's ACL abuse actually generates an event).
- `telemetry/wef/subscription.xml` + README: source-initiated WEF
  subscription pulling Sysmon + the relevant Security event IDs into
  `dc01`'s `ForwardedEvents`; README covers the GPO + `wecutil` + Security
  log SDDL steps needed on top of the XML itself.
- `telemetry/winlogbeat/winlogbeat.yml`: ships Sysmon/Security/
  ForwardedEvents from `dc01` to Elasticsearch on `siem01`.
- `telemetry/elastic/`: `docker-compose.yml` (single-node ES + Kibana,
  sized for a lab), `index-template.json` (extends winlogbeat's default
  template with this lab's custom fields), README.
- `telemetry/dashboards/`: `baseline-queries.md` (raw KQL/DSL checks for
  "is telemetry landing at all," including the actual Kerberoasting/
  AS-REP-roasting/DCSync detection queries a Phase 4 Sigma rule would be
  based on) and `baseline-dashboard.ndjson` — explicitly flagged as
  **hand-authored, not exported from a real Kibana and not import-tested**,
  since Kibana's saved-object schema is version-specific enough that I
  don't have confidence in it the way I do the syntax-checked artifacts.
  The README for that directory says outright which of the two to trust
  first.

**Verification performed:** every XML file confirmed well-formed
(`xml.dom.minidom.parse`), every YAML file confirmed valid
(`yaml.safe_load`), every JSON file confirmed valid (`json.load`,
including line-by-line for the NDJSON). No execution against a real host —
none exists.

**Not done / explicitly deferred:**

- None of this is wired into `config/dc`/`config/member`'s Ansible roles
  yet, or into a new `config/siem/` role (which doesn't exist) — every
  setup step documented here is currently manual.
- Wazuh/Splunk (`SIEM_BACKEND` alternatives) have no config — Elastic only.
- The DCSync SACL GUIDs and the NDJSON dashboard are this batch's two
  lowest-confidence artifacts specifically because I couldn't verify them
  against a live system — flagged accordingly rather than presented with
  the same confidence as the syntax-checked config.

## 2026-08-01 — Session 1 continued: detection library (Phase 4, fixture-tested)

**Work done:**

- Installed `sigma-cli`/`pySigma` via `pip install --user` (same no-sudo
  path as everything else this session) and used it for real — explored
  pySigma's actual parsed-condition object model (`ConditionAND`/`OR`/`NOT`,
  `ConditionFieldEqualsValueExpression`) interactively before writing
  anything, rather than assuming its shape.
- `detections/matcher.py`: evaluates a parsed `SigmaRule`'s real condition
  tree against a plain event dict. Deliberately does NOT reimplement
  Sigma's AND/OR/NOT/modifier semantics — reuses pySigma's own parser for
  that and only supplies the leaf-level "does this event's field match
  this Sigma value" comparison (wildcard via `fnmatch`, numeric-vs-string
  tolerant for `SigmaNumber`).
- `detections/sigma/`: 6 Sigma rules, one per `attack/techniques.py`
  technique — `kerberoasting` (4769/RC4, with a machine-account filter),
  `asrep_roasting` (4768/PreAuthType=0), `acl_genericall_abuse` (4662 on
  Domain-Backups), `unconstrained_delegation_coerce` (Sysmon PipeEvent on
  `\PIPE\efsrpc`/`\PIPE\lsarpc` — the actual PetitPotam-coercion
  signature), `dcsync` (4662 with the replication-rights GUIDs, filtered
  to exclude dc01's own legitimate replication — narrowly, since this
  lab's own DCSync technique uses a *captured mem01$ ticket*, so a
  naive "exclude all machine accounts" filter would have hidden our own
  attack chain; caught this while writing the rule, not after), and
  `bloodhound_collect` (process creation matching bloodhound-python/
  SharpHound signatures). All cite their technique's ATT&CK URL in
  `references` and an `attack.t####` tag.
- Ran `sigma check detections/sigma/` (sigma-cli, after fixing the same
  SSL cert issue as ansible-galaxy last session — `SSL_CERT_FILE` via
  certifi): found and fixed one real low-severity issue (`PreAuthType: '0'`
  should be an unquoted number, not a string).
- `detections/fixtures/`: one JSON file per technique with `matching` +
  `non_matching` synthetic events, each `non_matching` case commented with
  *why* it shouldn't match (e.g. "machine-account SPN request — excluded
  by filter_machine_accounts") — proving the rule's filters actually
  filter, not just that the happy path matches.
- `detections/coverage.py` + `detections/test_runner.py`: evaluates every
  technique, writes `detections/coverage_matrix.json` (committed, feeds
  the eventual Phase 5 heatmap). Deliberately does NOT shell out to
  `sigma-cli`'s `sigma check` automatically — its tag validator fetches
  MITRE ATT&CK data from GitHub, which would make `make detections-test`
  fail offline/in a restricted CI runner; uses pySigma's local parser
  directly instead, documented in the module's own docstring.
- `tests/test_matcher.py` (7 tests) + `tests/test_detections_runner.py`
  (5 tests, including an integration check against the real
  `detections/sigma/`+`detections/fixtures/` content, same pattern as
  `tests/test_attack_runner.py`'s registry sanity tests).
- `Makefile`'s `detections-test` target now real. CI: replaced the old
  `sigma-validate` stub job with `detections-test` (runs the real
  test_runner, uploads `coverage_matrix.json` as a build artifact).
- `docs/vulnerabilities.md` gained a Detection column linking items 1-4 to
  their Sigma rules; items 5/6/7/8 honestly marked "not started" (6 and 7
  have no exercising attack technique yet, so no rule exists for them).
- Synced `handbook.txt` again (Phase 4 status, `make detections-test`
  moved out of the "stub" bucket) per the operator's standing instruction
  to keep it current as commands/behavior change.

**Verification performed (all actually run):** `pytest` — 67/67 passing
(12 new). `ruff`/`mypy --strict` — clean, 13 source files. `sigma check
detections/sigma/` — 0 errors, 0 issues (after the one fix).
`make detections-test` run directly: 6/6 techniques covered (100%),
`detections/coverage_matrix.json` written.

**Not done / explicitly deferred:**

- No rule has been tested against real telemetry — the fixtures are a
  reasonable-effort approximation of real Sysmon/Security event shapes,
  hand-authored, not captured from an actual host (none exists yet).
- Misconfigs 6 (GPO edit rights) and 7 (SYSVOL plaintext creds) have
  neither an `attack/techniques.py` technique nor a Sigma rule yet — the
  telemetry to detect them exists (`telemetry/windows-audit-policy/`,
  Sysmon FileCreate on SYSVOL) but nothing exercises or detects them end
  to end.
- `detections/matcher.py` only handles the Sigma condition constructs this
  project's 6 rules actually use (AND/OR/NOT, field modifiers, OR-lists) —
  it's not a claim of full Sigma spec coverage (e.g. no aggregation
  conditions, no near/timeframe correlation).

## 2026-08-01 — Session 1 continued: platform layer (Phase 5) — backend tested, frontend not

**Work done:**

- `pyproject.toml` (root): added `[build-system]` + `[tool.setuptools.packages.find]`
  (explicit `include = ["attack*", "detections*"]` — flat-layout
  auto-discovery errors out with this many non-package top-level
  directories) so the root `eadadl` package can be `pip install -e .`'d
  for real. Added `attack/py.typed` + `detections/py.typed` (PEP 561
  markers) so a *separate* package's `mypy` run can resolve `attack.*`
  imports as typed.
- `platform/backend/`: FastAPI app — `app/config.py` (pydantic-settings),
  `app/database.py` (SQLAlchemy, SQLite dev default / Postgres via
  compose, no Alembic — documented scope decision), `app/models.py`
  (User/ScenarioRun/RunFinding), `app/schemas.py`, `app/auth.py` (JWT +
  viewer/operator RBAC), `app/bootstrap.py` (creates one operator account
  from `BACKEND_ADMIN_*` on first startup — no self-service registration,
  single-operator lab), `app/routers/{auth,scenarios,runs,coverage}.py`.
  `POST /runs` calls the real `attack.runner.run_scenario()` through the
  real scope guard — not a separate, less-safe path.
- Two-step install pattern established (`pip install -e .` at repo root,
  then `pip install -e platform/backend[.dev]`) since the backend imports
  `attack.*` directly rather than vendoring it — documented in
  `platform/backend/README.md` "Why a path dependency".
- 19 tests across `tests/{test_health,test_auth,test_scenarios,test_runs,test_coverage}.py`,
  using an in-memory SQLite `TestClient` fixture. Notably:
  `test_create_run_against_real_unprovisioned_scope_returns_403` —
  deliberately does NOT mock the scope file, proving the API is gated by
  actual repo state, same as the CLI's CI smoke test.
  `test_viewer_cannot_create_run` — RBAC actually enforced, not just
  declared.
- **Found and fixed a real bug getting tests green:** `passlib`'s bcrypt
  backend runs an internal self-test (hashing a 250-byte probe string)
  that throws under `bcrypt>=4.0`'s strict 72-byte-input enforcement — a
  currently-unfixed `passlib`/`bcrypt` version incompatibility, not
  anything wrong with this code's own inputs. Switched to calling `bcrypt`
  directly instead of `passlib.CryptContext`; documented in `app/auth.py`.
- Chased down a second real issue: `mypy` couldn't resolve `attack.*`
  imports from within `platform/backend/` despite the editable install
  working fine at runtime — root cause: modern `pip install -e` uses a
  PEP 660 finder-based mechanism (a generated Python file registered as an
  import hook) that mypy's static import resolution can't see, since mypy
  doesn't execute Python import machinery. Fixed with an explicit
  `mypy_path = ["../.."]` in `platform/backend/pyproject.toml` rather than
  fighting the editable-install mechanism.
- Also hit (twice) a reminder that shell state doesn't persist between
  Bash tool calls in this environment — a `pip install --user
  types-python-jose` run without re-exporting `PATH` landed in a different
  `site-packages` than the one `mypy`/`pytest` actually use, silently
  "succeeding" while not fixing anything. Re-ran with `python3 -m pip
  install --user ...` and explicit `PATH` export; now consistent.
- `platform/frontend/`: Next.js 15 App Router + TypeScript (strict) +
  Tailwind. Pages: `/` (dashboard — trigger a dry-run, view history),
  `/runs/[id]` (findings detail), `/coverage` (heatmap from the real
  `GET /coverage`), `/login`. `src/lib/api.ts` (typed fetch wrapper, JWT in
  `localStorage`), `src/lib/types.ts` (hand-kept in sync with
  `app/schemas.py` — no generated client).
- `platform/docker-compose.yml` (Postgres + backend + frontend, outside
  the lab network — distinct from `telemetry/elastic/docker-compose.yml`,
  which runs the SIEM stack *inside* the lab on `siem01`) +
  `platform/backend/Dockerfile` + `platform/frontend/Dockerfile`.
- `.github/workflows/ci.yml`: `backend` job now unconditional and real
  (two-step install, `ruff`/`mypy`/`pytest`); `frontend` job switched from
  `npm ci` to `npm install` (no lockfile exists yet — no local npm to
  generate one).
- `.env.example`: added `BACKEND_ADMIN_USERNAME`/`BACKEND_ADMIN_PASSWORD`.

**Verification performed:** Backend — `pytest`: 19/19 passing. `ruff
check .`: clean. `mypy .` (strict): clean, 20 source files. Root repo's
own `make lint`/`make test` re-confirmed green after the root
`pyproject.toml` changes (55 tests, unaffected). Frontend — **none**: no
local Node.js to run `npm install`/`tsc`/`eslint` against any of it.
`docker-compose.yml`/both `Dockerfile`s — YAML-syntax-checked only, not
built (no local Docker).

**Not done / explicitly deferred:**

- Frontend is genuinely unvalidated — flagged prominently in
  `platform/frontend/README.md` and `ROADMAP.md` rather than presented
  with the same confidence as the tested backend.
- No Alembic migrations (SQLite `create_all()` only) — a real scope
  decision for a lab-scale app with disposable run-history data, not an
  oversight; documented in `platform/backend/README.md`.
- `mode=live` on `POST /runs` goes through the same untested live path as
  `attack/runner.py`'s CLI — no lab exists to exercise it either way.
- No rate limiting, no fine-grained per-scenario permissions, no
  `package-lock.json` (blocks `npm ci` in CI until one exists).
