# Baseline queries: proving events land

These are the actual "does telemetry work at all" checks — run them in
Kibana's Dev Tools (DSL) or the Discover search bar (KQL) against
`winlogbeat-*` once `telemetry/winlogbeat/` is shipping. More reliable
than a Kibana dashboard export across versions, and this is what
`baseline-dashboard.ndjson` in this directory visualizes — if these
queries return nothing, the dashboard won't show anything meaningful
either, so start here.

## 1. Anything landing at all in the last 15 minutes?

KQL (Discover):
```
_exists_:"@timestamp"
```
DSL:
```json
GET winlogbeat-*/_count
{
  "query": { "range": { "@timestamp": { "gte": "now-15m" } } }
}
```

## 2. Sysmon process creation events (event ID 1) landing?

KQL:
```
winlog.channel: "Microsoft-Windows-Sysmon/Operational" and winlog.event_id: "1"
```

## 3. Kerberoasting-relevant events (4769, RC4 encryption) landing?

DSL — this is the actual Sigma-rule-equivalent query for
`docs/vulnerabilities.md` item 1, useful to hand-verify before writing the
Phase 4 Sigma rule:
```json
GET winlogbeat-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "winlog.event_id": "4769" } },
        { "term": { "winlog.event_data.TicketEncryptionType": "0x17" } }
      ]
    }
  }
}
```

## 4. AS-REP roasting-relevant events (4768, missing pre-auth) landing?

```json
GET winlogbeat-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "winlog.event_id": "4768" } },
        { "term": { "winlog.event_data.PreAuthType": "0" } }
      ]
    }
  }
}
```

## 5. DCSync-relevant events (4662, replication rights GUIDs) landing?

```json
GET winlogbeat-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "winlog.event_id": "4662" } },
        {
          "bool": {
            "should": [
              { "wildcard": { "winlog.event_data.Properties": "*1131f6aa-9c07-11d1-f79f-00c04fc2dcd2*" } },
              { "wildcard": { "winlog.event_data.Properties": "*1131f6ad-9c07-11d1-f79f-00c04fc2dcd2*" } }
            ]
          }
        }
      ]
    }
  }
}
```

## 6. mem01's forwarded events reaching dc01's collector?

KQL:
```
winlog.channel: "ForwardedEvents" and host.name: "dc01*"
```
If this returns nothing but query 2 (dc01's own Sysmon) does, the WEF
subscription/GPO from `telemetry/wef/` is the thing to check — not
Elasticsearch or Winlogbeat.

## Status

Written as queries to run once telemetry exists; none have been run
against a real cluster yet (see ROADMAP.md). The field names
(`winlog.event_data.TicketEncryptionType`, etc.) match Winlogbeat's
standard ECS-adjacent field mapping for these event IDs — worth
double-checking against `GET winlogbeat-*/_mapping` once real data lands,
since exact field names have shifted across Winlogbeat versions.
