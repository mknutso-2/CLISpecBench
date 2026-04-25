from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .conftest import run_las
from .las_support import dataset_for_point_format, encode_request_for_inspect


def test_reference_cli_runs(submission_command: Sequence[str], tmp_path: Path) -> None:
    request = encode_request_for_inspect(dataset_for_point_format(0))
    result, payload = run_las(submission_command, request, tmp_path)

    assert result.returncode == 0
    assert payload is not None
    assert payload.get("status") == "ok"
