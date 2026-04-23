from __future__ import annotations

import subprocess

from clispecbench.build import PreparedSubmission


def test_payload_builds_successfully(prepared_submission: PreparedSubmission) -> None:
    assert prepared_submission.build_dir.exists()
    result = subprocess.run(list(prepared_submission.command), capture_output=True, timeout=10)
    assert result.returncode == 1
