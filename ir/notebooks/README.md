# Threat-hunting notebooks

`ad-purple-team-hunting.ipynb`: exploratory Elasticsearch queries, one
section per `attack/techniques.py` technique, deliberately **broader**
than the corresponding `detections/sigma/*.yml` rule (e.g. any non-AES
Kerberos ticket encryption, not just RC4; a wider named-pipe list for
coercion detection than just the two the Sigma rule matches). Each hunt
notes whether a Sigma rule already exists — the point of a hunt is to
catch what the precise, low-false-positive alerting rule doesn't, not to
duplicate it.

## Running

```bash
pip install jupyter elasticsearch
jupyter notebook ir/notebooks/ad-purple-team-hunting.ipynb
```

Requires `SIEM_ADMIN_PASSWORD` in the environment (`.env`) and a reachable
`telemetry/elastic/` cluster.

## Status

Built via `nbformat`'s Python API and validated with `nbformat.validate()`
— guarantees schema-correct notebook JSON, not hand-typed. **Not run**
against a real Elasticsearch cluster — no lab exists yet (see
`ROADMAP.md`). The Elasticsearch DSL queries follow the same field-naming
conventions as `telemetry/dashboards/baseline-queries.md`'s hand-checked
queries but haven't independently returned real results.
