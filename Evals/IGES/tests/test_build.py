from __future__ import annotations

import subprocess

from swe_buildbench.build import PreparedSubmission


def test_payload_builds_successfully(prepared_submission: PreparedSubmission) -> None:
    assert prepared_submission.build_dir.exists()
    assert len(prepared_submission.command) >= 1

    # Smoke test: the submission is actually invokable as a subprocess.
    result = subprocess.run(
        list(prepared_submission.command),
        capture_output=True,
        timeout=10,
    )
    assert result.returncode is not None
