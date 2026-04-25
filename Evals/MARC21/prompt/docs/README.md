# MARC21 Docs Provenance

This folder contains a local mirror of the official Library of Congress MARC 21
bibliographic HTML corpus plus a local stitched convenience mirror, and a
maintainer-authored MARCXML slim structural reference.

- Source root: `https://www.loc.gov/marc/bibliographic/`
- Retrieved: `2026-04-22`
- Local mirror directory: `loc-bibliographic-html/`
- Convenience stitched file: `MARC21_Bibliographic_Full_Stitched.html`
- MARCXML slim structural reference: `MARCXML_Slim.md`

An official one-file download for the current full bibliographic format was not
found during retrieval. The Library of Congress MARC documentation page
advertises PDF downloads for the concise 2012 formats, while the current full
bibliographic format is published as HTML. The stitched HTML file is a local
convenience artifact built from the mirrored official pages; the authoritative
source text is the mirrored Library of Congress HTML corpus.

The `MARCXML_Slim.md` document describes the MARC21 slim XML wire format
(namespace, element ordering, required attributes, and allowed child
elements). Field-level semantics come from the mirrored bibliographic HTML
pages and apply to both ISO 2709 and MARCXML.
