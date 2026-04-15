"""One-shot extraction script: walk Evals/IGES-SDK/src/entities/*.hpp and
emit TypeScript-style schema blocks for the technical-requirements-prompt
appendix.

Not part of the eval itself. Kept under IGES-SDK/scripts/ for reference
only; re-run by hand if the upstream entity headers change.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ENTITIES_DIR = Path(__file__).resolve().parents[1] / "src" / "entities"
EXCLUDE = {"entity.hpp"}  # base header, not an entity

# C++ → TS primitive type mapping
PRIMITIVE_MAP = {
    "int": "number",
    "Real": "number",
    "bool": "boolean",
    "char": "string",
    "std::string": "string",
    "Vec3": "Vec3",
    "Matrix3x3": "Matrix3x3",
    "DEIndex": "DEIndex",
    "Timestamp": "Timestamp",
    "LineFontVariant": "LineFontVariant",
    "LevelVariant": "LevelVariant",
    "ColorVariant": "ColorVariant",
    "Units": "Units",
    "SpecVersion": "SpecVersion",
    "DraftingStandard": "DraftingStandard",
    "StatusNumber": "StatusNumber",
    "AttributeValue": "number | string | DEIndex",
}


@dataclass
class Field:
    name: str
    ts_type: str
    comment: str


@dataclass
class Struct:
    name: str
    fields: list[Field]
    # Nested-struct dependencies that appear in this file above the main struct
    nested: list["Struct"]


@dataclass
class EntityInfo:
    filename: str
    type_number: int
    section: str
    summary: str
    form_dependent: bool
    main_struct: Struct
    nested_structs: list[Struct]


def map_cpp_to_ts(cpp_type: str) -> str:
    cpp_type = cpp_type.strip()

    # std::optional<T> → T | null
    m = re.fullmatch(r"std::optional<\s*(.+)\s*>", cpp_type)
    if m:
        return f"{map_cpp_to_ts(m.group(1))} | null"

    # std::vector<T> → T[]
    m = re.fullmatch(r"std::vector<\s*(.+)\s*>", cpp_type)
    if m:
        inner = map_cpp_to_ts(m.group(1))
        # Parenthesize unions
        if " | " in inner or inner.endswith("null"):
            return f"({inner})[]"
        return f"{inner}[]"

    # std::array<T, N> → [T, T, ..., T]
    m = re.fullmatch(r"std::array<\s*(.+?)\s*,\s*(\d+)\s*>", cpp_type)
    if m:
        inner = map_cpp_to_ts(m.group(1))
        n = int(m.group(2))
        return "[" + ", ".join([inner] * n) + "]"

    # std::variant<T1, T2, ...>
    m = re.fullmatch(r"std::variant<\s*(.+)\s*>", cpp_type)
    if m:
        parts = [map_cpp_to_ts(p) for p in split_template_args(m.group(1))]
        return " | ".join(parts)

    # primitive / known type
    return PRIMITIVE_MAP.get(cpp_type, cpp_type)


def split_template_args(args: str) -> list[str]:
    """Split 'A, B<C, D>, E' on top-level commas only."""
    out = []
    depth = 0
    current: list[str] = []
    for ch in args:
        if ch == "<":
            depth += 1
            current.append(ch)
        elif ch == ">":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        out.append("".join(current).strip())
    return out


# Match a struct definition: `struct Name { ... };`
STRUCT_RE = re.compile(r"struct\s+(\w+)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*;", re.DOTALL)

# Match one field declaration line inside a struct body.
# Captures: type, name, optional default-init, optional trailing comment.
# Type can contain <...>, ::, spaces.
FIELD_RE = re.compile(
    r"^\s*(?P<type>(?:(?!//|\breturn\b)[\w:<>&,\s])+?)\s+"
    r"(?P<name>[a-zA-Z_]\w*)"
    r"(?:\s*=\s*[^;]+)?"
    r"\s*;(?:\s*//\s*(?P<comment>.*))?$",
)


def extract_fields(body: str) -> list[Field]:
    fields: list[Field] = []
    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        # Strip trailing // comment for structural checks, but keep it for regex capture
        code_part, _, _ = line.partition("//")
        code_stripped = code_part.strip()
        if not code_stripped:
            continue
        if code_stripped.startswith(("using ", "constexpr ", "auto ", "return ")):
            continue
        if "operator" in code_stripped:
            continue
        # Skip method declarations (contain '(' before ';')
        if "(" in code_stripped and ")" in code_stripped:
            continue
        if "{" in code_stripped or "}" in code_stripped:
            continue
        if not code_stripped.endswith(";"):
            continue

        m = FIELD_RE.match(line)
        if not m:
            continue
        cpp_type = re.sub(r"\s+", " ", m.group("type")).strip()
        # Skip if the 'type' is really a C++ keyword like `return`
        if cpp_type in {"return", "static", "friend"}:
            continue
        # Drop leading `const`, references, `mutable`
        cpp_type = re.sub(r"\bconst\b|\bmutable\b|&", "", cpp_type).strip()
        ts_type = map_cpp_to_ts(cpp_type)
        comment = (m.group("comment") or "").strip()
        fields.append(Field(m.group("name"), ts_type, comment))
    return fields


def extract_structs(source: str) -> list[Struct]:
    """Return all `struct X { ... };` definitions in source order."""
    structs: list[Struct] = []
    for m in STRUCT_RE.finditer(source):
        name = m.group(1)
        body = m.group(2)
        fields = extract_fields(body)
        structs.append(Struct(name=name, fields=fields, nested=[]))
    return structs


# Header comment: "// iges::FooEntity — Type NNN" or "Types 100/110"
TYPE_LINE_RE = re.compile(r"//\s*iges::(\w+)Entity\s+[—-]\s+Type[s]?\s+([\d, /]+)")
SECTION_LINE_RE = re.compile(r"//\s*§([\d.]+):\s*\"(.+)\"")


def extract_header_info(source: str, filename: str) -> tuple[int, str, str, bool]:
    """Extract (primary_type_number, section, summary, form_dependent)."""
    type_num = 0
    section = ""
    summary = ""
    form_dependent = False

    m = TYPE_LINE_RE.search(source)
    if m:
        # Pick the first number from "100, 110" or "100/110"
        nums_str = m.group(2)
        nums = re.findall(r"\d+", nums_str)
        if nums:
            type_num = int(nums[0])

    m = SECTION_LINE_RE.search(source)
    if m:
        section = f"§{m.group(1)}"
        summary = m.group(2)

    # Form-dependency: does the parse function take `int form`?
    if re.search(r"parse_\w+_entity\s*\([^)]*\bint\s+form\b", source):
        form_dependent = True

    return type_num, section, summary, form_dependent


def load_entity(path: Path) -> EntityInfo | None:
    source = path.read_text(encoding="utf-8")
    type_num, section, summary, form_dependent = extract_header_info(source, path.name)
    structs = extract_structs(source)
    if not structs:
        return None
    # Main struct: the one whose name ends with "Entity"
    main = next((s for s in structs if s.name.endswith("Entity")), None)
    if main is None:
        return None
    nested = [s for s in structs if s is not main]
    return EntityInfo(
        filename=path.name,
        type_number=type_num,
        section=section,
        summary=summary,
        form_dependent=form_dependent,
        main_struct=main,
        nested_structs=nested,
    )


def render_struct(s: Struct, name_override: str | None = None) -> str:
    lines = [f"type {name_override or s.name} = {{"]
    for f in s.fields:
        comment_suffix = f"  // {f.comment}" if f.comment else ""
        lines.append(f"  {f.name}: {f.ts_type},{comment_suffix}")
    # Drop trailing comma on last field
    if lines[-1].endswith(","):
        # Replace only the first comma-before-comment or at EOL
        lines[-1] = re.sub(r",(\s*//|$)", r"\1", lines[-1], count=1)
    lines.append("};")
    return "\n".join(lines)


def render_entity(e: EntityInfo) -> str:
    lines: list[str] = []
    header = f"### Type {e.type_number} — {e.main_struct.name}"
    if e.section:
        header += f" ({e.section})"
    if e.form_dependent:
        header += " — form-dependent"
    lines.append(header)
    lines.append("")
    if e.summary:
        lines.append(f"> {e.summary}")
        lines.append("")
    lines.append("```ts")
    for nested in e.nested_structs:
        lines.append(render_struct(nested))
        lines.append("")
    # Emit the main struct as `<EntityName>Data`
    data_name = e.main_struct.name.removesuffix("Entity") + "Data"
    lines.append(render_struct(e.main_struct, name_override=data_name))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    # Force UTF-8 on stdout so em-dashes from header comments survive on Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    entities: list[EntityInfo] = []
    for path in sorted(ENTITIES_DIR.glob("*.hpp")):
        if path.name in EXCLUDE:
            continue
        info = load_entity(path)
        if info is None:
            print(f"WARN: no entity struct found in {path.name}", file=sys.stderr)
            continue
        entities.append(info)

    # Sort by IGES type number for a stable, spec-aligned appendix.
    entities.sort(key=lambda e: (e.type_number, e.main_struct.name))

    out = ["<!-- AUTO-GENERATED from Evals/IGES-SDK/src/entities/*.hpp -->",
           "<!-- See Evals/IGES-SDK/scripts/extract_entity_schemas.py -->",
           ""]
    for e in entities:
        out.append(render_entity(e))

    sys.stdout.write("\n".join(out))
    print(f"\n\n<!-- Rendered {len(entities)} entities -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
