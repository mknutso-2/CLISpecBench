from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

_RULES_PATH = (
    Path(__file__).resolve().parents[1]
    / "reference-implementation-py"
    / "generated"
    / "marc21_field_rules.json"
)
_EXAMPLES_PATH = Path(__file__).resolve().parent / "generated" / "marc21_field_examples.json"
_LEADER_TEMPLATE = "00000nam a2200000 a 4500"


@lru_cache(maxsize=1)
def load_field_rules() -> dict[str, dict[str, Any]]:
    return json.loads(_RULES_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_field_examples() -> dict[str, list[dict[str, str]]]:
    return json.loads(_EXAMPLES_PATH.read_text(encoding="utf-8"))


def representative_example_records() -> list[tuple[str, dict[str, Any]]]:
    cases: list[tuple[str, dict[str, Any]]] = []
    for tag in sorted(load_field_examples()):
        example_text = try_roundtrippable_example_text(tag)
        if example_text is None:
            continue
        cases.append((tag, record_for_official_example(tag, example_text)))
    return cases


def data_field_example_records() -> list[tuple[str, dict[str, Any]]]:
    return [(tag, record) for tag, record in representative_example_records() if tag > "009"]


def fields_with_indicator_constraints() -> list[tuple[str, dict[str, Any]]]:
    rules = load_field_rules()
    return [
        (tag, rule)
        for tag, rule in sorted(rules.items())
        if tag > "009"
        and _rule_has_unambiguous_indicators(rule)
        and try_rule_compatible_example_text(tag) is not None
    ]


def fields_with_subfield_constraints() -> list[tuple[str, dict[str, Any]]]:
    rules = load_field_rules()
    return [
        (tag, rule)
        for tag, rule in sorted(rules.items())
        if tag > "009"
        and _rule_has_unambiguous_subfields(rule)
        and try_rule_compatible_example_text(tag) is not None
    ]


def fields_with_nonrepeatable_subfields() -> list[tuple[str, dict[str, Any]]]:
    rules = load_field_rules()
    return [
        (tag, rule)
        for tag, rule in sorted(rules.items())
        if tag > "009"
        and any(entry["repeatable"] is False for entry in rule.get("subfields", []))
        and _rule_has_unambiguous_subfields(rule)
        and try_rule_compatible_example_text(tag) is not None
    ]


def nonrepeatable_control_field_cases() -> list[tuple[str, dict[str, Any]]]:
    rules = load_field_rules()
    return [
        (tag, rule)
        for tag, rule in sorted(rules.items())
        if tag <= "009" and rule.get("repeatable") is False and tag in load_field_examples()
    ]


def nonrepeatable_data_field_cases() -> list[tuple[str, dict[str, Any]]]:
    rules = load_field_rules()
    return [
        (tag, rule)
        for tag, rule in sorted(rules.items())
        if tag > "009"
        and rule.get("repeatable") is False
        and try_rule_compatible_example_text(tag) is not None
    ]


def record_for_official_example(tag: str, example_text: str) -> dict[str, Any]:
    if tag <= "009":
        return {
            "leader_template": _LEADER_TEMPLATE,
            "control_fields": [{"tag": tag, "value": example_text}],
            "data_fields": [],
        }
    return {
        "leader_template": _LEADER_TEMPLATE,
        "control_fields": [{"tag": "001", "value": f"example-{tag}"}],
        "data_fields": [parse_data_field_example(tag, example_text)],
    }


def duplicate_nonrepeatable_field_record(tag: str) -> dict[str, Any]:
    example_text = (
        rule_compatible_example_text(tag) if tag > "009" else representative_example_text(tag)
    )
    record = record_for_official_example(tag, example_text)
    if tag <= "009":
        field = deepcopy(record["control_fields"][0])
        record["control_fields"] = [field, deepcopy(field)]
        return record
    field = deepcopy(record["data_fields"][0])
    record["data_fields"] = [field, deepcopy(field)]
    return record


def representative_example_text(tag: str) -> str:
    result = try_roundtrippable_example_text(tag)
    if result is None:
        raise KeyError(tag)
    return result


def try_parseable_example_text(tag: str) -> str | None:
    rows = load_field_examples().get(tag)
    if rows is None:
        return None
    if tag <= "009":
        return rows[0]["text"]
    for row in rows:
        text = row["text"]
        try:
            parse_data_field_example(tag, text)
        except ValueError:
            continue
        return text
    return None


def try_roundtrippable_example_text(tag: str) -> str | None:
    rows = load_field_examples().get(tag)
    if rows is None:
        return None
    if tag <= "009":
        return rows[0]["text"]
    rule = load_field_rules().get(tag)
    require_rule_match = isinstance(rule, dict) and (
        _rule_has_unambiguous_indicators(rule) or _rule_has_unambiguous_subfields(rule)
    )
    for row in rows:
        text = row["text"]
        try:
            field = parse_data_field_example(tag, text)
        except ValueError:
            continue
        if require_rule_match and rule is not None and not _matches_rule(field, rule):
            continue
        return text
    return None


def rule_compatible_example_text(tag: str) -> str:
    result = try_rule_compatible_example_text(tag)
    if result is None:
        raise KeyError(tag)
    return result


def try_rule_compatible_example_text(tag: str) -> str | None:
    rows = load_field_examples().get(tag)
    if rows is None:
        return None
    if tag <= "009":
        return rows[0]["text"]
    rule = load_field_rules()[tag]
    for row in rows:
        text = row["text"]
        try:
            field = parse_data_field_example(tag, text)
        except ValueError:
            continue
        if _matches_rule(field, rule):
            return text
    return None


def parse_data_field_example(tag: str, example_text: str) -> dict[str, Any]:
    if len(example_text) < 2:
        raise ValueError(f"Example for field {tag} is too short: {example_text!r}")
    indicators = [
        normalize_indicator_char(example_text[0]),
        normalize_indicator_char(example_text[1]),
    ]
    payload = example_text[2:]
    if not payload.startswith("$"):
        raise ValueError(
            f"Example for field {tag} does not start with a subfield: {example_text!r}"
        )
    subfields: list[dict[str, str]] = []
    cursor = 0
    while cursor < len(payload):
        if payload[cursor] != "$" or cursor + 1 >= len(payload):
            raise ValueError(f"Malformed subfield sequence in field {tag}: {example_text!r}")
        code = payload[cursor + 1]
        next_cursor = cursor + 2
        while next_cursor < len(payload) and payload[next_cursor] != "$":
            next_cursor += 1
        subfields.append({"code": code, "value": payload[cursor + 2 : next_cursor]})
        cursor = next_cursor
    return {
        "tag": tag,
        "indicators": indicators,
        "subfields": subfields,
    }


def _matches_rule(field: dict[str, Any], rule: dict[str, Any]) -> bool:
    indicator1 = rule.get("indicator1")
    indicator2 = rule.get("indicator2")
    if indicator1 and field["indicators"][0] not in {
        normalize_indicator_char(value) for value in indicator1
    }:
        return False
    if indicator2 and field["indicators"][1] not in {
        normalize_indicator_char(value) for value in indicator2
    }:
        return False
    allowed_subfields = {entry["code"]: entry["repeatable"] for entry in rule.get("subfields", [])}
    counts: dict[str, int] = {}
    if allowed_subfields:
        for subfield in field["subfields"]:
            code = subfield["code"]
            if code not in allowed_subfields:
                return False
            counts[code] = counts.get(code, 0) + 1
            if allowed_subfields[code] is False and counts[code] > 1:
                return False
    return True


def _rule_has_unambiguous_indicators(rule: dict[str, Any]) -> bool:
    has_constraint = False
    for key in ("indicator1", "indicator2"):
        raw_values = rule.get(key)
        if raw_values is None:
            continue
        if rule.get(f"{key}_complete") is not True:
            return False
        if not isinstance(raw_values, list) or not raw_values:
            return False
        values = cast(list[Any], raw_values)
        normalized: set[str] = set()
        for value in values:
            if not isinstance(value, str) or len(value) != 1:
                return False
            normalized.add(normalize_indicator_char(value))
        if len(normalized) != len(values):
            return False
        has_constraint = True
    return has_constraint


def _rule_has_unambiguous_subfields(rule: dict[str, Any]) -> bool:
    if rule.get("subfields_complete") is not True:
        return False
    raw_subfields = rule.get("subfields")
    if not isinstance(raw_subfields, list) or not raw_subfields:
        return False
    subfields = cast(list[Any], raw_subfields)
    seen: set[str] = set()
    for raw_entry in subfields:
        if not isinstance(raw_entry, dict):
            return False
        entry = cast(dict[str, Any], raw_entry)
        code = entry.get("code")
        repeatable = entry.get("repeatable")
        if not isinstance(code, str) or len(code) != 1:
            return False
        if code in seen:
            return False
        if repeatable not in {True, False}:
            return False
        seen.add(code)
    return True


def normalize_indicator_char(char: str) -> str:
    return " " if char == "#" else char


def invalid_indicator_for(tag: str, allowed: list[str] | None) -> str:
    options = [" ", "#", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "z", "|"]
    allowed_set = {normalize_indicator_char(value) for value in (allowed or [])}
    for candidate in options:
        normalized = normalize_indicator_char(candidate)
        if normalized not in allowed_set:
            return normalized
    raise ValueError(f"Could not find an invalid indicator for field {tag}")


def invalid_subfield_code_for(rule: dict[str, Any]) -> str:
    allowed_codes = {entry["code"] for entry in rule.get("subfields", [])}
    for candidate in ["x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
        if candidate not in allowed_codes:
            return candidate
    raise ValueError(f"Could not find an invalid subfield code for field {rule['tag']}")


def first_nonrepeatable_subfield_code(rule: dict[str, Any]) -> str:
    for entry in rule.get("subfields", []):
        if entry["repeatable"] is False:
            return str(entry["code"])
    raise ValueError(f"Field {rule['tag']} has no nonrepeatable subfield in generated rules")


def case_id(case: tuple[str, Any]) -> str:
    return case[0]
