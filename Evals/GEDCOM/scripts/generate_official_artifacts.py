"""Generate maintainer-only GEDCOM artifacts from the official HTML corpus.

The authoritative spec that agents see lives in
`prompt/docs/FamilySearchGEDCOMv7.html`. This script derives helper artifacts for
the evaluator under `tests/generated/`; those files are not prompt-mounted.

`html.parser.HTMLParser` is used instead of `xml.etree.ElementTree` because the
mirrored FamilySearch HTML is not XML-clean enough for strict XML parsing.

The emitted GEDCOM code-block metadata includes a best-effort
`classification_hint`; treat it as triage help for test authors, not a
replacement for reading the surrounding official prose.
"""

import json
import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import cast

_DOC_PATH = Path(__file__).resolve().parents[1] / "prompt" / "docs" / "FamilySearchGEDCOMv7.html"
_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "tests" / "generated"
_NEGATIVE_HINT_PATTERN = re.compile(
    r"\b("
    r"not allowed|not legal|not valid|invalid|error|incorrect|wrong|"
    r"must not|shall not|forbidden|prohibited|deprecated"
    r")\b",
    re.IGNORECASE,
)
_CONTEXT_CLASS_PRIORITY = ("example", "note")
_VOID_TAGS = {"area", "base", "br", "col", "hr", "img", "input", "link", "meta", "source"}


def _new_parts() -> list[str]:
    return []


@dataclass(slots=True)
class _ElementContext:
    uid: int
    tag: str
    classes: set[str]
    attributes: dict[str, str]
    paragraphs: list[str] = field(default_factory=_new_parts)


@dataclass(slots=True)
class _ActiveBlock:
    kind: str
    source_block_id: str | None
    section_id: str | None
    context_classes: list[str]
    lead_text: str | None
    context_text: str | None
    parts: list[str] = field(default_factory=_new_parts)


def _normalize_text(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _starts_with_level_zero(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.startswith("0 ")
    return False


def _contains_line(text: str, prefix: str) -> bool:
    return any(line.lstrip().startswith(prefix) for line in text.splitlines())


def _classify_gedcom_block(text: str, context_classes: list[str], lead_text: str | None) -> str:
    if lead_text and _NEGATIVE_HINT_PATTERN.search(lead_text):
        return "counterexample"
    if "note" in context_classes:
        return "note"
    if _contains_line(text, "0 HEAD") and _contains_line(text, "0 TRLR"):
        return "dataset"
    if _starts_with_level_zero(text):
        return "record_fragment"
    return "substructure_fragment"


def _is_context_container(element: _ElementContext) -> bool:
    return element.tag == "div" and any(name in element.classes for name in _CONTEXT_CLASS_PRIORITY)


class _GedcomSpecParser(HTMLParser):
    def __init__(self) -> None:
        # The spec mirror encodes grammar tokens like &lt;&lt;HEADER&gt;&gt; inside
        # code blocks; convert_charrefs=True decodes them back to GEDCOM syntax.
        super().__init__(convert_charrefs=True)
        self.structures: dict[str, str] = {}
        self.examples: list[dict[str, object]] = []
        self._element_stack: list[_ElementContext] = []
        self._next_uid = 1
        self._current_h4_parts: list[str] | None = None
        self._current_paragraph_parts: list[str] | None = None
        self._current_pre_kind: str | None = None
        self._current_block: _ActiveBlock | None = None
        self._pending_structure_name: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value for name, value in attrs if value is not None}
        classes = set(attributes.get("class", "").split())
        if tag not in _VOID_TAGS:
            self._element_stack.append(
                _ElementContext(
                    uid=self._next_uid,
                    tag=tag,
                    classes=classes,
                    attributes=attributes,
                )
            )
        self._next_uid += 1

        if tag == "h4":
            self._current_h4_parts = []
        elif tag == "p":
            self._current_paragraph_parts = []
        elif tag == "pre":
            if "gedstruct" in classes:
                self._current_pre_kind = "gedstruct"
            elif "gedcom" in classes:
                self._current_pre_kind = "gedcom"
            else:
                self._current_pre_kind = None
        elif tag == "code" and self._current_pre_kind and self._current_pre_kind in classes:
            self._current_block = _ActiveBlock(
                kind=self._current_pre_kind,
                source_block_id=self._current_source_block_id(),
                section_id=self._current_section_id(),
                context_classes=self._current_context_classes(),
                lead_text=self._current_lead_text(),
                context_text=self._current_context_text(),
            )

    def handle_endtag(self, tag: str) -> None:
        if tag == "code" and self._current_block is not None:
            self._finalize_current_block()
        elif tag == "pre":
            self._current_pre_kind = None
        elif tag == "h4" and self._current_h4_parts is not None:
            heading_text = _collapse_whitespace("".join(self._current_h4_parts))
            self._current_h4_parts = None
            if heading_text.endswith(":="):
                if self._pending_structure_name is not None:
                    raise ValueError(
                        f"Structure heading {self._pending_structure_name!r} had no gedstruct block"
                    )
                self._pending_structure_name = heading_text[:-2].strip()
        elif tag == "p" and self._current_paragraph_parts is not None:
            paragraph_text = _collapse_whitespace("".join(self._current_paragraph_parts))
            self._current_paragraph_parts = None
            if paragraph_text:
                context = self._current_context_element()
                if context is not None:
                    context.paragraphs.append(paragraph_text)

        if tag not in _VOID_TAGS and self._element_stack:
            self._element_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._current_h4_parts is not None:
            self._current_h4_parts.append(data)
        if self._current_paragraph_parts is not None:
            self._current_paragraph_parts.append(data)
        if self._current_block is not None:
            self._current_block.parts.append(data)

    def finalize(self) -> tuple[dict[str, str], list[dict[str, object]]]:
        if self._pending_structure_name is not None:
            raise ValueError(
                f"Structure heading {self._pending_structure_name!r} had no gedstruct block"
            )
        return self.structures, self.examples

    def _finalize_current_block(self) -> None:
        if self._current_block is None:
            return

        block = self._current_block
        self._current_block = None
        text = _normalize_text("".join(block.parts))
        if not text:
            return

        if block.kind == "gedstruct":
            if self._pending_structure_name is None:
                return
            self.structures[self._pending_structure_name] = text
            self._pending_structure_name = None
            return

        starts_at_level_zero = _starts_with_level_zero(text)
        has_head = _contains_line(text, "0 HEAD")
        has_trlr = _contains_line(text, "0 TRLR")
        self.examples.append(
            {
                "text": text,
                "section_id": block.section_id,
                "source_block_id": block.source_block_id,
                "context_classes": block.context_classes,
                "lead_text": block.lead_text,
                "context_text": block.context_text,
                "classification_hint": _classify_gedcom_block(
                    text,
                    block.context_classes,
                    block.lead_text,
                ),
                "starts_at_level_zero": starts_at_level_zero,
                "has_head": has_head,
                "has_trlr": has_trlr,
                "is_full_dataset": starts_at_level_zero and has_head and has_trlr,
            }
        )

    def _current_section_id(self) -> str | None:
        for element in reversed(self._element_stack):
            if element.tag == "section":
                return element.attributes.get("id")
        return None

    def _current_context_element(self) -> _ElementContext | None:
        for element in reversed(self._element_stack):
            if _is_context_container(element):
                return element
        for element in reversed(self._element_stack):
            if element.tag == "section":
                return element
        return None

    def _current_context_classes(self) -> list[str]:
        context = self._current_context_element()
        if context is None:
            return []
        return [name for name in _CONTEXT_CLASS_PRIORITY if name in context.classes]

    def _current_lead_text(self) -> str | None:
        context = self._current_context_element()
        if context is None or not context.paragraphs:
            return None
        return context.paragraphs[-1]

    def _current_context_text(self) -> str | None:
        context = self._current_context_element()
        if context is None or not context.paragraphs:
            return None
        return "\n".join(context.paragraphs)

    def _current_source_block_id(self) -> str | None:
        for element in reversed(self._element_stack):
            if element.tag != "div":
                continue
            if "sourceCode" not in element.classes:
                continue
            return element.attributes.get("id")
        return None


def build_artifacts() -> tuple[dict[str, str], list[dict[str, object]]]:
    html = _DOC_PATH.read_text(encoding="utf-8")
    parser = _GedcomSpecParser()
    parser.feed(html)
    parser.close()
    structures, examples = parser.finalize()
    return structures, examples


def build_data_rules() -> dict[str, object]:
    html = _DOC_PATH.read_text(encoding="utf-8")
    return {
        "datatypes": {
            "Age": {
                "section_id": "age",
                "allows_empty": True,
                "grammar": "Age = [[ageBound D] ageDuration]",
            },
            "DateValue": {
                "section_id": "date",
                "allows_empty": True,
                "restrict_words": ["FROM", "TO", "BET", "AND", "BEF", "AFT", "ABT", "CAL", "EST"],
                "calendars": ["GREGORIAN", "JULIAN", "FRENCH_R", "HEBREW"],
            },
            "FilePath": {
                "section_id": "file-path",
                "local_forbidden_prefixes": ["/"],
                "local_forbidden_segments": [".."],
                "gedzip_reserved_names": ["gedcom.ged", "MANIFEST.MF", "META-INF/"],
                "supported_schemes": ["", "file", "ftp", "http", "https"],
            },
            "Language": {
                "section_id": "language",
                "source": "BCP 47 language tag",
            },
            "Latitude": {
                "section_id": "latitude",
                "hemispheres": ["N", "S"],
                "max_degrees": 90,
            },
            "Longitude": {
                "section_id": "longitude",
                "hemispheres": ["E", "W"],
                "max_degrees": 180,
            },
            "MediaType": {
                "section_id": "media-type",
                "source": "RFC 2045 section 5.1 plus HTTP-style parameters",
            },
            "TagDef": {
                "section_id": "tag-definition",
                "grammar": "TagDef = extTag D URI-reference",
            },
            "Time": {
                "section_id": "time",
                "utc_suffix": "Z",
                "allows_24_hour": False,
                "allows_leap_second": False,
            },
            "URI": {
                "section_id": "uri",
                "source": "RFC 3986 URI-reference",
            },
        },
        "enumerations": _extract_enum_sets(html),
        "gedzip": {
            "section_id": "gedzip",
            "format": "ZIP archive",
            "dataset_entry": "gedcom.ged",
            "file_extension": ".gdz",
            "entry_names_are_utf8_case_sensitive": True,
            "local_file_payloads_must_have_matching_entries": True,
            "zip_entry_names_are_not_percent_escaped": True,
        },
    }


def _extract_enum_sets(html: str) -> dict[str, list[str]]:
    enum_sets: dict[str, list[str]] = {}
    for match in re.finditer(
        r'<section id="enumset-([^"]+)"[^>]*>(.*?)(?=<section id="enumset-|<section id="gedzip")',
        html,
        flags=re.DOTALL,
    ):
        name = unescape(match.group(1))
        section_html = match.group(2)
        values: list[str] = []
        for row_match in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", section_html, flags=re.DOTALL):
            row_html = row_match.group(1)
            cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row_html, flags=re.DOTALL)
            if not cells:
                continue
            code_match = re.search(r"<code\b[^>]*>(.*?)</code>", cells[0], flags=re.DOTALL)
            if code_match is None:
                continue
            value = _collapse_whitespace(re.sub(r"<[^>]+>", "", unescape(code_match.group(1))))
            if value:
                values.append(value)
        enum_sets[name] = values
    return enum_sets


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    structures, examples = build_artifacts()
    data_rules = build_data_rules()
    enum_sets = cast(dict[str, object], data_rules["enumerations"])
    _write_json(_OUTPUT_DIR / "gedcom_structure_grammar.json", structures)
    _write_json(_OUTPUT_DIR / "gedcom_examples.json", examples)
    _write_json(_OUTPUT_DIR / "gedcom_data_rules.json", data_rules)
    print(
        "Wrote "
        f"{len(structures)} structure definitions, {len(examples)} GEDCOM code blocks, "
        f"and {len(enum_sets)} enum sets "
        f"to {_OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()
