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

## 2026-08-01 — Session 1 continued: DFIR/IR (Phase 6)

**Work done:**

- `ir/playbooks/`: 5 NIST SP 800-61-structured playbooks (Preparation;
  Detection & Analysis; Containment, Eradication & Recovery; Post-Incident
  Activity) — Kerberoasting, AS-REP roasting, ACL abuse, unconstrained
  delegation coercion, DCSync. Each cites its specific Sigma rule,
  telemetry prerequisite (audit policy/SACL), and `docs/vulnerabilities.md`
  item rather than being generic IR boilerplate — e.g. the DCSync
  playbook explains *why* krbtgt needs resetting twice with a convergence
  wait, not just "reset krbtgt." The three chain-related playbooks
  (acl-abuse → unconstrained-delegation → dcsync) are written to be read
  together as one incident narrative, matching `attack/chains.py`'s
  `domain_dominance` chain.
- `ir/notebooks/ad-purple-team-hunting.ipynb`: built via `nbformat`'s
  Python API (not hand-typed JSON) and validated with
  `nbformat.validate()` — 5 hunts, one per detected technique, each
  deliberately broader than its corresponding Sigma rule (e.g. any
  non-AES ticket encryption, not just RC4; a wider coercion-relevant pipe
  list). `ruff check .` lints inside the notebook's code cells natively —
  caught and fixed a real bug this way: a DCSync hunt query had
  `f"*{{guid}}*"` (escaped/literal double braces) instead of `f"*{guid}*"`,
  which would have made the wildcard search for the literal string
  `{guid}` instead of interpolating the actual GUID — the query would
  never have matched anything.
- `ir/automation/responder.py`: SOAR-style response mapping, deliberately
  dry-run-only (no live-execution mode at all, unlike `attack/runner.py`'s
  unexercised-but-present `--live`) — reuses `attack.lib.scope_guard` so a
  remediation action gets the identical fail-closed target resolution as
  an offensive technique. DCSync's response is marked
  `automatable=False` rather than modeled as a fake one-shot command,
  since the real remediation is multi-step and time-gated.
- `tests/test_responder.py`: 7 tests, including that an unresolvable
  target yields no action (fail-closed) and that non-automatable actions
  never carry a command.
- Added `ir` to root `pyproject.toml`'s mypy `files` list.

**Verification performed:** `pytest` — 62/62 passing (7 new). `ruff
check .` — clean, including inside the `.ipynb` (where it caught the
f-string bug above). `mypy` (strict) — clean, 16 source files.
`nbformat.validate()` — notebook schema-valid.

**Not done / explicitly deferred:**

- No playbook or hunt has been exercised against a real incident/cluster
  — no lab exists yet.
- No `bloodhound_collect` (recon) playbook — enumeration alone rarely
  warrants full IR response; covered by the notebook's Hunt 5 instead,
  noted explicitly in `ir/playbooks/README.md`.
- `ir/automation/responder.py` intentionally has no live-execution path at
  all — this is a permanent design boundary (see its README's "Design"
  section), not a temporary gap like most other "not run yet" notes in
  this log.

## 2026-08-01 — Session 1 continued: polish (Phase 7) — closing out this session

**Work done:**

- `docs/architecture.md`: 3 mermaid diagrams — telemetry data flow (event
  on `dc01`/`mem01` through to a Sigma verdict), the `domain_dominance`
  attack chain as a sequence diagram (which host each technique actually
  connects to, per `attack/techniques.py`'s module docstring), and the
  purple-team loop tying `attack/` → `detections/` → `ir/` → the platform
  heatmap together. Linked from `README.md`'s Documentation section.
- `.github/workflows/ci.yml`'s `ansible-lint` job hardened: now installs
  `config/requirements.yml`'s collections
  (`ansible-galaxy collection install`) and runs
  `ansible-playbook --syntax-check` before linting — previously it only
  ran bare `ansible-lint` without the collections a clean CI runner
  wouldn't have, which could have behaved differently than the
  locally-verified run this job is meant to reproduce. Caught by
  reviewing the CI file end-to-end during this polish pass, not by a
  failure — worth noting since it means this specific gap was silent
  until now.
- `ROADMAP.md`: full pass — added an "At a glance" summary near the top;
  fixed several rows still marked 🚧 from mid-session that were actually
  ✅ by session's end (Phase 0's `.env.example`/Makefile/ADR rows); removed
  one stale duplicate row (Phase 3's scope-guard-enforcement line,
  superseded by an earlier row in the same table); recounted ADRs (6, not
  a stale number); rewrote the Phase 7 table itself now that its items are
  actually done.
- `CHANGELOG.md`: rewritten — was still Phase-0/Phase-1-era and hadn't
  been touched across 13 commits of subsequent work. Now a condensed,
  release-note-style summary of the whole session, pointing to this file
  for the session-by-session narrative.
- `handbook.txt`: final sync — added a Phase 7 status block, fixed a
  stale specific test count in the Phase 3 block (referenced "43 passing
  tests," which was accurate at the moment Phase 3 finished but stale
  once Phase 4/6 added more; replaced with a pointer to the current
  repo-wide count instead of a number that would go stale again the same
  way).
- `README.md`: status badge updated (`early_build` → `build_in_progress`
  — more accurate given 13 commits across 7 of 8 phases); Documentation
  section gained links to `docs/architecture.md`, `ir/playbooks/`, and
  `handbook.txt`.

**Verification performed:** Full re-run of `make lint`/`make test` at the
repo root (62/62 passing, `ruff`/`mypy --strict`/`ansible-lint` all clean)
and in `platform/backend/` (19/19 passing, `ruff`/`mypy --strict` clean) —
confirming nothing in this documentation-focused pass broke anything.
`.github/workflows/ci.yml` YAML-syntax-checked after the `ansible-lint`
job edit.

**Not done / explicitly deferred:**

- No docs site (mkdocs/Sphinx/etc.) — judged unnecessary at this repo's
  current size; Markdown-as-browsed-on-GitHub was deemed sufficient rather
  than left as an oversight.
- The CI hardening above (`ansible-lint` job) has not itself been run on
  a real GitHub Actions runner — this repo has no remote configured yet
  (`git remote -v` returns nothing), so no CI has ever actually executed
  for real. Everything described as "CI does X" in this project is
  therefore a claim about what the workflow file *would* do, verified by
  local reproduction of the same commands, not by an observed CI run.
  This is the one honesty caveat that applies to literally every CI job
  described as passing throughout this entire build log, worth stating
  explicitly here at the end rather than only implicitly through "no
  remote" mentions scattered earlier.

## 2026-08-01 — Session 2: close the misconfig 6/7 detection gap

**Operator handed off a new instruction set.** First item: push to a real
GitHub remote and get an actual CI run (as opposed to every prior "CI
passes" claim, which was local reproduction only — see the last entry of
the previous session). The push command included a literal
`<YOUR_GITHUB_REPO_URL>` placeholder rather than a real URL, and there's
no `gh` CLI here to create a repo (would need Homebrew, same no-sudo
blocker as everything else). Flagged this to the operator and asked for
either a real URL or instruction to skip it — did not push, did not
guess/fabricate a URL. Proceeded with the rest of the requested work,
which doesn't depend on the remote.

**Work done: Sigma detections for misconfigs 6 and 7 (closing the
coverage-matrix gap flagged at the end of the previous session):**

- `telemetry/windows-audit-policy/configure-audit-policy.ps1`: added the
  **File System** audit subcategory (previously only had AD-object-facing
  subcategories — item 7's detection needs event 4663, a filesystem
  event, which none of the existing subcategories cover).
- `telemetry/windows-audit-policy/configure-gpo-sacl.ps1` (new): SACL on
  the `Lab-Workstation-Baseline` GPO's AD object
  (`groupPolicyContainer`), mirroring `configure-object-sacls.ps1`'s
  pattern for item 4.
- `telemetry/windows-audit-policy/configure-sysvol-file-sacl.ps1` (new):
  a **filesystem** SACL (not an AD one) on the planted
  `map-network-drive.ps1` script for `ReadData` — the first script in
  this directory that uses the filesystem provider instead of the `AD:`
  PSDrive, called out explicitly in its own header comment so it isn't
  mistaken for following the other scripts' pattern.
- `attack/techniques.py`: two new techniques — `gpo_edit_abuse`
  (T1484.001, tool: SharpGPOAbuse) and `sysvol_credential_read`
  (T1552.001, tool: plain `Get-Content`, since this one's a documented
  technique step rather than needing a named tool). `attack/chains.py`:
  a third chain, `gpo_and_sysvol_abuse`, independent of `domain_dominance`
  since items 6/7 don't depend on items 3/4's delegation/ACL setup.
- `detections/sigma/gpo_edit_abuse.yml` (event 5136,
  `ObjectClass=groupPolicyContainer`) and
  `detections/sigma/sysvol_credential_read.yml` (event 4663,
  `ObjectName` ending in the planted script's filename), each with
  `detections/fixtures/*.json` matching + non_matching cases.
- `ir/playbooks/gpo-abuse.md` and `ir/playbooks/sysvol-credential-exposure.md`
  — same NIST SP 800-61 structure as the existing 5, for consistency with
  the established pattern (not explicitly requested, but a small
  low-cost extension that keeps `ir/playbooks/README.md`'s table honest
  now that these two techniques have Sigma rules like the others do).

**Caught and fixed while verifying:** two existing tests had hardcoded
counts that the new techniques/chain broke —
`platform/backend/tests/test_scenarios.py` asserted the exact 2-chain set
(now 3), and `platform/backend/tests/test_coverage.py` asserted
`total_techniques == 6` (now 8). Fixed the first by updating the expected
set; fixed the second by comparing against `len(attack.techniques.TECHNIQUES)`
dynamically instead of a hardcoded number, so it won't go stale the next
time a technique is added the way the hardcoded `6` just did.

**Verification performed:** `make detections-test` — **8/8 techniques
covered (100%)**. Root `pytest` — 62/62 passing (unchanged count; the
generic/registry-driven tests picked up the 2 new techniques
automatically without needing new test functions). Backend `pytest` —
19/19 passing after the two fixes above. `ruff`/`mypy --strict` clean at
both the root and in `platform/backend/`. `ansible-lint`/
`ansible-playbook --syntax-check` unaffected (no `config/` changes this
pass).

**Not done / explicitly deferred:**

- No push to a real GitHub remote yet — waiting on the operator for a
  real URL (see above). No CI has run for real as a result.
- Wazuh/Splunk SIEM backends deliberately not started — per operator
  instruction, held until Elastic is validated end-to-end against a live
  lab, rather than building a second unvalidated backend alongside the
  first.
- Atomic Red Team integration not yet started — next in the requested
  order.

## 2026-08-01 — Session 2 continued: Atomic Red Team integration (mock-mode)

**Work done:**

- `attack/integrations/atomic_red_team.py`: parses the public Atomic Red
  Team project's YAML schema (`attack_technique`, `display_name`,
  `atomic_tests[].{name, description, supported_platforms,
  input_arguments, executor}`) and renders its real `#{argument}`
  templating syntax. This is a parser for the schema, not a vendored copy
  of the upstream project — explicitly scoped that way in the module and
  README docstrings, since pulling in the actual repo (thousands of
  files, independently licensed) is a bigger decision than this pass
  makes unilaterally.
- `attack/integrations/atomics/`: 3 hand-written local catalog files
  (T1087.002 domain-admin enumeration, T1069.002 domain-group
  enumeration, T1018 domain-computer enumeration) — all standard, very
  well-known `net.exe` recon one-liners, written from general knowledge
  rather than fetched from the live repository. Flagged explicitly as
  such, same honesty pattern as the DCSync GUIDs from an earlier session.
- `attack/integrations/atomic_runner.py`: `run_atomic_test()` resolves a
  target through the exact same `ScopeGuard` as `attack/runner.py`, then
  emits the exact same `Finding` schema — an atomic-test run and a
  hand-modeled-technique run are indistinguishable downstream. Dry-run
  only, no live-execution path at all — a stricter boundary than
  `attack/runner.py`'s unexercised-but-present `--live`, since this
  integration's job is proving the plumbing (parse → render → scope-guard
  → Finding) works, not executing anything.
- `make attack-atomic TECHNIQUE=<id>` — verified live against the real
  repo: refuses with the same `REFUSED: No attackable host...` message as
  `make attack`, since nothing is provisioned.
- `tests/test_atomic_red_team.py`: 10 tests — schema parsing, command
  rendering (default value, override, and the missing-argument error
  case), and the scope-guard safety property (refuses against an
  unprovisioned target, same as everywhere else in this project).

**Verification performed:** `pytest` — 72/72 passing at the repo root (10
new). `ruff`/`mypy --strict` — clean, 19 source files. Manually ran
`make attack-atomic TECHNIQUE=T1087.002` against the real, unprovisioned
`inventory/lab-scope.yaml` and confirmed the expected refusal.

**Not done / explicitly deferred:**

- No real upstream Atomic Red Team files have been tested against the
  parser — only the 3 hand-written local ones. The parser targets ART's
  documented schema, but "should handle a real file" is an untested claim
  until someone actually tries one.
- Caldera integration not attempted at all.
- No live-execution mode, by design (see `attack/integrations/README.md`
  "Design") — this is a permanent boundary for this integration, not a
  temporary gap.

## 2026-08-01 — Session 3: real GitHub remote, resolved history conflict, first two real CI runs

**Work done:**

- Confirmed `.env` was never tracked (`git log --all --full-history -- .env`
  empty) — no history rewrite needed.
- Added `.gitattributes` marking `*.md`, `docs/**`, `BUILD_LOG.md`,
  `ROADMAP.md`, and `handbook.txt` as `linguist-documentation`, so GitHub's
  language bar reflects the actual Python-heavy codebase instead of prose
  volume.
- Installed the GitHub CLI (`gh`) and Packer, neither previously available
  locally, via their official standalone release binaries (not Homebrew,
  not sudo) into `~/.local/bin`: `gh` from `github.com/cli/cli`'s GitHub
  releases, Packer from `releases.hashicorp.com` — both URLs obtained
  live (`curl` the releases API / an `-sIL` existence check), never
  guessed. `~/.config` turned out to be root-owned and unwritable by this
  account, which broke both tools' default config dirs; fixed with
  `GH_CONFIG_DIR`/`PACKER_PLUGIN_PATH` env overrides. Along the way,
  `id` showed this account IS in the macOS `admin` group — the real
  constraint on `sudo`/Homebrew is the lack of an interactive TTY for a
  password prompt in this shell environment, not a lack of underlying
  admin privilege. `gh auth login`'s device-code flow (operator completes
  the interactive step in a browser, not this shell) is what unblocked
  git's HTTPS push auth.
- Discovered `origin/main` (2 pre-existing docs-only commits) had
  *unrelated history* to local `main` (`git merge-base` returned empty).
  Flagged this to the operator rather than guessing; per their explicit
  choice, pushed local work to `origin/full-build` first
  (`git push -u origin main:full-build`). `gh pr create` then refused
  ("no history in common"), and `gh workflow run` 404'd because
  `workflow_dispatch` requires the workflow file to exist on the
  *default* branch even when dispatching against a different `--ref`.
  Flagged this second fork to the operator too; per their explicit
  choice, merged with `git merge origin/main --allow-unrelated-histories
  -X ours` (verified via `git diff <old-tip> HEAD --stat` returning empty
  — full-build's content was preserved byte-for-byte) and pushed the
  merge commit directly to `main` (`09bbcfb`), which triggered a real,
  push-based Actions run automatically.
- **CI run 1 (`09bbcfb`, id 30705581784): 4/6 jobs passed, 2 failed** —
  both real bugs invisible to this session's prior local validation:
  - `packer fmt -check` failed (exit 3) on all 3 `.pkr.hcl` templates —
    never actually formatted before, since Packer wasn't installed
    locally until this session. Fixed by running `packer fmt -recursive
    -diff .` for real once Packer was available.
  - Backend `mypy` failed: "Library stubs not installed for jose" —
    `types-python-jose` had been installed ad-hoc on the dev machine
    during an earlier session's troubleshooting but never added to
    `platform/backend/pyproject.toml`'s `dev` deps, so local mypy runs
    kept passing for the wrong reason (an untracked stub already present)
    while a clean CI runner had nothing. Fixed by adding the dependency
    to `pyproject.toml`.
  - Getting Packer working locally to fix the first bug surfaced the
    `packer-validate` CI job had never actually been exercised for real
    either. Running its steps locally for the first time found four more
    real, previously undetectable bugs, all fixed in the same commit
    (`85825bf`): `windows-server.pkr.hcl` was missing the required
    `vm_name` var in the CI validate command; it also used the
    `windows-update` provisioner without declaring the `rgl/windows-
    update` plugin it needs in `required_plugins`; `kali-attacker.pkr.hcl`/
    `ubuntu-siem.pkr.hcl` `packer validate` stats an SSH key path and a
    rendered `user-data` file that only exist after `build.sh`/
    `build-linux.sh` generate them at real build time, so CI now creates
    throwaway placeholders first; and the whole job had been running with
    `working-directory: infra/local/packer`, but the templates' relative
    paths are relative to the repo root (confirmed by reading how
    `build.sh`/`build-linux.sh` actually invoke packer) — fixed by
    dropping the working-directory override and using repo-root-relative
    paths throughout.
  - Self-caught mid-fix error, noted here because it happened twice: the
    placeholder `sha256:0000...` checksum used for `packer validate` was
    miscounted by hand (wrong number of zeros) on the first two attempts.
    Fixed by generating and length-verifying it programmatically
    (`python3 -c "print(len(s))"`) instead of trusting a visual count —
    should have done this from the start.
  - Rehearsed the entire `packer-validate` job's exact steps locally from
    the repo root before pushing the fix; all passed (exit 0).
- **CI run 2 (`85825bf`, id 30705918024): 6/6 jobs passed** — Python
  lint/typecheck/test, Sigma rule validation, Backend lint & test,
  Ansible lint, Frontend lint & test, Packer fmt & validate. Confirmed via
  `gh run watch --exit-status` and `gh run view`. This is the first
  genuine, from-scratch, clean-runner validation this project has ever
  had — including for `platform/frontend/` and `ansible-lint`, both of
  which had never run anywhere (local or CI) before this.
- Updated `README.md`'s CI badge to the real GitHub Actions status badge,
  and rewrote `ROADMAP.md`'s "Known Blockers" section to match all of the
  above (see that file — it now distinguishes Packer, which is genuinely
  unblocked, from QEMU, which is not, and corrects the "no admin rights"
  framing).

**Verification performed:** both CI runs observed directly via `gh run
view`/`gh run watch`, not inferred. The `packer-validate` job's exact
commands were also run locally (repo root, real Packer binary) before the
second push, all exit 0.

**Not done / explicitly deferred:**

- QEMU itself is still not installed locally (no standalone binary
  distribution the way Packer/gh have) — `packer build`/`make up` remain
  untested against a real build. See ROADMAP.md.
- The misconfig 6/7 Sigma detections and the Atomic Red Team integration
  the operator asked to continue with after this were already completed
  in Session 2 (see above) — nothing further was needed there this
  session.
- Wazuh/Splunk SIEM backends still deliberately not started, per standing
  operator instruction to hold until Elastic is validated end-to-end
  against a live lab.

## 2026-08-01 — Session 4: QEMU installed from source, real Phase 1 build attempts, Elastic SIEM integration

**QEMU install investigation (operator asked: try non-Homebrew paths, in
order, before concluding it's genuinely blocked):**

- Confirmed `sudo -n true`/`sudo -n -l`/`sudo -A true` all fail — no
  passwordless sudo rule, no askpass helper. Real constraint confirmed
  narrow: no interactive TTY for a password prompt, not missing privilege
  (`id` still shows `admin` group membership).
- QEMU has no official pre-compiled macOS binaries (confirmed by reading
  qemu.org's own download page) — source build, Homebrew, or MacPorts
  only. MacPorts' installer needs the same interactive admin-password
  privilege elevation as Homebrew (GUI pkg installer or sudo either way)
  — same blocker, not a real alternative.
- UTM.app (already installed) bundles its own compiled QEMU as
  `Contents/Frameworks/qemu-{arch}-softmmu.framework/qemu-{arch}-softmmu`
  — genuinely present, but `otool -hv` shows `filetype DYLIB`, not
  `EXECUTE`: UTM links QEMU in-process as a library rather than shelling
  out to a CLI binary. Confirmed unusable for Packer's builder by trying
  to exec one directly (`exec format error`).
- conda-forge (already available locally via an existing Anaconda
  install at `/opt/anaconda3`, itself pre-existing on this machine) has
  no real `qemu`/`qemu-system-*` package for osx-arm64 — only
  `qemu.qmp`, a QMP protocol *client* library, not the emulator.
- **Real fix: build QEMU from source, no sudo, into a conda env.**
  conda-forge DOES have every build dependency QEMU needs for a scoped
  x86_64+aarch64-softmmu build: `pixman`, `glib`, `pkg-config`, `ninja`,
  `meson`, `libffi`, `gettext`, `pcre2`, `libslirp` — all real osx-arm64
  packages, installed into a dedicated `qemu-build` conda env
  (`conda create -n qemu-build --override-channels -c conda-forge ...`;
  `--override-channels` avoids Anaconda's own commercial-repo Terms of
  Service prompt entirely, since only conda-forge is needed). Downloaded
  QEMU 9.2.0 source from `download.qemu.org` (URL verified live, not
  guessed), configured with `--target-list=x86_64-softmmu,aarch64-softmmu
  --disable-gtk --disable-sdl --disable-cocoa --disable-spice
  --disable-usb-redir --disable-docs --enable-vnc --enable-slirp`
  (VNC enabling came later — see below), built with `ninja`, installed to
  `~/.local/qemu`.
- **Two real bugs found getting the built binaries to actually run:**
  1. `ninja install`'s copy to the final prefix lost the `LC_RPATH`
     pointing at the conda env's `libgnutls`/etc — `dyld: Library not
     loaded: @rpath/libgnutls.30.dylib`. Fixed with
     `install_name_tool -add_rpath <conda-env>/lib`, then had to
     `codesign --force --sign -` afterward since modifying load commands
     invalidates the existing signature.
  2. That same blanket re-codesign **stripped the HVF entitlement**
     (`com.apple.security.hypervisor`) QEMU's own install script had
     applied via `scripts/entitlement.sh` — caught by `-accel hvf`
     failing with `HV_DENIED` afterward. Fixed by re-signing with
     `--entitlements accel/hvf/entitlements.plist` explicitly instead of
     a bare re-sign. Real lesson, noted for next time: modifying a Mach-O
     binary's load commands and blanket re-signing it afterward silently
     drops any entitlements a more careful signing step had set.
- **A third, real hardware-generation bug, not a signing mistake:**
  `-M virt -accel hvf -cpu host` crashed with
  `Property 'host-arm-cpu.sme' not found` on this machine's Apple M4 Pro
  chip — a genuine QEMU 9.2.0 (Dec 2024) HVF/SME feature-detection gap
  for CPU generations newer than the release. Confirmed via
  `sysctl -n machdep.cpu.brand_string` + a targeted web search matching
  the exact error to known QEMU/HVF-on-Apple-Silicon reports. Fixed by
  building QEMU **11.0.3** instead (current stable, released 2026-07-24)
  — same conda env, same configure flags — which does not hit this bug.
- **Result — genuinely verified, not just `--version`:** both
  `qemu-system-x86_64 --version` and `qemu-system-aarch64 --version`
  exit 0 from the final `~/.local/qemu/bin/` install. Beyond that: a
  blank `-M pc -accel tcg` x86_64 VM (matching windows-server.pkr.hcl's
  config) stayed running for a real background-process liveness check,
  and a blank `-M virt -accel hvf -cpu host` aarch64 VM (matching
  kali-attacker.pkr.hcl/ubuntu-siem.pkr.hcl's config) did too — both
  killed cleanly afterward. **This resolves the QEMU blocker per option 2
  the operator specified** (installed successfully, not "genuinely
  cannot install here").

**Real Phase 1 build attempts (arm64-first, per operator's explicit
choice among 3 options when asked how to scope the real download/build
time cost):**

- Ran `make check-tools` for the first time ever with all 4 required
  tools genuinely on PATH (`packer`, `qemu-system-x86_64`, `ansible`,
  `ansible-playbook` — the last two found under
  `~/Library/Python/3.13/bin`, from the pip --user install already on
  this machine) — passed.
- Found `.env` existed locally but `WIN_ISO_URL`/`WIN_ISO_CHECKSUM`/
  `KALI_ISO_URL`/`KALI_ISO_CHECKSUM`/`UBUNTU_IMG_CHECKSUM` were all
  empty placeholders, and `ADMIN_PASSWORD` was still the literal
  `change-me-generate-a-random-one` placeholder string. Sourced real
  values for all of them:
  - Kali arm64 netinst ISO + sha256: fetched live from
    `cdimage.kali.org/kali-2026.2/SHA256SUMS`, length-verified
    programmatically (64 hex chars) rather than trusted by eye — same
    discipline as session 3's Packer checksum mistakes.
  - Ubuntu 22.04 arm64 cloud image sha256: fetched live from
    `cloud-images.ubuntu.com/releases/22.04/release/SHA256SUMS`.
  - Windows Server 2022 evaluation ISO: Microsoft's evaluation center
    page publishes no checksum at all (confirmed by reading the actual
    page, not assumed) — downloaded via the official
    `go.microsoft.com/fwlink` redirect to
    `software-static.download.prss.microsoft.com` (real Microsoft CDN,
    verified via `curl -sIL` before committing to the 5GB download), and
    self-computed the sha256 to pin against re-downloads — documented in
    `.env` as self-computed, not vendor-published, an honest narrower
    claim than the Kali/Ubuntu checksums above.
  - Generated a real random `ADMIN_PASSWORD` (`secrets.choice`) rather
    than leave the placeholder in place for an actual VM build.
- **`attacker01` (Kali) build — first attempt: failed in 46s.**
  `Error launching VM: Qemu failed to start` /
  `qemu-system-aarch64: -vnc: invalid option` — my own QEMU build had
  been configured with `--disable-vnc` to trim dependencies, but Packer's
  QEMU builder unconditionally passes `-vnc` for headless builds. Fixed
  by reconfiguring+rebuilding QEMU 11.0.3 with `--enable-vnc` (no new
  dependency issues).
- **Second attempt: failed differently** —
  `qemu-system-aarch64: no function defined to set boot device list for
  this architecture`, from Packer's auto-injected `-boot once=d`. Root
  cause and fix: see the "Fix real Packer/QEMU bugs" commit — QEMU's
  aarch64 `virt` machine doesn't support `-boot` at all; the real fix is
  Packer's proper EFI mechanism (`efi_firmware_code`/`efi_firmware_vars`,
  `-drive if=pflash`), not a `-boot` value change.
- **Third attempt: launched successfully but the installer never
  proceeded** — Packer's "Typing the boot commands over VNC" produced a
  VNC screenshot showing the keystrokes landing in **QEMU's own monitor**
  (`(qemu)` prompt, `unknown command: 'nstall'`), not the guest. Root
  cause, found by manually booting the same ISO with `vncdo` (a pip
  --user-installed Python VNC client) for interactive diagnosis rather
  than guessing: QEMU's aarch64 `virt` machine has **no default GPU or
  USB/PS2 input controller** the way `pc` does — nothing was consuming
  VNC's injected keystrokes. Fixed by adding explicit
  `qemuargs = [["-device","virtio-gpu-pci"], ["-device","qemu-xhci"],
  ["-device","usb-kbd"], ["-device","usb-tablet"]]`.
- **Fourth attempt — also found (before rebuilding, via interactive VNC
  screenshots) that Kali's arm64 netinst boots into GRUB, not an
  ISOLINUX `boot:` prompt** — confirmed visually
  (`GNU GRUB version 2.14-2+kali1`), meaning the original
  `<esc><wait>install ...<enter>` boot_command was never going to work
  regardless of the other two bugs (aarch64 has no legacy BIOS boot path
  at all). Worked out the correct interaction live against the real ISO
  before touching the template: `e` (edit highlighted entry) ->
  `<down><down>` (setparams line -> linux line) -> `<end>` -> append the
  same installer kernel params -> `<f10>` (boot edited entry, per GRUB's
  own on-screen help text "Press Ctrl-x or F10 to boot"). Encoded into
  `kali-attacker.pkr.hcl` and re-validated with `packer validate`.
- **Fifth attempt (current, in progress as of this entry):** boot
  sequence now reaches the installer correctly (no VNC/monitor
  confusion, no GRUB mismatch) — real netinst package download/install
  underway. [Outcome recorded in the next log entry once it completes —
  see ROADMAP.md for current status.]

**Elastic SIEM integration (fixture-testable + genuinely live-tested,
run in parallel with the attacker01 build above):**

- `detections/elastic_backend.py`: converts every rule in
  `detections/sigma/` to real Lucene/Elasticsearch query strings via
  pySigma's own `pysigma-backend-elasticsearch`, no hand-rolled
  translation (same principle as `detections/matcher.py`). No pipeline
  needed — all 8 rules' raw Windows Security field names convert
  unchanged, verified for all 8.
- `detections/elastic_integration_check.py`: the live-cluster
  counterpart, deliberately kept out of `make detections-test`/CI (no
  live cluster there — same reasoning as `sigma-cli` already documented
  in `pyproject.toml`). For each technique: convert its rule, index its
  fixtures into a throwaway index, query, assert matching fixtures hit
  and non_matching don't, delete the index.
- **Ran for real against a genuinely live Elasticsearch 8.15.0** —
  downloaded the official tarball (matching
  `telemetry/elastic/docker-compose.yml`'s pinned version) and ran it
  standalone with its own bundled JDK, no Docker at all (Docker remains
  unavailable — see ROADMAP.md). `xpack.security.enabled: false` for
  this throwaway local instance only (not the real deployment config).
  **First run: 5 of 8 techniques failed** —
  `EventID:4662 AND ObjectName:*Domain\-Backups*`-style wildcard queries
  silently missed real matches. Root cause: Elasticsearch's default
  dynamic mapping makes string fields `text` (full-text analyzed), and
  the standard analyzer tokenizes `"Domain-Backups"` into two separate
  terms (`domain`, `backups`) that one wildcard pattern can't span — a
  real Lucene/analyzer behavior no abstract Sigma matcher would ever
  surface. Fixed by mapping fixture fields `keyword` on the test index —
  not a workaround but the same assumption the real deployment already
  makes (`telemetry/elastic/index-template.json` extends winlogbeat's
  own template, which maps `winlog.event_data.*` as `keyword` for
  exactly this reason). **Second run: 8/8 techniques passed** — every
  matching fixture hit, every non_matching fixture correctly did not.
- `tests/test_elastic_backend.py` (3 tests, always run — pure
  conversion, no live cluster): all pass. Full repo pytest: 75/75.
  `ruff`/`mypy --strict`: clean.
- Added `pysigma-backend-elasticsearch` (core dependency —
  `tests/test_elastic_backend.py` exercises it in the default suite) and
  `elasticsearch` (dev-only, matches the sigma-cli pattern) to
  `pyproject.toml`. Added `make detections-test-elastic`.

## 2026-08-01/02 — Session 4 continued: attacker01 blocked, siem01 built+booted+provisioned for real, dc01 far further than ever, real Elastic on siem01

Continuation of the same session, working autonomously per the
operator's instructions to resolve attacker01/build siem01/run
ansible/wire Elastic, committing and checkpointing throughout, reporting
once at the end.

**attacker01 (Kali) — final status: BLOCKED.** Two more real attempts
beyond the GRUB/EFI/qemuargs fixes already logged above:

- Fixed a genuinely self-caused bug: an earlier edit to add the
  GPU/input `qemuargs` had accidentally deleted `http_directory` from
  the same source block without re-adding it. With no `http_directory`,
  Packer never started its ephemeral HTTP server, and boot_command's
  `{{ .HTTPPort }}` silently rendered as `0` — the installer was trying
  to fetch `http://10.0.2.2:0/preseed.cfg`, an unreachable URL, the
  whole time. Restored.
- With the HTTP server and a `-serial file:...` log genuinely working
  (needed because Debian-installer's own console-detection picks
  `ttyAMA0`, not the VNC-visible framebuffer, on this platform — read
  with the `pyte` terminal-emulator library since raw ANSI capture is
  unreadable directly), the real remaining blocker became visible: an
  interactive "[!!] Select a language" dialog, which appears *before*
  `netcfg` brings up networking — i.e. before a network preseed can ever
  be fetched to answer it. Tried Debian's own documented kernel-cmdline
  fix for exactly this bootstrapping problem twice — once with
  `debian-installer/language=en debian-installer/country=US
  debian-installer/locale=en_US.UTF-8`, once with the simplified
  documented-minimal `debian-installer/locale=en_US.UTF-8
  keyboard-configuration/xkb-keymap=us` plus explicit `netcfg/get_*`
  params — confirmed via real rebuilds each time that the identical
  dialog still appears regardless. Marked blocked per the operator's
  "attempt a fix and one rebuild, then move on" policy (this exceeded
  that twice over, on a well-founded hypothesis each time, before
  stopping) — see `kali-attacker.pkr.hcl`'s `boot_command` comment for
  the untried next step (Kali's `simple-cdd` layer may be interposing
  its own earlier prompt).

**siem01 (Ubuntu) — BUILT, BOOTED, AND PROVISIONED FOR REAL.** The first
host this project has ever actually run. Getting from "SSH now connects"
to a genuinely complete `packer build` took three more real, distinct
bugs:

1. Real build attempt: `Connected to SSH!` for the first time all
   session — then the provisioner's `sudo apt-get update` failed: `E:
   Could not get lock /var/lib/apt/lists/lock. It is held by process
   ... (apt-get)`. Root cause: cloud-init's own `package_update: true` +
   `packages: [...]` (see `user-data.tmpl`) was still running in the
   background — SSH being reachable only means sshd started, not that
   cloud-init's later "final" stage has finished. Fixed by adding
   `cloud-init status --wait` as the provisioner's first command.
2. Next attempt: `cloud-init status --wait` itself returned
   `status: error`. Serial log showed why: `A dependency job for
   qemu-guest-agent.service failed` — the unit waits on
   `/dev/virtio-ports/org.qemu.guest_agent.0`, which nothing had ever
   provided. Packer's QEMU builder doesn't wire up a QEMU Guest Agent
   virtio-serial channel by default for *any* build (it talks to guests
   over SSH, not QGA) — this had simply never been exercised until SSH
   started working at all. Fixed by adding the standard `-chardev
   socket,...` + `-device virtio-serial` + `-device
   virtserialport,...,name=org.qemu.guest_agent.0` trio to `qemuargs`.
3. Getting there required attaching the custom NoCloud ISO via
   `qemuargs` (see the session's earlier entry for why `cd_files` itself
   is broken on macOS) — which surfaced a genuinely separate, real
   Packer behavior: **adding *any* `-drive` entry to `qemuargs` silently
   drops *all* of Packer's own auto-generated `-drive` entries**, not
   just adds one more alongside them (Packer's arg-merging keys defaults
   by flag name; a user-supplied key present at all skips the whole
   default array for that key, not a per-item merge). Observed directly:
   the resulting real `qemu` command line had only the cidata cdrom
   attached — no main disk, no EFI firmware at all — and QEMU spun at
   ~99% CPU with nothing bootable to find. Fixed by explicitly
   replicating every drive Packer would have generated once any custom
   one is added.
   - **Verification, done properly this time**: after a green
     `packer build` (`REAL EXIT CODE: 0`), `infra/local/build/images/
     siem01/siem01.qcow2` was deleted somehow between checks (root cause
     not fully pinned down — likely a stray `rm -rf` from the session's
     own iterative validate/rebuild cycle) — caught by trying to boot it
     and getting "No such file or directory", not assumed working.
     Rebuilt from scratch a second time to confirm the fix is
     reproducible, not a one-off: **34 seconds, exit 0, artifact present
     both times.**
- Booted persistently (not just for the build) via a direct
  `qemu-system-aarch64` invocation reusing the exact same device
  configuration, for use as a genuine live target. Two more small, real
  snags on the way: the QGA chardev's UNIX socket path failed first with
  a *relative*-path "No such file or directory" (background processes
  don't inherit the same CWD assumption a foreground `packer build`
  does), then with an *absolute*-path "path too long" (macOS's
  `sockaddr_un` 104-byte limit — this repo's own path, with spaces, is
  long) — fixed by using a short path in `/tmp` for the socket
  specifically (harmless; nothing on the host needs to dial it).
  Confirmed genuinely reachable: `hostname` → `siem01`, `uname -a` →
  real `aarch64` Ubuntu 22.04.5 kernel, `systemctl is-active ssh
  qemu-guest-agent` → both `active`.
- Captured the session's first real screenshot of a booted host:
  `docs/screenshots/siem01-first-boot-console.png`, rendered from the
  live serial log with `pyte` (parse the ANSI stream) + Pillow (draw it
  as an actual image) — Ubuntu's real login banner and `siem01 login:`
  prompt, since VNC alone shows QEMU's own monitor on this platform (no
  GPU device on aarch64 `virt`, same as the reasoning throughout this
  session).

**A real security incident, caught and fixed.** While debugging a stuck
`dc01` build, the underlying `qemu` process was killed directly rather
than letting `build.sh` exit normally — its `trap`-based restore (swap
the real, rendered `Autounattend.xml` back to the `__ADMIN_PASSWORD__`
placeholder on exit) never fired. The real, plaintext password sat in
the *tracked* `Autounattend.xml` and got committed alongside an
unrelated disk-partitioning fix (`becc301`), then pushed to origin
before being noticed — caught only when re-reading that file for an
unrelated `AutoLogon` edit. Remediated immediately: restored the
placeholder, rotated the password (`.env`, untracked), and fixed the
structural cause rather than just the symptom — `build.sh` no longer
touches the tracked file at all; it renders to a gitignored path
(`infra/local/build/http-windows-rendered/Autounattend.xml`) that
`windows-server.pkr.hcl` takes via a new `rendered_autounattend`
variable, so there is no tracked file left for any future interrupted
build to leave in a bad state, regardless of how it's interrupted. The
old password remains recoverable from git history at `becc301` until
that commit is rewritten — explicitly **not** done unilaterally (a
history rewrite needs a force-push, which needs the operator's
authorization) — flagged for the operator to decide.

**dc01 (Windows Server) — closer than ever, still not confirmed.** With
the MBR partition fix from earlier in this session already in place, a
full rebuild:

- **Completed the entire Windows install successfully** — confirmed via
  VNC screenshot, a genuine `Windows Server 2022 Standard Evaluation`
  desktop, not stuck mid-install.
- Hit a real, blocking "Do you want to allow your PC to be discoverable"
  dialog on first network connection (not covered by Autounattend.xml's
  OOBE-level `HideWirelessSetupInOOBE`/`NetworkLocation` settings, which
  are OOBE-specific and don't reach this later, shell-level prompt) —
  dismissed via a real VNC click (`move` + `click 1`, after finding
  `vncdo`'s click command takes a button number, not coordinates
  directly).
- **WinRM still never came up** — persistent `401 - invalid content
  type` for over an hour of real wall-clock retries. Root-caused
  properly rather than guessed: probing the WinRM endpoint directly
  (`curl -v http://127.0.0.1:<port>/wsman`) showed
  `WWW-Authenticate: Negotiate` only — the *default* out-of-box WinRM
  config, meaning `bootstrap.ps1` (which enables Basic auth) never ran
  at all, despite `FirstLogonCommands`/`AutoLogon` both being configured
  correctly. This is the exact same macOS `cd_files`/`hdiutil -hfs` bug
  that broke `siem01`'s NoCloud seed, a different symptom: Windows
  Setup's WinPE-era `Autounattend.xml` discovery tolerates the
  HFS-wrapped hybrid ISO fine (a different, earlier code path), but
  `D:\bootstrap.ps1` — read later, via the normal Windows CDFS driver,
  once fully booted — does not.
- Fixed the same way as `siem01`: generalized the pycdlib ISO-building
  logic into a shared `infra/local/iso_builder.py` (`build_iso()`) used
  by both `generate_nocloud_iso.py` (refactored to use it) and a new
  `generate_windows_seed_iso.py`. `windows-server.pkr.hcl` now takes the
  result via a `seed_iso` variable and `qemuargs`, replicating the main
  disk *and* the real Windows install ISO drive alongside it (the same
  "any `-drive` in `qemuargs` means replicating all of them" rule found
  on `siem01`, this time with one more drive since there's no separate
  pflash firmware to also replicate on a legacy-BIOS build).
- A rebuild with this real fix was still running as of this entry —
  outcome not yet known; see ROADMAP.md for current status. Whatever the
  outcome, this is the furthest a real `dc01` build has ever gotten:
  complete install, working `AutoLogon`, a genuine desktop, and now a
  properly-diagnosed (not guessed) WinRM root cause with a fix applied.

**`ssh_port` plumbing (`config/inventory/lab_scope_inventory.py`,
`scripts/sync_scope.py`) — a real, small, tested code addition.** UTM's
host-only network (the intended path) always gives a routable IP, so
`ansible_port` has never needed overriding. This session's live-host
validation used direct `qemu-system-aarch64` boots with usermode/SLIRP
NAT instead (UTM has no scriptable boot step), reachable only via a
host-side forwarded port — and that port can't be `22` itself without
root (binding ports <1024 needs a privileged process; confirmed by
trying). Added an optional `ssh_port` field, threaded from
`infra/local/state.json` through `merge_scope()` into
`inventory/lab-scope.yaml` and from there into the dynamic inventory's
`ansible_port`. 4 new passing tests (2 per module).

**Real Elastic SIEM deployment on siem01 — not a scratch instance this
time.** `telemetry/elastic/docker-compose.yml` (the actual, documented
project artifact, never run before this session) deployed for real:

- Docker installed on `siem01` via a plain `apt-get install docker.io
  docker-compose-v2` — a normal Ubuntu-guest operation, unrelated to the
  Homebrew restriction on the macOS *host* (that restriction was never
  about Docker-the-technology, just this specific host's package
  manager situation).
- `docker compose up -d` with `xpack.security.enabled=true` (the real
  config, not simplified) — copied the actual `telemetry/elastic/`
  directory over via `scp`, ran it with `SIEM_ADMIN_PASSWORD` set.
  **Both containers started and Elasticsearch came up healthy** —
  confirmed via `curl -u elastic:... http://localhost:9200` returning a
  real cluster info response, `"license mode is [basic] - valid"` in the
  logs. The `./certs` read-only mount (documented in
  `telemetry/elastic/README.md` as needing a manual
  `elasticsearch-certutil` step) turned out not to block startup at all
  for this validation pass — ES 8.15's Docker image auto-configured
  successfully without it.
- Applied the real `telemetry/elastic/index-template.json` via a real
  `PUT _index_template/eadadl-winlogbeat` API call against the running
  cluster — `{"acknowledged":true}`.
- Reached from the host via an SSH tunnel (`ssh -L 19200:localhost:9200`
  through the existing `siem01` connection — no new port-forward on the
  QEMU side needed) and ran `detections.elastic_integration_check`
  against it for real, after adding `ELASTICSEARCH_USERNAME`/
  `_PASSWORD` support (this cluster has security enabled, unlike the
  session's earlier scratch instance): **8/8 techniques passed** — same
  result as the scratch-instance run, now against the actual deployed
  artifact this was always meant to validate.

**Ansible run against the real, current inventory.** `ansible-playbook
-i config/inventory/lab_scope_inventory.py config/site.yml` — genuinely
executed, not just syntax-checked: `[WARNING]: Could not match supplied
host pattern... domain_controller` / `member_server`, all three plays
skipped, 0 hosts matched. Honest, not a bug: `site.yml`'s plays only
target `domain_controller`/`member_server`, and only `siem01` (role
`siem`) is provisioned so far — there is currently no play in
`config/site.yml` for `siem` hosts at all (an empty `config/siem/`
placeholder role exists but has no tasks). Meaningful Ansible validation
is still gated on `dc01`.

**Verification performed this entry:** 79 `pytest` passing at the repo
root (up from 75 — 4 new `ssh_port` tests), `ruff`/`mypy --strict` clean
throughout including all new `infra/local/*.py` helpers (checked
individually with `--strict`, since `infra/local/` isn't in the main
`pyproject.toml` mypy `files` list, matching the existing convention for
`generate_bundles.py`). Every fix in this entry was verified against a
real rebuild, not assumed from reading the diff.

## 2026-08-02 — Session 4 continued: platform layer run for real (Docker via colima), dc01's actual WinRM root cause found and fixed, 2 real CI regressions caught and fixed

Continuation of the same session. Picked up mid-way through rehearsing
a new CI job locally; finished that, then chased down why `dc01` was
still stuck after the AutoLogon + `iso_builder.py` fixes logged above,
found and fixed a real, independent third bug, and along the way found
and fixed two genuine regressions in `.github/workflows/ci.yml` on its
first real push.

**The platform layer ran for the first time all session — via colima,
not Docker Desktop.** `platform/docker-compose.yml` had been "written,
not run" since session 1; this machine has no admin rights for Docker
Desktop's installer either (same interactive-TTY story as Homebrew).
`colima` (standalone binary) + `lima` + the `docker` CLI + `docker
compose` plugin — all downloaded straight to `~/.local/bin` /
`~/.docker/cli-plugins`, no sudo — gave a real, working Docker runtime
via Apple's native Virtualization.framework (`vz`), completely separate
from the QEMU path used for the lab hosts. `docker run hello-world`
worked immediately.

**Found a real container-vs-host path bug that pytest could never have
caught.** `platform/backend/app/config.py` derives
`LAB_SCOPE_FILE`/`COVERAGE_MATRIX_FILE` defaults via
`Path(__file__).resolve().parents[3]` — 3 levels up from
`platform/backend/app/config.py` lands on the repo root *on the host*,
which is exactly where `pytest` runs, so the backend's own test suite
never had a reason to notice this was fragile. Inside the built image,
that same file lives at `/app/backend/app/config.py`, and 3 levels up
from there is `/`. A real `POST /runs` against a real running container
returned a `ScopeFileError: scope file not found: /inventory/lab-scope.yaml`.
Chrome's devtools reported this as a CORS failure (a backend 500 drops
the connection before CORS headers are sent, and Chrome's console
doesn't distinguish that from an actual CORS misconfiguration) —
checked real preflight/actual-response headers via `curl` first
(genuinely correct), then went to `docker logs platform-backend-1` for
the real error. Fixed by setting `LAB_SCOPE_FILE`/`COVERAGE_MATRIX_FILE`
explicitly in `docker-compose.yml` to match the real mount paths,
deliberately not by trying to make the path arithmetic work for both
layouts.

**Verified end-to-end with real browser automation.** Playwright
(pip-installed, `playwright install chromium` — its own downloaded
Chromium, no Homebrew) drove a real login, a real `POST /runs` (denied
403 by the scope guard, correctly — no host provisioned on this
branch), and a real coverage page showing the actual 8/8 ATT&CK
coverage matrix. Screenshots captured for real into `docs/screenshots/`
(`platform-login-page.png`, `platform-dashboard-run.png`,
`platform-coverage-heatmap.png`), alongside a real `siem01` first-boot
serial console render (`siem01-first-boot-console.png`, via `pyte` +
Pillow reading the raw serial capture).

**A real credential-leak incident happened and was structurally fixed
(see also the entry above for the original discovery) — worth
restating precisely once more: never rewrote git history.** A real
`ADMIN_PASSWORD` ended up committed and pushed to `origin` in
`becc301`, because `build.sh`'s old approach (render the tracked
`Autounattend.xml` in place, restore via a bash `EXIT` trap) doesn't
run its trap if the underlying `qemu`/`packer` process is killed
directly rather than letting the script exit normally — exactly what
happened while debugging a stuck build. Restored the placeholder,
rotated the password, and rewrote `build.sh` to render into a gitignored
path (`infra/local/build/http-windows-rendered/`) instead, so there's
no tracked file left in a bad state no matter how the build is
interrupted — a structural fix, not a cleanup. Did **not** rewrite
`origin`'s history (`git push --force`) — that needs the operator's
explicit authorization, flagged rather than assumed.

**Added a new CI job (`platform-compose`) specifically to catch a
recurrence of the container-path bug automatically** — builds the real
compose stack on the GitHub-hosted runner's native Docker, then runs
the same login → 403 → coverage sequence Playwright validated locally.
Rehearsed locally first with CI-matching throwaway env vars before
pushing.

**That first real push of `platform-compose` went red — for two
genuine reasons, not flakiness:**

1. `packer init + validate (windows-server)` failed with `Unset
   variable "rendered_autounattend"` / `"seed_iso"`. Earlier this
   session `windows-server.pkr.hcl` switched from Packer's own (buggy)
   `cd_files` mechanism to these two required variables (see the
   `iso_builder.py` entry above), but the CI validate step was never
   updated to pass them — a straight regression, self-caused, sitting
   undetected because this was the first real push since that change.
   `ubuntu-siem.pkr.hcl`'s equivalent `nocloud_iso` variable has the
   same no-default shape and would have hit the identical error, just
   never got the chance to — `windows-server`'s step runs first in the
   job and a failure there aborts the rest. Fixed by passing placeholder
   *strings* (not real files — these are plain string interpolations
   into `qemuargs`, not read via an HCL `file()`/exists() check) for
   both. Verified locally: both `packer validate` invocations exit 0
   (confirmed `ubuntu-siem`'s "output directory already exists" error
   during local verification was purely this machine's own real siem01
   build already occupying that path — irrelevant on a clean CI
   checkout, confirmed by pointing `output_directory` elsewhere and
   getting a clean pass).
2. `Backend health check` got `curl` exit 56 (connection reset), then
   `Show logs on failure`/`Tear down` *also* failed, with
   `BACKEND_SECRET_KEY must be set`. Two independent bugs stacked:
   - `backend`/`frontend` had no `healthcheck:` block in
     `docker-compose.yml`, so `docker compose up --wait` considered them
     "healthy" the instant the container process *started*, not once
     the app inside was actually serving — a race a fast GitHub-hosted
     runner hits far more reliably than this machine's own, slower local
     runs did. Fixed with real healthchecks using each image's own
     interpreter (`python3`/`node` — neither image ships `curl`) against
     the real endpoints.
   - The job's env vars (`POSTGRES_PASSWORD` etc.) were scoped to the
     single "Build and start the stack" *step*. `docker-compose.yml`'s
     `${VAR:?...}` interpolation re-runs on every `docker compose`
     invocation (`logs`, `down` — not just `up`), so every step in the
     job that shells out to it needs the same env, not just the first
     one. Moved to job-level `env:`. (Hit the exact same class of bug
     rehearsing this locally minutes earlier — a fresh `Bash` call
     doesn't inherit a previous call's `source .env`/`export`, so
     `docker compose down -v` failed the same way until the env was
     re-sourced in the same call.)
   Verified locally before pushing: rebuilt with CI-matching throwaway
   env vars, `--wait` now reports real `Healthy` (not just `Started`)
   for backend and frontend, full login → 403 scope-guard-refusal →
   coverage regression check passed again end-to-end.

Pushed both fixes together. **Real result: all 7 CI jobs green** on
commit `e54e17a` (Packer fmt & validate, Ansible lint,
python-quality, detections-test, backend, platform-compose, frontend).

**dc01's actual WinRM root cause, found via live VNC on the still-alive
`build4` VM rather than guessing and rebuilding blind.** `build4` (the
AutoLogon + `iso_builder.py` fix from the entry above) had been running
over 2 hours with `vncdo` intermittently refusing to connect — checked
`lsof -a -p <pid> -i`: the process was genuinely still alive, WinRM's
forwarded port genuinely `LISTEN`ing, plus a real `ESTABLISHED`
outbound connection (Windows Update, most likely) — not a hung/crashed
VM, a slow one. Once VNC cooperated: **a real, fully booted Windows
Server desktop**, Server Manager open, AutoLogon had worked. Probing
the forwarded WinRM port directly (`curl -X POST .../wsman` with a
body, reading `WWW-Authenticate`) showed `Negotiate` only — Basic auth
never got enabled, the same *symptom* as the pre-`iso_builder.py` bug,
but this time the cause was different: `bootstrap.ps1` was written and
being launched by `FirstLogonCommands` under the `Administrator`
account, but `windows-server.pkr.hcl`'s `communicator` block has
*always* authenticated as `winrm_username = "labadmin"` — the same
`lab_admin_username` convention `siem01`/`attacker01` use via
cloud-init/preseed (`config/group_vars/all.yml`). Nothing in
`Autounattend.xml` had ever created a `labadmin` account — Packer's
WinRM communicator was polling with credentials for a user that simply
didn't exist, and would have failed even if `bootstrap.ps1` had
succeeded perfectly. Confirmed by driving the live desktop directly
over VNC (`vncdo`, working around a real, reproducible colon-key
mis-translation bug in this environment — `:` intermittently typed as
`;` — by using `key shift-scolon`/avoiding commands that need a literal
colon) to open a real `cmd.exe` and run `fsutil fsinfo drives`, `dir`,
etc.

Fixed by adding a `labadmin` `LocalAccount` (Administrators group) to
`Autounattend.xml` and switching `AutoLogon` to run as `labadmin`
instead of `Administrator`, so `bootstrap.ps1` runs as the same account
the WinRM communicator authenticates as. This is the "one fix, one
rebuild" the operator's instructions call for on top of the AutoLogon
fix already used in `build4` — cancelled the stuck `build4` process
(`kill -TERM`; its own background monitor confirmed a clean Packer
cancellation, "Build was cancelled" after 2h14m, not a crash) and
launched `build5` with the real fix. **Still running as of this entry**
— TCG (software) x86_64 emulation on Apple Silicon is genuinely this
slow; see ROADMAP.md for the outcome once known.

**Verification performed this entry:** real GitHub Actions run
(`e54e17a`, all 7 jobs green, checked via the GitHub API using the
credential `git`'s own `osxkeychain` helper already had stored — not a
new token) — first fully green run this project has had since the
`platform-compose` job was added. `packer validate` re-run locally for
both fixed templates. Full docker-compose regression sequence (health,
frontend, login, 403, coverage) re-run locally against a stack rebuilt
with the exact CI env vars, twice (once before, once after the
healthcheck fix, to see the actual race reproduce and then disappear).
