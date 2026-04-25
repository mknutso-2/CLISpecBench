from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from las_parser import LasError, inspect_las, render_las


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    args = _parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        request = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:
        _write_payload(
            output_path,
            {
                "status": "error",
                "error": {
                    "code": "invalid_request",
                    "message": f"Failed to parse request JSON: {exc}",
                },
                "result": None,
            },
        )
        return 1

    try:
        if not isinstance(request, dict):
            raise LasError("invalid_request", "Request JSON must be an object")
        request_obj = cast(dict[str, Any], request)
        action = request_obj.get("action")
        if action == "inspect":
            result = {"dataset": inspect_las(request_obj)}
        elif action == "render":
            dataset = request_obj.get("dataset")
            if not isinstance(dataset, dict):
                raise LasError("invalid_request", "render requests must include a dataset object")
            result = {"las_b64": render_las(cast(dict[str, Any], dataset))}
        else:
            raise LasError("invalid_request", "Unsupported action")
        _write_payload(
            output_path,
            {
                "status": "ok",
                "error": None,
                "result": result,
            },
        )
        return 0
    except LasError as exc:
        error: dict[str, Any] = {"code": exc.code, "message": exc.message}
        if exc.offset is not None:
            error["offset"] = exc.offset
        _write_payload(
            output_path,
            {
                "status": "error",
                "error": error,
                "result": None,
            },
        )
        return 1 if exc.code != "internal_error" else 2
    except Exception as exc:
        _write_payload(
            output_path,
            {
                "status": "error",
                "error": {
                    "code": "internal_error",
                    "message": f"Unexpected internal error: {exc}",
                },
                "result": None,
            },
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
