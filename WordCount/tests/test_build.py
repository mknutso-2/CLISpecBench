from __future__ import annotations

from swe_buildbench.cncsim import CMakeBuildResult


def test_payload_builds_successfully(build_result: CMakeBuildResult) -> None:
    assert build_result.build_dir.exists()
    assert build_result.configure.returncode == 0
    assert build_result.build.returncode == 0
