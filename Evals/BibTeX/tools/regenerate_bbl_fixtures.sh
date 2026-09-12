#!/usr/bin/env bash
# Reproduce hidden BBL fixtures with an explicitly selected independent oracle.
# Example: bash Evals/BibTeX/tools/regenerate_bbl_fixtures.sh --bibtex /absolute/path/to/bibtex --check
# Docker: --docker sha256:<full-image-id> (image must already exist locally).
# Omit --check to replace the eight BBLs after every oracle run succeeds.
set -euo pipefail

EVAL_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
FIXTURES_DIR="$EVAL_ROOT/tests/fixtures"
STYLES_DIR="$EVAL_ROOT/prompt/docs/authoritative"
ORACLE_MODE=""
ORACLE=""
CHECK_ONLY=0
while (($#)); do
    case "$1" in
        --bibtex|--docker)
            [[ -z "$ORACLE_MODE" && $# -ge 2 ]] || { echo 'select one oracle' >&2; exit 2; }
            ORACLE_MODE="${1#--}"
            ORACLE="$2"
            shift 2
            ;;
        --check) CHECK_ONLY=1; shift ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done
[[ -n "$ORACLE_MODE" ]] || { echo 'specify --bibtex PATH or --docker sha256:ID' >&2; exit 2; }
if [[ "$ORACLE_MODE" == docker ]]; then
    [[ "$ORACLE" =~ ^sha256:[0-9a-f]{64}$ ]] || { echo 'Docker requires an immutable image ID' >&2; exit 2; }
else
    ORACLE="$(command -v -- "$ORACLE")"
    [[ "$ORACLE" = /* && -x "$ORACLE" ]] || { echo 'BibTeX executable must resolve to an absolute path' >&2; exit 2; }
fi

STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT
run_oracle() {
    local oracle_dir="$1"
    shift
    if [[ "$ORACLE_MODE" == docker ]]; then
        docker run --rm --pull=never --network none -v "$oracle_dir":/work -w /work \
            -e max_print_line=79 -e min_print_line=3 -e BIBINPUTS=. -e BSTINPUTS=. \
            "$ORACLE" bibtex "$@"
    else
        (cd "$oracle_dir" && max_print_line=79 min_print_line=3 BIBINPUTS=. BSTINPUTS=. \
            "$ORACLE" "$@")
    fi
}
run_oracle "$STAGING_DIR" --version > "$STAGING_DIR/oracle-version.txt"

for corpus in refs refs-edge; do
    for style in plain alpha unsrt abbrv; do
        case_dir="$STAGING_DIR/$style.$corpus"
        mkdir "$case_dir"
        cp "$FIXTURES_DIR/$corpus.bib" "$case_dir/$corpus.bib"
        cp "$STYLES_DIR/$style.bst" "$case_dir/$style.bst"
        # The public copies mounted by the grader must also remain exact.
        cmp "$STYLES_DIR/$style.bst" "$FIXTURES_DIR/authoritative/$style.bst"
        {
            printf '\\relax\n\\bibstyle{%s}\n\\bibdata{%s}\n' "$style" "$corpus"
            while IFS= read -r key || [[ -n "$key" ]]; do
                [[ -z "$key" || "$key" == \#* ]] && continue
                printf '\\citation{%s}\n' "$key"
            done < "$FIXTURES_DIR/$corpus.cites"
        } > "$case_dir/$corpus.aux"
        run_oracle "$case_dir" -min-crossrefs=2 "$corpus" > "$case_dir/oracle.log"
        [[ -f "$case_dir/$corpus.bbl" ]] || { echo "missing oracle output: $style/$corpus" >&2; exit 1; }
    done
done

# Check all bytes before writing any fixture. Record executable/image identity,
# runtime parameters and every input/output hash for reproducible regeneration.
python3 - "$EVAL_ROOT" "$STAGING_DIR" "$ORACLE_MODE" "$ORACLE" "$CHECK_ONLY" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

eval_root, staging = map(Path, sys.argv[1:3])
mode, oracle, check = sys.argv[3:]
fixtures = eval_root / 'tests/fixtures'
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
rows = []
for corpus in ('refs', 'refs-edge'):
    for style in ('plain', 'alpha', 'unsrt', 'abbrv'):
        generated = staging / f'{style}.{corpus}' / f'{corpus}.bbl'
        target = fixtures / f'{style}.{corpus}.expected.bbl'
        if check == '1' and generated.read_bytes() != target.read_bytes():
            raise SystemExit(f'oracle mismatch: {target}')
        rows.append({'corpus': corpus, 'style': style,
                     'bib_sha256': digest(fixtures / f'{corpus}.bib'),
                     'cites_sha256': digest(fixtures / f'{corpus}.cites'),
                     'style_sha256': digest(eval_root / f'prompt/docs/authoritative/{style}.bst'),
                     'bbl_sha256': digest(generated)})
if check == '1':
    print('all eight independent oracle outputs match the committed fixtures')
else:
    for row in rows:
        stem = f"{row['style']}.{row['corpus']}"
        (fixtures / f'{stem}.expected.bbl').write_bytes(
            (staging / stem / f"{row['corpus']}.bbl").read_bytes())
    provenance = {'oracle_mode': mode, 'oracle': oracle,
                  'version': (staging / 'oracle-version.txt').read_text(),
                  'max_print_line': 79, 'min_print_line': 3, 'min_crossrefs': 2,
                  'rows': rows}
    if mode == 'bibtex':
        provenance['binary_sha256'] = digest(Path(oracle))
    (fixtures / 'regeneration-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print('all eight fixtures regenerated; hashes saved in regeneration-provenance.json')
PY
