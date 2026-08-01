"""Prove detections/sigma/ rules fire real hits against a real Elasticsearch cluster.

Usage: `python3 -m detections.elastic_integration_check` (needs a reachable
cluster — see ELASTICSEARCH_URL below).

This is deliberately NOT part of `make detections-test` / the default
pytest suite (tests/test_elastic_backend.py covers the pure conversion
half there, always). A live Elasticsearch cluster is not something CI
runners have, and this project's established pattern (see
detections/test_runner.py's docstring re: sigma-cli) is to keep anything
that needs live network/service access out of the default test run rather
than let it fail or silently skip in CI. This script is the genuinely
live-tested counterpart, for a human to run by hand against a real
cluster — whether that's telemetry/elastic/docker-compose.yml on a real
siem01, or (as first validated in BUILD_LOG.md session 4) a bare
`elasticsearch` tarball run locally with no Docker at all.

For each technique with both a Sigma rule and fixtures:
  1. Convert the rule to a Lucene query (detections.elastic_backend).
  2. Index its fixture events (matching + non_matching) into a throwaway
     index, refresh, then delete the index when done (self-cleaning, safe
     to run repeatedly against a shared cluster).
  3. Run the Lucene query via ES's query_string search.
  4. Assert every "matching" event's _id is a hit and every
     "non_matching" event's _id is not — same fixture data and same
     pass/fail semantics as detections.matcher's abstract check, but
     proven against Elasticsearch's actual query engine this time.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

from elasticsearch import Elasticsearch

from attack.techniques import TECHNIQUES
from detections.elastic_backend import convert_rule_to_lucene

SIGMA_DIR = Path(__file__).resolve().parent / "sigma"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_PREFIX = "eadadl-detections-check"

# Every event field here is a short, exact-value Windows Security log field
# (ObjectName, TargetUserName, PreAuthType, ...), not prose — so it needs
# to be mapped `keyword`, not ES's dynamic default of `text` (full-text
# analyzed) with a separate `.keyword` subfield. Left at the default, a
# wildcard query like `ObjectName:*Domain\-Backups*` silently fails to
# match, because the standard analyzer tokenizes "Domain-Backups" into
# two separate terms ("domain", "backups") and a single wildcard pattern
# can't span both — caught by actually running this against a real
# cluster, not by the abstract matcher in detections/matcher.py, which
# has no analyzer to disagree with (see BUILD_LOG.md session 4). This
# mapping is deliberately the same assumption the real deployment relies
# on too: telemetry/elastic/index-template.json extends winlogbeat's own
# default template, which maps `winlog.event_data.*` fields as `keyword`
# for exactly this reason — this test index just applies that same rule
# directly to this project's flat (non-ECS-nested) field names.
KEYWORD_MAPPING = {
    "dynamic_templates": [
        {"strings_as_keywords": {"match_mapping_type": "string", "mapping": {"type": "keyword"}}}
    ]
}


def _index_fixtures(
    es: Elasticsearch, index: str, events: list[dict[str, Any]], id_prefix: str
) -> list[str]:
    ids = []
    for i, event in enumerate(events):
        doc = {k: v for k, v in event.items() if not k.startswith("_")}
        doc_id = f"{id_prefix}-{i}"
        es.index(index=index, id=doc_id, document=doc)
        ids.append(doc_id)
    return ids


def check_technique(es: Elasticsearch, technique_id: str) -> tuple[bool, str]:
    rule_path = SIGMA_DIR / f"{technique_id}.yml"
    fixture_path = FIXTURES_DIR / f"{technique_id}.json"
    if not rule_path.exists() or not fixture_path.exists():
        return True, "skipped (no rule or fixtures)"

    queries = convert_rule_to_lucene(rule_path.read_text())
    fixtures = json.loads(fixture_path.read_text())
    matching_events = fixtures.get("matching", [])
    non_matching_events = fixtures.get("non_matching", [])

    index = f"{INDEX_PREFIX}-{technique_id}-{uuid.uuid4().hex[:8]}"
    try:
        es.indices.create(index=index, mappings=KEYWORD_MAPPING)
        matching_ids = _index_fixtures(es, index, matching_events, "m")
        non_matching_ids = _index_fixtures(es, index, non_matching_events, "nm")
        es.indices.refresh(index=index)

        hit_ids: set[str] = set()
        for query in queries:
            result = es.search(
                index=index,
                query={"query_string": {"query": query}},
                size=1000,
            )
            hit_ids |= {hit["_id"] for hit in result["hits"]["hits"]}

        missed_matches = [i for i in matching_ids if i not in hit_ids]
        false_positives = [i for i in non_matching_ids if i in hit_ids]

        if missed_matches or false_positives:
            return False, (
                f"missed {len(missed_matches)}/{len(matching_ids)} matching, "
                f"{len(false_positives)}/{len(non_matching_ids)} non_matching false-fired"
            )
        return True, (
            f"OK — {len(matching_ids)} matching hit, "
            f"{len(non_matching_ids)} non_matching correctly not hit"
        )
    finally:
        es.indices.delete(index=index, ignore_unavailable=True)


def main() -> int:
    es = Elasticsearch(ELASTICSEARCH_URL)
    try:
        info = es.info()
    except Exception as exc:  # noqa: BLE001 — reporting connectivity failure, not handling it
        print(
            f"Cannot reach Elasticsearch at {ELASTICSEARCH_URL}: {exc}\n"
            "Set ELASTICSEARCH_URL or start a cluster — see telemetry/elastic/README.md.",
            file=sys.stderr,
        )
        return 1

    print(f"Connected to Elasticsearch {info['version']['number']} at {ELASTICSEARCH_URL}\n")

    had_error = False
    for technique in TECHNIQUES.values():
        ok, message = check_technique(es, technique.id)
        status = "OK" if ok else "FAIL"
        print(f"[{technique.id}] {status} — {message}")
        if not ok:
            had_error = True

    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
