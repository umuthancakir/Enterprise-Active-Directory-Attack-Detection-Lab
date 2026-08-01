# SIEM: Elasticsearch + Kibana (default `SIEM_BACKEND`)

Single-node Elasticsearch + Kibana on `siem01`, sized for a lab. `.env.example`
defaults `SIEM_BACKEND=elastic`; Wazuh/Splunk remain documented-but-unbuilt
alternatives (the same "gated, not silently assumed" pattern as
`DEPLOY_TARGET`).

## Files

| File | Purpose |
|---|---|
| `docker-compose.yml` | Runs Elasticsearch + Kibana on `siem01` |
| `index-template.json` | Extends winlogbeat's default index template with this lab's custom fields (`eadadl.lab`, `eadadl.collector`) |

## Setup (currently manual — see "Not done" below)

```bash
# On siem01:
docker compose -f telemetry/elastic/docker-compose.yml up -d

# Generate a self-signed CA + cert for the single node (never leaves the
# isolated lab network — SECURITY.md #1):
docker exec eadadl-elasticsearch \
  bin/elasticsearch-certutil ca --out /usr/share/elasticsearch/config/certs/ca.p12 --pass ""

# Apply the index template (after auth is up):
curl -k -u elastic:$SIEM_ADMIN_PASSWORD \
  -X PUT "https://siem01.eadadl.lab:9200/_index_template/eadadl-winlogbeat" \
  -H "Content-Type: application/json" \
  -d @telemetry/elastic/index-template.json
```

Then point `telemetry/winlogbeat/winlogbeat.yml` (on `dc01`) at
`https://siem01.eadadl.lab:9200` with the CA cert copied over — see that
file's `output.elasticsearch` block.

## Status

Written, not run — no `siem01` host exists yet (see ROADMAP.md). Both
files are syntax-validated (`docker compose config`-equivalent YAML parse,
JSON parse) but not applied to a real Elasticsearch cluster.

## Not done / follow-up

- `config/siem/` Ansible role (installing Docker, running this compose
  file, generating certs) doesn't exist yet — everything above is a
  manual, documented procedure for now.
- Wazuh/Splunk alternate `SIEM_BACKEND` values are declared in
  `.env.example` but have no corresponding config here — only Elastic is
  built out.
