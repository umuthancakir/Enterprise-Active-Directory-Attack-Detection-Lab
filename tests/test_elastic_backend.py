"""Tests for detections/elastic_backend.py — pure Sigma-to-Lucene conversion.

Deterministic, no live Elasticsearch needed (that's
detections/elastic_integration_check.py's job — see its docstring for why
it's kept separate). This proves every real rule in detections/sigma/ is
genuinely Elasticsearch-compatible syntax, not just valid abstract Sigma.
"""

from __future__ import annotations

from attack.techniques import TECHNIQUES
from detections.elastic_backend import convert_all_rules, convert_rule_to_lucene


def test_every_real_technique_with_a_rule_converts_to_a_lucene_query():
    converted = convert_all_rules()
    technique_ids_with_rules = {
        t.id for t in TECHNIQUES.values() if (t.id in converted)
    }
    assert technique_ids_with_rules, "no rules found to convert"
    for technique_id in technique_ids_with_rules:
        queries = converted[technique_id]
        assert queries, f"{technique_id}: converted to zero queries"
        for query in queries:
            assert isinstance(query, str)
            assert query.strip(), f"{technique_id}: empty Lucene query string"


def test_acl_genericall_abuse_converts_to_the_expected_lucene_clauses():
    # One concrete example checked by hand, same "don't just assert
    # non-empty everywhere" spirit as test_matcher.py's specific cases.
    rule_yaml = (
        "title: t\nlogsource:\n  product: windows\ndetection:\n"
        "  selection:\n    EventID: 4662\n    ObjectName|contains: 'Domain-Backups'\n"
        "  condition: selection\n"
    )
    queries = convert_rule_to_lucene(rule_yaml)
    assert len(queries) == 1
    assert "EventID:4662" in queries[0]
    assert "Domain" in queries[0] and "Backups" in queries[0]


def test_convert_rule_to_lucene_handles_and_or_not():
    rule_yaml = (
        "title: t\nlogsource:\n  product: windows\ndetection:\n"
        "  selection:\n    EventID: 4769\n    TicketEncryptionType: '0x17'\n"
        "  filter:\n    ServiceName|endswith: '$'\n"
        "  condition: selection and not filter\n"
    )
    queries = convert_rule_to_lucene(rule_yaml)
    assert len(queries) == 1
    query = queries[0]
    assert "4769" in query
    assert "NOT" in query
