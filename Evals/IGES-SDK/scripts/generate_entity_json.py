"""One-shot generator: walk Evals/IGES-SDK/src/entities/*.hpp and emit
to_json / from_json ADL overloads for every struct they define.

Emits a single `entity_json.hpp` (inline overloads). Kept here under
IGES-SDK/scripts/ so the ref-impl carries only the generated output.

Run:
    python Evals/IGES-SDK/scripts/generate_entity_json.py \
        > Evals/IGES/reference-implementation-cpp/src/json/entity_json.hpp

The output path is intentional: the ref-impl compiles the generated
header, not this script.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ENTITIES_DIR = Path(__file__).resolve().parents[1] / "src" / "entities"
EXCLUDE = {"entity.hpp"}  # base header, not an entity

# Match `struct Name { ... };` (supports one nesting level inside the body)
STRUCT_RE = re.compile(
    r"struct\s+(\w+)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*;", re.DOTALL
)

# One field declaration inside a struct body.
# Accepts trailing `= default_expr` and optional `// comment`.
FIELD_RE = re.compile(
    r"^\s*(?P<type>(?:(?!//|\breturn\b)[\w:<>&,\s])+?)\s+"
    r"(?P<name>[a-zA-Z_]\w*)"
    r"(?:\s*=\s*[^;]+)?"
    r"\s*;(?:\s*//\s*(?P<comment>.*))?$",
)

# C-style fixed array: `Type name[N] = {...};` or `Type name[N];`
ARRAY_FIELD_RE = re.compile(
    r"^\s*(?P<type>[\w:<>&,\s]+?)\s+"
    r"(?P<name>[a-zA-Z_]\w*)"
    r"\s*\[\s*(?P<size>\d+)\s*\]"
    r"(?:\s*=\s*[^;]+)?"
    r"\s*;(?:\s*//.*)?$",
)


def extract_fields(body: str) -> list[tuple[str, str, int]]:
    """Return [(type, name, array_size), ...] for plain data members.

    `array_size` is 0 for non-array fields, or N for `Type name[N]`.
    """
    fields: list[tuple[str, str, int]] = []
    for raw in body.splitlines():
        line = raw.rstrip()
        code, _, _ = line.partition("//")
        code = code.strip()
        if not code:
            continue
        if code.startswith(("using ", "constexpr ", "auto ", "return ")):
            continue
        if "operator" in code:
            continue
        # Method declarations / definitions
        if "(" in code and ")" in code:
            continue
        if not code.endswith(";"):
            continue
        # A field can have `= {}` default-init braces — don't reject those.
        # But a bare `{` or `}` on its own is structural (nested scope).
        # We detect structural braces by seeing whether they come before `=`.
        eq_idx = code.find("=")
        check_region = code if eq_idx < 0 else code[:eq_idx]
        if "{" in check_region or "}" in check_region:
            continue

        # Try fixed-array pattern first (has `[N]`)
        am = ARRAY_FIELD_RE.match(line)
        if am:
            cpp_type = re.sub(r"\s+", " ", am.group("type")).strip()
            cpp_type = re.sub(r"\bconst\b|\bmutable\b|&", "", cpp_type).strip()
            fields.append((cpp_type, am.group("name"), int(am.group("size"))))
            continue

        m = FIELD_RE.match(line)
        if not m:
            continue
        cpp_type = re.sub(r"\s+", " ", m.group("type")).strip()
        if cpp_type in {"return", "static", "friend"}:
            continue
        cpp_type = re.sub(r"\bconst\b|\bmutable\b|&", "", cpp_type).strip()
        fields.append((cpp_type, m.group("name"), 0))
    return fields


def extract_structs(source: str) -> list[tuple[str, list[tuple[str, str, int]]]]:
    """Return [(struct_name, fields)] in source order."""
    out: list[tuple[str, list[tuple[str, str, int]]]] = []
    for m in STRUCT_RE.finditer(source):
        out.append((m.group(1), extract_fields(m.group(2))))
    return out


def render_to_json(name: str, fields: list[tuple[str, str, int]]) -> str:
    lines = [f"inline void to_json(nlohmann::json& j, {name} const& o) {{"]
    if not fields:
        lines.append("    (void)o;")
        lines.append("    j = nlohmann::json::object();")
        lines.append("}")
        return "\n".join(lines)
    lines.append("    j = nlohmann::json::object();")
    for _, fname, size in fields:
        if size > 0:
            # Fixed-size C array → JSON array
            lines.append(f'    {{ auto a = nlohmann::json::array();')
            lines.append(f"      for (int i = 0; i < {size}; ++i) a.push_back(o.{fname}[i]);")
            lines.append(f'      j["{fname}"] = std::move(a); }}')
        else:
            lines.append(f'    j["{fname}"] = o.{fname};')
    lines.append("}")
    return "\n".join(lines)


def render_from_json(name: str, fields: list[tuple[str, str, int]]) -> str:
    lines = [f"inline void from_json(nlohmann::json const& j, {name}& o) {{"]
    if not fields:
        lines.append("    (void)j; (void)o;")
        lines.append("}")
        return "\n".join(lines)
    for _, fname, size in fields:
        if size > 0:
            lines.append(f'    {{ auto const& a = j.at("{fname}");')
            lines.append(f'      if (!a.is_array() || a.size() != {size})')
            lines.append(f'          throw nlohmann::json::type_error::create(302, "{name}.{fname} expects {size}-element array", &a);')
            lines.append(f"      for (int i = 0; i < {size}; ++i) a.at(i).get_to(o.{fname}[i]); }}")
        else:
            lines.append(f'    j.at("{fname}").get_to(o.{fname});')
    lines.append("}")
    return "\n".join(lines)


# Map entity .hpp filename → list of other entity headers that must be
# included (for entities whose nested structs reference another entity).
# Empty by default; the ref-impl includes entity_writer.hpp's transitive
# closure, so just including the per-entity header is enough.


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    # Emit header preamble
    out: list[str] = [
        "#pragma once",
        "// AUTO-GENERATED by Evals/IGES-SDK/scripts/generate_entity_json.py",
        "// Do not edit by hand — regenerate after changing any entity struct.",
        "",
        '#include "core_json.hpp"',
    ]

    paths = sorted(ENTITIES_DIR.glob("*.hpp"))
    paths = [p for p in paths if p.name not in EXCLUDE]

    # Include every entity header so the ADL overloads can see the types.
    for p in paths:
        out.append(f'#include "../entities/{p.name}"')

    out.append("#include <nlohmann/json.hpp>")
    out.append("")
    out.append("namespace iges {")
    out.append("")

    total_structs = 0
    for p in paths:
        source = p.read_text(encoding="utf-8")
        structs = extract_structs(source)
        if not structs:
            print(f"WARN: no structs found in {p.name}", file=sys.stderr)
            continue
        out.append(f"// ── {p.name} ──")
        for name, fields in structs:
            out.append(render_to_json(name, fields))
            out.append(render_from_json(name, fields))
            out.append("")
            total_structs += 1

    out.append("} // namespace iges")

    sys.stdout.write("\n".join(out))
    print(f"\n\n// generated {total_structs} struct serializers", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
