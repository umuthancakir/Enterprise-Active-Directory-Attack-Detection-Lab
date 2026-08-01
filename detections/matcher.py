"""Evaluate a parsed Sigma rule's condition tree against a single flat event dict.

Deliberately does NOT reimplement Sigma's condition language (AND/OR/NOT,
field modifiers, wildcards) — pySigma's own parser already does that
correctly, and re-deriving it by hand would be exactly the kind of
"looks right, subtly wrong" logic this project tries to avoid. This
module only supplies the one thing pySigma doesn't: comparing an already-
parsed Sigma value against a plain Python event dict's field value.
Everything else (AND/OR/NOT structure, `|contains`/`|endswith` modifiers
compiling down to wildcarded SigmaStrings, OR-lists under one field) is
pySigma's real, tested parse tree — see rule_matches_event()'s docstring.
"""

from __future__ import annotations

import fnmatch
from typing import Any

from sigma.conditions import (
    ConditionAND,
    ConditionFieldEqualsValueExpression,
    ConditionNOT,
    ConditionOR,
    ConditionValueExpression,
)
from sigma.rule import SigmaRule
from sigma.types import SigmaNumber, SigmaType


def _value_matches(sigma_value: SigmaType, event_value: Any) -> bool:
    if event_value is None:
        return False
    if isinstance(sigma_value, SigmaNumber):
        try:
            return int(event_value) == sigma_value.number
        except (TypeError, ValueError):
            return str(event_value) == str(sigma_value.number)
    # SigmaString, including modifier-derived wildcards (|contains, |endswith,
    # etc. all compile down to a wildcarded SigmaString at this point) —
    # str(sigma_value) renders it in fnmatch-compatible '*'/'?' syntax.
    return fnmatch.fnmatch(str(event_value), str(sigma_value))


def _eval_node(node: Any, event: dict[str, Any]) -> bool:
    if isinstance(node, ConditionAND):
        return all(_eval_node(arg, event) for arg in node.args)
    if isinstance(node, ConditionOR):
        return any(_eval_node(arg, event) for arg in node.args)
    if isinstance(node, ConditionNOT):
        return not _eval_node(node.args[0], event)
    if isinstance(node, ConditionFieldEqualsValueExpression):
        return _value_matches(node.value, event.get(node.field))
    if isinstance(node, ConditionValueExpression):
        # Fieldless "keyword" match — not used by any rule in
        # detections/sigma/ today, handled for completeness.
        return any(_value_matches(node.value, v) for v in event.values())
    raise TypeError(f"Unsupported Sigma condition node type: {type(node)!r}")


def rule_matches_event(rule: SigmaRule, event: dict[str, Any]) -> bool:
    """True if `event` satisfies any of `rule`'s condition expressions.

    A rule with multiple `condition:` entries has each evaluated
    independently and OR'd together, per Sigma semantics (matches ANY
    listed condition, not all of them).
    """
    return any(
        _eval_node(parsed_condition.parsed, event)
        for parsed_condition in rule.detection.parsed_condition
    )
