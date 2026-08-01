# Baseline dashboard

`baseline-dashboard.ndjson` is a Kibana saved-objects export: an index
pattern (`winlogbeat-*`) + one visualization (event count by
`winlog.event_id`) + one dashboard. Import via Kibana's Stack Management >
Saved Objects > Import once `telemetry/elastic/` is running.

**This is the minimum viable "prove events land" artifact, not a real
detection dashboard** — Phase 4's Sigma-rule-driven coverage view is what
belongs in the eventual Phase 5 platform UI. This one panel answering
"is anything arriving at all" is deliberately all it does.

## Status — hand-authored, not exported from a running Kibana

Unlike most of this project's genuinely-tested artifacts, this NDJSON was
**hand-written**, not exported from a real Kibana instance (there is no
running Kibana to export from yet — see ROADMAP.md). Each line is
validated as syntactically correct JSON, but Kibana's saved-object schema
is version-specific (`migrationVersion` requirements, panel reference
formats) and this has not been import-tested. If it fails to import on a
real Kibana 8.15.x instance, that's expected until someone actually runs
`make platform`-adjacent telemetry setup and re-exports a working copy —
see [`baseline-queries.md`](baseline-queries.md) in this same directory
for the underlying raw queries, which are the more reliable "does this
work" check and don't depend on Kibana's export format at all.
