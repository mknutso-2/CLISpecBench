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
CORPORA=(refs refs-edge)

USE_DOCKER=0
if [[ "${1:-}" == "--docker" ]]; then
    USE_DOCKER=1
fi

if [[ ! -d "$FIXTURES_DIR" ]]; then
    echo "error: fixtures dir missing: $FIXTURES_DIR" >&2
    exit 1
fi
for corpus in "${CORPORA[@]}"; do
    if [[ ! -f "$FIXTURES_DIR/$corpus.bib" ]]; then
        echo "error: $corpus.bib missing from $FIXTURES_DIR" >&2
        exit 1
    fi
done

run_bibtex_host() {
    local tmp="$1"
    local stem="$2"
    (cd "$tmp" && bibtex "$stem") || {
        echo "bibtex failed on $stem" >&2
        exit 1
    }
}

run_bibtex_docker() {
    local tmp="$1"
    local stem="$2"
    docker run --rm \
        -v "$tmp":/work \
        -w /work \
        texlive/texlive:latest \
        bibtex "$stem"
}

for corpus in "${CORPORA[@]}"; do
    for style in "${STYLES[@]}"; do
        tmp="$(mktemp -d)"
        trap 'rm -rf "$tmp"' EXIT

        cp "$FIXTURES_DIR/$corpus.bib" "$tmp/$corpus.bib"
        cp "$STYLES_DIR/$style.bst" "$tmp/$style.bst"

        # Minimal .aux naming the style, the database, and every citation key.
        {
            echo "\\relax"
            echo "\\bibstyle{$style}"
            echo "\\bibdata{$corpus}"
            while IFS= read -r key; do
                [[ -z "$key" ]] && continue
                [[ "$key" =~ ^# ]] && continue
                echo "\\citation{$key}"
            done < "$FIXTURES_DIR/$corpus.cites"
        } > "$tmp/$corpus.aux"

        if (( USE_DOCKER )); then
            run_bibtex_docker "$tmp" "$corpus"
        else
            run_bibtex_host "$tmp" "$corpus"
        fi

        cp "$tmp/$corpus.bbl" "$FIXTURES_DIR/$style.$corpus.expected.bbl"
        echo "wrote $FIXTURES_DIR/$style.$corpus.expected.bbl"
        rm -rf "$tmp"
        trap - EXIT
    done
done

echo "all fixtures regenerated."
