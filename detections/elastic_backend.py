"""Convert this project's Sigma rules into real Elasticsearch/Lucene queries.

Uses pySigma's own Elasticsearch backend (pysigma-backend-elasticsearch) —
same "don't reimplement pySigma's logic by hand" principle as
detections/matcher.py. No pipeline is configured: every rule in
detections/sigma/ already uses raw Windows Security event log field names
(EventID, ObjectName, PreAuthType, ...), and those convert to Lucene query
clauses unchanged (verified for all 8 rules — see BUILD_LOG.md session 4).
A winlogbeat/ECS field-mapping pipeline would only be needed if the rules
or the target index used ECS-style dotted field names instead; they don't,
so adding one here would be unexercised complexity.

This module only does the pure, deterministic conversion (Sigma rule ->
Lucene query string) — no live Elasticsearch connection, safe to run
anywhere including CI. detections/elastic_integration_check.py is the
separate, live-cluster counterpart (see that module's docstring for why
it's kept out of the default test suite).
"""

from __future__ import annotations

from pathlib import Path

# The top-level sigma.backends.elasticsearch package doesn't re-export
# LuceneBackend in a way mypy can see (no py.typed re-export) — importing
# from the submodule directly is the same class, just a stricter import
# path for the type checker.
from sigma.backends.elasticsearch.elasticsearch_lucene import LuceneBackend
from sigma.collection import SigmaCollection

SIGMA_DIR = Path(__file__).resolve().parent / "sigma"


def convert_rule_to_lucene(rule_yaml: str) -> list[str]:
    """Return the Lucene query string(s) pySigma's ES backend derives from one rule.

    A rule with multiple `condition:` entries yields multiple queries
    (one per condition), mirroring detections.matcher.rule_matches_event's
    "matches ANY listed condition" semantics.
    """
    collection = SigmaCollection.from_yaml(rule_yaml)
    queries = LuceneBackend().convert(collection)
    return [str(query) for query in queries]


def convert_all_rules() -> dict[str, list[str]]:
    """Convert every rule in detections/sigma/ — technique_id -> Lucene queries."""
    return {
        path.stem: convert_rule_to_lucene(path.read_text())
        for path in sorted(SIGMA_DIR.glob("*.yml"))
    }
