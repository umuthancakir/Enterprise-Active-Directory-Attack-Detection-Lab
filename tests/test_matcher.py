"""Tests for detections/matcher.py — evaluating pySigma's parsed condition
tree (AND/OR/NOT, wildcards via |contains/|endswith, OR-lists under one
field) against plain event dicts.
"""

from __future__ import annotations

from sigma.rule import SigmaRule

from detections.matcher import rule_matches_event


def rule_from(detection_yaml: str) -> SigmaRule:
    return SigmaRule.from_yaml(
        f"""
title: Test rule
id: 00000000-0000-0000-0000-000000000000
status: test
logsource:
    category: test
detection:
{detection_yaml}
"""
    )


def test_simple_field_equality():
    rule = rule_from(
        """    selection:
        EventID: 4769
    condition: selection
"""
    )
    assert rule_matches_event(rule, {"EventID": "4769"})
    assert not rule_matches_event(rule, {"EventID": "4768"})


def test_and_across_multiple_fields_in_one_selection():
    rule = rule_from(
        """    selection:
        EventID: 4769
        TicketEncryptionType: '0x17'
    condition: selection
"""
    )
    assert rule_matches_event(rule, {"EventID": "4769", "TicketEncryptionType": "0x17"})
    assert not rule_matches_event(rule, {"EventID": "4769", "TicketEncryptionType": "0x12"})
    assert not rule_matches_event(rule, {"TicketEncryptionType": "0x17"})  # missing EventID


def test_or_list_under_one_field():
    rule = rule_from(
        """    selection:
        PipeName|contains:
            - efsrpc
            - lsarpc
    condition: selection
"""
    )
    assert rule_matches_event(rule, {"PipeName": "\\PIPE\\efsrpc"})
    assert rule_matches_event(rule, {"PipeName": "\\PIPE\\lsarpc"})
    assert not rule_matches_event(rule, {"PipeName": "\\PIPE\\spoolss"})


def test_and_not_filter_block():
    rule = rule_from(
        """    selection:
        EventID: 4769
    filter:
        ServiceName|endswith: '$'
    condition: selection and not filter
"""
    )
    assert rule_matches_event(rule, {"EventID": "4769", "ServiceName": "svc-sql"})
    assert not rule_matches_event(rule, {"EventID": "4769", "ServiceName": "MEM01$"})


def test_missing_field_never_matches():
    rule = rule_from(
        """    selection:
        SomeField: somevalue
    condition: selection
"""
    )
    assert not rule_matches_event(rule, {"OtherField": "somevalue"})
    assert not rule_matches_event(rule, {})


def test_number_field_matches_string_event_value():
    # Real Windows event log fields (and winlogbeat's rendering of them)
    # are strings even for numeric-looking values like EventID — the
    # matcher must compare a SigmaNumber against a string event value.
    rule = rule_from(
        """    selection:
        EventID: 4662
    condition: selection
"""
    )
    assert rule_matches_event(rule, {"EventID": "4662"})
    assert rule_matches_event(rule, {"EventID": 4662})
    assert not rule_matches_event(rule, {"EventID": "4663"})


def test_contains_modifier_wildcard():
    rule = rule_from(
        """    selection:
        ObjectName|contains: 'Domain-Backups'
    condition: selection
"""
    )
    matching = {"ObjectName": "CN=Domain-Backups,OU=LabUsers,DC=eadadl,DC=lab"}
    non_matching = {"ObjectName": "CN=HelpDesk-L1,OU=LabUsers,DC=eadadl,DC=lab"}
    assert rule_matches_event(rule, matching)
    assert not rule_matches_event(rule, non_matching)
