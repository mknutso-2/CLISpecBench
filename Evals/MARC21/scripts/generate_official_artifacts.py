from __future__ import annotations

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

_DOCS_DIR = Path(__file__).resolve().parents[1] / "prompt" / "docs" / "loc-bibliographic-html"
_EXAMPLES_OUTPUT_PATH = (
    Path(__file__).resolve().parents[1] / "tests" / "generated" / "marc21_field_examples.json"
)
_RULES_OUTPUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "reference-implementation-py"
    / "generated"
    / "marc21_field_rules.json"
)
_PAGE_PATTERN = re.compile(r"^bd(\d{3})\.html$")
_REPEATABILITY_PATTERN = re.compile(r"^(\d{3})\s*-\s*(.*?)\s*\((NR|R)\)$")
_INDICATOR_VALUE_PATTERN = re.compile(r"([#0-9A-Za-z](?:-[0-9A-Za-z])?)\s*-")
_SUBFIELD_ENTRY_PATTERN = re.compile(r"^\$([0-9a-z])\s*-\s*(.*?)\((NR|R)\)$")
_SUBFIELD_FRAGMENT_PATTERN = re.compile(r"(?=\$[0-9a-z]\s*-)")


def _text_content(element: ET.Element) -> str:
    return "".join(element.itertext())


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _expand_indicator_token(token: str) -> list[str]:
    if len(token) == 3 and token[1] == "-":
        start = token[0]
        end = token[2]
        if start.isdigit() and end.isdigit():
            return [str(value) for value in range(int(start), int(end) + 1)]
        if start.isalpha() and end.isalpha() and start <= end:
            return [chr(value) for value in range(ord(start), ord(end) + 1)]
    return [token]


def _indicator_values_from_cell(cell: ET.Element) -> list[str]:
    values: list[str] = []
    for token in _INDICATOR_VALUE_PATTERN.findall(_collapse_whitespace(_text_content(cell))):
        for expanded in _expand_indicator_token(token):
            if expanded not in values:
                values.append(expanded)
    return values


def _find_indicator_cells(root: ET.Element) -> tuple[ET.Element, ET.Element] | None:
    table = root.find(".//{*}table[@class='indicators']")
    if table is not None:
        rows = table.findall("{*}tr")
        if len(rows) >= 2:
            cells = rows[1].findall("{*}td")
            if len(cells) >= 2:
                return cells[0], cells[1]

    for candidate in root.findall(".//{*}table"):
        row = candidate.find("{*}tr")
        if row is None:
            continue
        cells = row.findall("{*}td")
        if len(cells) < 2:
            continue
        first_text = _collapse_whitespace(_text_content(cells[0]))
        second_text = _collapse_whitespace(_text_content(cells[1]))
        if "First Indicator" in first_text and "Second Indicator" in second_text:
            return cells[0], cells[1]
    return None


def _find_subfield_summary_table(root: ET.Element) -> ET.Element | None:
    table = root.find(".//{*}table[@class='subfields']")
    if table is not None:
        return table
    for candidate in root.findall(".//{*}table"):
        if "Subfield Codes" in _collapse_whitespace(_text_content(candidate)):
            return candidate
    return None


def _iter_subfield_fragments(subfield_table: ET.Element) -> list[str]:
    list_items = subfield_table.findall(".//{*}li")
    if list_items:
        return [_collapse_whitespace(_text_content(item)) for item in list_items]

    fragments: list[str] = []
    for cell in subfield_table.findall(".//{*}td"):
        cell_text = _collapse_whitespace(_text_content(cell))
        if "$" not in cell_text:
            continue
        for fragment in _SUBFIELD_FRAGMENT_PATTERN.split(cell_text):
            cleaned = fragment.strip()
            if cleaned:
                fragments.append(cleaned)
    return fragments


def _text_without_emphasis(element: ET.Element) -> str:
    parts: list[str] = []
    if element.text:
        parts.append(element.text)
    for child in list(element):
        local_name = child.tag.rsplit("}", 1)[-1]
        if local_name != "em":
            parts.append(_text_without_emphasis(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def _extract_rule(root: ET.Element, tag: str) -> dict[str, object]:
    h1 = root.find(".//{*}h1")
    if h1 is None:
        raise ValueError(f"{tag}: missing h1")
    h1_text = _collapse_whitespace(_text_content(h1))
    match = _REPEATABILITY_PATTERN.match(h1_text)
    if match is None:
        raise ValueError(f"{tag}: unexpected h1 format: {h1_text!r}")

    rule: dict[str, object] = {
        "tag": tag,
        "title": match.group(2),
        "repeatable": match.group(3) == "R",
    }

    indicator_cells = _find_indicator_cells(root)
    if indicator_cells is not None:
        indicator_1 = _indicator_values_from_cell(indicator_cells[0])
        if indicator_1:
            rule["indicator1"] = indicator_1
        indicator_2 = _indicator_values_from_cell(indicator_cells[1])
        if indicator_2:
            rule["indicator2"] = indicator_2

    subfield_repeatability: dict[str, bool | None] = {}
    subfield_table = _find_subfield_summary_table(root)
    if subfield_table is not None:
        for fragment in _iter_subfield_fragments(subfield_table):
            match = _SUBFIELD_ENTRY_PATTERN.match(fragment)
            if match is None:
                continue
            code = match.group(1)
            current = match.group(3) == "R"
            existing = subfield_repeatability.get(code)
            if existing is None and code in subfield_repeatability:
                continue
            if existing is None:
                subfield_repeatability[code] = current
            elif existing != current:
                subfield_repeatability[code] = None
    if subfield_repeatability:
        rule["subfields"] = [
            {"code": code, "repeatable": repeatable}
            for code, repeatable in subfield_repeatability.items()
        ]

    return rule


def _extract_examples(root: ET.Element, tag: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in root.findall(".//{*}div[@class='example']//{*}tr"):
        cells = row.findall("{*}td")
        if len(cells) < 2:
            continue
        row_tag = _collapse_whitespace(_text_content(cells[0]))
        if row_tag != tag:
            continue
        text = _collapse_whitespace(" ".join(_text_without_emphasis(cell) for cell in cells[1:]))
        if not text or text in seen:
            continue
        seen.add(text)
        rows.append({"text": text})
    return rows


def _parse_root(path: Path) -> ET.Element:
    try:
        return ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError as exc:
        raise ValueError(f"Could not parse {path.name} as XML-compatible HTML") from exc


def build_artifacts() -> tuple[dict[str, dict[str, object]], dict[str, list[dict[str, str]]]]:
    rules: dict[str, dict[str, object]] = {}
    examples: dict[str, list[dict[str, str]]] = {}

    for path in sorted(_DOCS_DIR.glob("bd[0-9][0-9][0-9].html")):
        match = _PAGE_PATTERN.match(path.name)
        if match is None:
            continue
        tag = match.group(1)
        root = _parse_root(path)
        rules[tag] = _extract_rule(root, tag)
        field_examples = _extract_examples(root, tag)
        if field_examples:
            examples[tag] = field_examples

    return rules, examples


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rules, examples = build_artifacts()
    _write_json(_RULES_OUTPUT_PATH, rules)
    _write_json(_EXAMPLES_OUTPUT_PATH, examples)
    print(
        f"Wrote {len(rules)} field rules to {_RULES_OUTPUT_PATH} and "
        f"{len(examples)} example groups to {_EXAMPLES_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
