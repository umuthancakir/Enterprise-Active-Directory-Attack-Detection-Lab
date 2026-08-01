# config/member

Domain-joins `mem01` into the lab forest. Misconfig 3 (unconstrained
Kerberos delegation) is applied afterward from `config/dc`, not here — see
`config/dc/tasks/post_join_misconfigs.yml` and `site.yml`.

**STATUS: written, not run-tested** — same caveat as `config/dc/README.md`.

```bash
set -a; source .env; set +a
ansible-playbook -i config/inventory/lab_scope_inventory.py config/site.yml
```

Run the full `site.yml`, not this role in isolation with `--limit mem01` —
domain join needs `dc01` already promoted (`hostvars['dc01']` is used
directly for DNS), and misconfig 3 needs this play to have already run.
