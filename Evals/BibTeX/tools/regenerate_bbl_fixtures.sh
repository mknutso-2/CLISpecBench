#!/usr/bin/env bash
# Regenerate the .expected.bbl fixtures for the BibTeX eval.
#
# Usage (from repo root OR from Evals/BibTeX/):
#   bash Evals/BibTeX/tools/regenerate_bbl_fixtures.sh          # uses host bibtex if present
#   bash Evals/BibTeX/tools/regenerate_bbl_fixtures.sh --docker # uses texlive/texlive image
#
# Writes .expected.bbl back into Evals/BibTeX/tests/fixtures/.
set -euo pipefail

# Script lives at Evals/BibTeX/tools/; the BibTeX eval root is two levels up.
EVAL_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
FIXTURES_DIR="$EVAL_ROOT/tests/fixtures"
STYLES_DIR="$EVAL_ROOT/prompt/docs/authoritative"
STYLES=(plain alpha unsrt abbrv)

USE_DOCKER=0
if [[ "${1:-}" == "--docker" ]]; then
    USE_DOCKER=1
fi

if [[ ! -d "$FIXTURES_DIR" ]]; then
    echo "error: fixtures dir missing: $FIXTURES_DIR" >&2
    exit 1
fi
if [[ ! -f "$FIXTURES_DIR/refs.bib" ]]; then
    echo "error: refs.bib missing from $FIXTURES_DIR" >&2
    exit 1
fi

run_bibtex_host() {
    local tmp="$1"
    local style="$2"
    (cd "$tmp" && bibtex refs) || {
        echo "bibtex failed on style=$style" >&2
        exit 1
    }
}

run_bibtex_docker() {
    local tmp="$1"
    local style="$2"
    docker run --rm \
        -v "$tmp":/work \
        -w /work \
        texlive/texlive:latest \
        bibtex refs
}

for style in "${STYLES[@]}"; do
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT

    cp "$FIXTURES_DIR/refs.bib" "$tmp/refs.bib"
    cp "$STYLES_DIR/$style.bst" "$tmp/$style.bst"

    # Minimal .aux naming the style, the database, and every citation key.
    {
        echo "\\relax"
        echo "\\bibstyle{$style}"
        echo "\\bibdata{refs}"
        while IFS= read -r key; do
            [[ -z "$key" ]] && continue
            [[ "$key" =~ ^# ]] && continue
            echo "\\citation{$key}"
        done < "$FIXTURES_DIR/refs.cites"
    } > "$tmp/refs.aux"

    if (( USE_DOCKER )); then
        run_bibtex_docker "$tmp" "$style"
    else
        run_bibtex_host "$tmp" "$style"
    fi

    cp "$tmp/refs.bbl" "$FIXTURES_DIR/$style.expected.bbl"
    echo "wrote $FIXTURES_DIR/$style.expected.bbl"
    rm -rf "$tmp"
    trap - EXIT
done

echo "all fixtures regenerated."
