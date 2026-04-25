# MARCXML (MARC21 slim) — Structural Reference

MARC 21 bibliographic records have two interchange serializations relevant to
this eval: ISO 2709 (defined throughout the Library of Congress
`loc-bibliographic-html/` corpus) and MARCXML using the MARC21 slim schema.
The LOC bibliographic HTML pages describe field semantics and are shared
between both serializations. This document describes the MARCXML slim
structural rules that govern the XML wire format itself; these rules are
normative for this eval's `inspect_marcxml` and `render_marcxml` actions.

## Namespace

Every MARCXML document exchanged by this tool uses the MARC21 slim namespace:

```
http://www.loc.gov/MARC21/slim
```

The namespace must be declared on the root element (via `xmlns=` or a bound
prefix). Documents that use a different namespace — or no namespace at all —
are not valid MARC21 slim documents and must be rejected by `inspect_marcxml`
as `invalid_record`. Rendered output from `render_marcxml` must declare this
exact namespace on the root element.

## Root elements

The root of a MARCXML document is either:

1. A `<record>` element — a single bibliographic record.
2. A `<collection>` element — a container that, for this eval's scope, must
   contain exactly one `<record>` child. Collections with zero or multiple
   records are rejected as `invalid_record`.

Any other root element is rejected as `invalid_record`.

## Record element structure

A `<record>` element contains:

1. At least one `<leader>` child (the first `<leader>` supplies the
   record's leader text).
2. Zero or more `<controlfield>` children.
3. Zero or more `<datafield>` children.

`<controlfield>` elements precede `<datafield>` elements. This ordering
mirrors the ISO 2709 directory rule in `bdintro.html`, which states that
variable control field entries appear before variable data field entries in
the record directory. A MARCXML record that has a `<controlfield>` appearing
after a `<datafield>` is rejected as `invalid_record`.

Unknown or unexpected elements inside `<record>` (elements other than
`<leader>`, `<controlfield>`, or `<datafield>` in the MARC21 slim namespace)
are rejected as `invalid_record`.

## Leader element

The `<leader>` element text is a 24-character MARC 21 leader. All leader
position rules from `bdleader.html` apply. On `inspect_marcxml`, the
evaluator-facing canonical JSON form normalizes positions 00-04 and 12-16 to
`00000` (see `technical-requirements-prompt.md`); on `render_marcxml`, the
emitted leader carries the same normalized template because MARCXML has no
base-address serialization.

## Controlfield elements

Each `<controlfield>` has:

- A required `tag` attribute whose value is a three-character numeric tag in
  the range `001`-`009`. The `tag` attribute rules follow `bdintro.html`'s
  variable-field tag definition.
- Text content that is the control-field value. Control-field text is treated
  as UTF-8 Unicode.

A `<controlfield>` with a tag outside `001`-`009` or a missing `tag`
attribute is rejected as `invalid_record`.

## Datafield elements

Each `<datafield>` has:

- A required `tag` attribute whose value is a three-character numeric tag in
  the range `010`-`999`.
- Two required indicator attributes named `ind1` and `ind2`. Each indicator
  is a single character. A space indicator is represented by the literal
  space character `" "`. A `<datafield>` missing either `ind1` or `ind2` is
  rejected as `invalid_record`.
- Zero or more `<subfield>` children. The children of a `<datafield>` must
  all be `<subfield>` elements in the MARC21 slim namespace. Any other child
  element (including unknown elements or nested `<datafield>` / `<leader>` /
  `<controlfield>`) causes the record to be rejected as `invalid_record`.

## Subfield elements

Each `<subfield>` has:

- A required `code` attribute whose value is a single lowercase ASCII letter
  or ASCII digit, as described in the MARC 21 subfield code conventions in
  `bdleader.html` (Subfield code count) and in each field's subfield
  definition page (`bd###.html`).
- Text content that is the subfield value, treated as UTF-8 Unicode.

A `<subfield>` missing a `code` attribute, or using a code outside the
allowed character class, is rejected as `invalid_record`.

## Relation to the bibliographic HTML corpus

MARCXML structural rules above govern only the XML wire format. Field-level
semantics — which tags exist, which indicator values each field permits,
which subfield codes each field permits, and repeatability — come from the
LOC bibliographic HTML pages in `loc-bibliographic-html/` and apply
identically to both ISO 2709 and MARCXML.
