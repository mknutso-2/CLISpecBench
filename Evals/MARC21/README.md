# MARC21

MARC 21 bibliographic expanded-profile eval for CLISpecBench.

This eval asks an agent to implement a parser, validator, ISO 2709 renderer,
and MARCXML renderer for a broader MARC 21 bibliographic interchange profile.

The eval is intentionally narrower than full MARC 21. It focuses on:

- single-record ISO 2709 inputs
- single-record MARCXML inputs
- UTF-8 / Unicode records only
- leader and directory correctness
- control fields (`001`-`009`)
- data fields with exactly two indicators and explicit subfields
- canonical JSON inspection output
- MARCXML inspection and rendering from the canonical JSON record model

The initial runnable eval is Python-only for the same reason as the other new
batch evals: it keeps four new tasks runnable and agent-evaluable without
turning the work into a parallel C++ porting project.

## CLI Contract

The program is invoked with the standard CLISpecBench flags:

```text
python main.py --input <request.json> --output <response.json>
```

Supported actions:

- `inspect`: parse an ISO 2709 MARC record from base64
- `inspect_marcxml`: parse a MARCXML record string
- `render_iso2709`: render canonical JSON to ISO 2709 bytes
- `render_marcxml`: render canonical JSON to MARCXML text

See [prompt/technical-requirements-prompt.md](prompt/technical-requirements-prompt.md)
for the exact request and response schema.

## Running Tests

```bash
uv run pytest Evals/MARC21/tests --language=py
```
