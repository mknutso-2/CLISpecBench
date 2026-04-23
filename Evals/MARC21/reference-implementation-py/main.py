from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from marc21_model import MarcError, Record
from marc21_parser import (
    b64decode_bytes,
    b64encode_bytes,
    inspect_marcxml,
    inspect_record_bytes,
    render_iso2709,
    render_marcxml,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    output_path = Path(args.output)
    try:
        request_data: Any = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(request_data, dict):
            raise MarcError("invalid_request", "Request must be a JSON object")
        request = cast(dict[str, Any], request_data)
        response = handle_request(request)
        output_path.write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
        return 0 if response["status"] == "ok" else 1
    except MarcError as exc:
        output_path.write_text(
            json.dumps(error_response(exc.code, exc.message), indent=2) + "\n",
            encoding="utf-8",
        )
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        output_path.write_text(
            json.dumps(error_response("invalid_request", f"Invalid request: {exc}"), indent=2) + "\n",
            encoding="utf-8",
        )
        return 1
    except Exception as exc:  # pragma: no cover - internal error path
        output_path.write_text(
            json.dumps(error_response("internal_error", f"Unexpected internal error: {exc}"), indent=2)
            + "\n",
            encoding="utf-8",
        )
        return 2


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    action = request.get("action")
    if action == "inspect":
        raw = request.get("record_b64")
        if not isinstance(raw, str):
            raise MarcError("invalid_request", "inspect requires string field record_b64")
        record = inspect_record_bytes(b64decode_bytes(raw))
        return ok_response({"record": record.to_dict()})
    if action == "inspect_marcxml":
        marcxml = request.get("marcxml")
        if not isinstance(marcxml, str):
            raise MarcError("invalid_request", "inspect_marcxml requires string field marcxml")
        record = inspect_marcxml(marcxml)
        return ok_response({"record": record.to_dict()})
    if action == "render_iso2709":
        record_obj = request.get("record")
        if not isinstance(record_obj, dict):
            raise MarcError("invalid_request", "render_iso2709 requires object field record")
        record = Record.from_dict(cast(dict[str, Any], record_obj))
        return ok_response({"record_b64": b64encode_bytes(render_iso2709(record))})
    if action == "render_marcxml":
        record_obj = request.get("record")
        if not isinstance(record_obj, dict):
            raise MarcError("invalid_request", "render_marcxml requires object field record")
        record = Record.from_dict(cast(dict[str, Any], record_obj))
        return ok_response({"marcxml": render_marcxml(record)})
    raise MarcError("invalid_request", f"Unsupported action {action!r}")


def ok_response(result: dict[str, Any]) -> dict[str, Any]:
    return {"status": "ok", "error": None, "result": result}


def error_response(code: str, message: str) -> dict[str, Any]:
    return {"status": "error", "error": {"code": code, "message": message}, "result": None}


if __name__ == "__main__":
    sys.exit(main())
