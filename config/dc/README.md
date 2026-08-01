# config/dc

Promotes `dc01` to the lab's Active Directory forest, builds a synthetic OU/
user/group structure, and applies the deliberate misconfigurations from
[docs/vulnerabilities.md](../../docs/vulnerabilities.md) that live on the DC
(items 1, 2, 4, 6, 7 — item 3 is in `tasks/post_join_misconfigs.yml`, run
separately after `mem01` joins the domain; items 5 and 8 are deferred).

**STATUS: written, not run-tested.** There is no local WinRM-reachable
Windows target yet — `infra/local` hasn't been built (see
[ROADMAP.md](../../ROADMAP.md)). Review this role as a careful first draft,
the same caveat as the rest of this session's work.

## Task files

| File | Does |
|---|---|
| `tasks/main.yml` | Orchestrates the rest, in order |
| `tasks/promote_forest.yml` | AD DS + DNS feature install, forest promotion, points DC's own DNS at itself |
| `tasks/ou_structure.yml` | Creates `LabUsers`, `LabComputers`, `ServiceAccounts`, `HelpDesk` OUs |
| `tasks/users_and_groups.yml` | Synthetic population for recon realism (`config/dc/defaults/main.yml`'s `lab_users`/`lab_groups`) |
| `tasks/misconfigs.yml` | Misconfigs 1, 2, 4, 6, 7 |
| `tasks/post_join_misconfigs.yml` | Misconfig 3 — run from `site.yml` after `mem01` joins, not from `main.yml` |

## Running

```bash
set -a; source .env; set +a
ansible-playbook -i config/inventory/lab_scope_inventory.py config/site.yml --limit dc01
```

(`site.yml` handles the full dc → member → post-join-misconfigs ordering;
running this role alone via `--limit dc01` skips misconfig 3, which is
expected — see the ordering note in `tasks/post_join_misconfigs.yml`.)
