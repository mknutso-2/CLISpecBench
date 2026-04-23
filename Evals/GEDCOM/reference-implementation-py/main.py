from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from gedcom_model import GedcomDataset, GedcomError
from gedcom_parser import parse_gedcom_text, render_gedcom_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        return 0 if code == 0 else 1

    output_path = Path(args.output)
    try:
        request_data: Any = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(request_data, dict):
            raise GedcomError("invalid_request", "Request must be a JSON object")
        request = cast(dict[str, Any], request_data)
        response = handle_request(request)
        output_path.write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
        return 0 if response["status"] == "ok" else 1
    except GedcomError as exc:
        response = error_response(exc.code, exc.message, line=exc.line)
        output_path.write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        response = error_response("invalid_request", f"Invalid request: {exc}")
        output_path.write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
        return 1
    except Exception as exc:  # pragma: no cover - internal error path
        response = error_response("internal_error", f"Unexpected internal error: {exc}")
        output_path.write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
        return 2


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    action = request.get("action")
    if action == "inspect":
        text = request.get("gedcom_text")
        if not isinstance(text, str):
            raise GedcomError("invalid_request", "inspect requires string field gedcom_text")
        dataset = parse_gedcom_text(text)
        return ok_response({"dataset": dataset.to_dict()})
    if action == "render":
        dataset_obj = request.get("dataset")
        if not isinstance(dataset_obj, dict):
            raise GedcomError("invalid_request", "render requires object field dataset")
        dataset = GedcomDataset.from_dict(cast(dict[str, Any], dataset_obj))
        text = render_gedcom_text(dataset)
        return ok_response({"gedcom_text": text})
    raise GedcomError("invalid_request", f"Unsupported action {action!r}")


def ok_response(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "ok",
        "error": None,
        "result": result,
    }


def error_response(code: str, message: str, *, line: int | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if line is not None:
        error["line"] = line
    return {
        "status": "error",
        "error": error,
        "result": None,
    }


if __name__ == "__main__":
    sys.exit(main())
