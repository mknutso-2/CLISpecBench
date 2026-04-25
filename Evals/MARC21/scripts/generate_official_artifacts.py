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
_FIXED_RULES_OUTPUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "reference-implementation-py"
    / "generated"
    / "marc21_fixed_field_rules.json"
)
_PAGE_PATTERN = re.compile(r"^bd(\d{3})\.html$")
_REPEATABILITY_PATTERN = re.compile(r"^(\d{3})\s*-\s*(.*?)\s*\((NR|R)\)$")
_SUBFIELD_ENTRY_PATTERN = re.compile(r"^\$([0-9a-z])\s*-\s*(.*?)\((NR|R)\)$")
_SUBFIELD_FRAGMENT_PATTERN = re.compile(r"(?=\$[0-9a-z]\s*-)")
# Fixed-field rules below are curated from the checked-in LOC fixed-field pages.
# They cover unambiguous positional constraints that are not represented by the
# standard data-field table extractor.
_FIXED_RULES: dict[str, object] = {
    "leader": {
        "source": "bdleader.html",
        "length": 24,
        "positions": {
            "05": ["a", "c", "d", "n", "p"],
            "06": ["a", "c", "d", "e", "f", "g", "i", "j", "k", "m", "o", "p", "r", "t"],
            "07": ["a", "b", "c", "d", "i", "m", "s"],
            "08": ["#", "a"],
            "09": ["#", "a"],
            "10": ["2"],
            "11": ["2"],
            "17": ["#", "1", "2", "3", "4", "5", "7", "8", "u", "z"],
            "18": ["#", "a", "c", "i", "n", "u"],
            "19": ["#", "a", "b", "c"],
        },
        "entry_map": "4500",
    },
    "006": {
        "source": "bd006.html",
        "length": 18,
        "position_00": ["a", "c", "d", "e", "f", "g", "i", "j", "k", "m", "o", "p", "r", "s", "t"],
        "fill_disallowed_positions": [0],
    },
    "007": {
        "source": "bd007.html",
        "position_00": ["a", "c", "d", "f", "g", "h", "k", "m", "o", "q", "r", "s", "t", "v", "z"],
        "fill_disallowed_positions": [0],
        "category_lengths": {
            "a": {"minimum": 8, "maximum": 8},
            "c": {"minimum": 6, "maximum": 14},
            "d": {"minimum": 6, "maximum": 6},
            "f": {"minimum": 10, "maximum": 10},
            "g": {"minimum": 9, "maximum": 9},
            "h": {"minimum": 13, "maximum": 13},
            "k": {"minimum": 6, "maximum": 6},
            "m": {"minimum": 8, "maximum": 23},
            "o": {"minimum": 2, "maximum": 2},
            "q": {"minimum": 2, "maximum": 2},
            "r": {"minimum": 11, "maximum": 11},
            "s": {"minimum": 14, "maximum": 14},
            "t": {"minimum": 2, "maximum": 2},
            "v": {"minimum": 9, "maximum": 9},
            "z": {"minimum": 2, "maximum": 2},
        },
    },
    "008": {
        "source": "bd008.html",
        "length": 40,
        "fill_disallowed_positions": [0, 1, 2, 3, 4, 5],
        "date_entered_positions": [0, 1, 2, 3, 4, 5],
        "date_type_position_06": [
            "b",
            "c",
            "d",
            "e",
            "i",
            "k",
            "m",
            "n",
            "p",
            "q",
            "r",
            "s",
            "t",
            "u",
            "|",
        ],
        "position_code_tables": {
            "38": ["#", "d", "o", "r", "s", "x", "|"],
            "39": ["#", "c", "d", "u", "|"],
        },
    },
}


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


def _parse_indicator_label(text: str) -> list[str] | None:
    if " - " not in text:
        return None
    token = text.split(" - ", 1)[0].strip()
    if not token:
        return None
    return _expand_indicator_token(token)


def _indicator_values_from_cell(cell: ET.Element) -> tuple[list[str], bool]:
    values: list[str] = []
    saw_labeled_value = False
    for span in cell.findall(".//{*}span"):
        text = _collapse_whitespace(_text_content(span))
        if " - " not in text:
            continue
        saw_labeled_value = True
        parsed = _parse_indicator_label(text)
        if parsed is None:
            return [], False
        for expanded in parsed:
            if expanded not in values:
                values.append(expanded)
    return values, saw_labeled_value


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


def _iter_subfield_fragments(subfield_table: ET.Element) -> tuple[list[str], bool]:
    list_items = subfield_table.findall(".//{*}li")
    if list_items:
        fragments = [
            _collapse_whitespace(_text_content(item))
            for item in list_items
            if "$" in _collapse_whitespace(_text_content(item))
        ]
        return fragments, bool(fragments)

    fragments: list[str] = []
    for cell in subfield_table.findall(".//{*}td"):
        cell_text = _collapse_whitespace(_text_content(cell))
        if "$" not in cell_text:
            continue
        for fragment in _SUBFIELD_FRAGMENT_PATTERN.split(cell_text):
            cleaned = fragment.strip()
            if cleaned:
                fragments.append(cleaned)
    return fragments, bool(fragments)


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
        indicator_1, indicator_1_complete = _indicator_values_from_cell(indicator_cells[0])
        rule["indicator1_complete"] = indicator_1_complete
        if indicator_1:
            rule["indicator1"] = indicator_1
        indicator_2, indicator_2_complete = _indicator_values_from_cell(indicator_cells[1])
        rule["indicator2_complete"] = indicator_2_complete
        if indicator_2:
            rule["indicator2"] = indicator_2

    subfield_repeatability: dict[str, bool | None] = {}
    subfield_table = _find_subfield_summary_table(root)
    if subfield_table is not None:
        fragments, saw_subfields = _iter_subfield_fragments(subfield_table)
        subfields_complete = saw_subfields
        for fragment in fragments:
            match = _SUBFIELD_ENTRY_PATTERN.match(fragment)
            if match is None:
                subfields_complete = False
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
        rule["subfields_complete"] = subfields_complete
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


def build_artifacts() -> tuple[
    dict[str, dict[str, object]],
    dict[str, list[dict[str, str]]],
    dict[str, object],
]:
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

    return rules, examples, _FIXED_RULES


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rules, examples, fixed_rules = build_artifacts()
    _write_json(_RULES_OUTPUT_PATH, rules)
    _write_json(_EXAMPLES_OUTPUT_PATH, examples)
    _write_json(_FIXED_RULES_OUTPUT_PATH, fixed_rules)
    print(
        f"Wrote {len(rules)} field rules to {_RULES_OUTPUT_PATH} and "
        f"{len(examples)} example groups to {_EXAMPLES_OUTPUT_PATH} and "
        f"{len(fixed_rules)} fixed-field rule groups to {_FIXED_RULES_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
