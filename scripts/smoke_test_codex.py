"""Smoke-test Codex auth and restricted egress through the production harness path."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path, PurePosixPath

from clispecbench.agents.codex_cli import CodexCLIAdapter
from clispecbench.harness.docker import ContainerConfig, DockerSandbox
from clispecbench.harness.platform import resolve_host_home


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", nargs="?")
    parser.add_argument("effort", nargs="?")
    args = parser.parse_args()
    if args.effort and not args.model:
        parser.error("an effort requires a model")

    adapter = CodexCLIAdapter(model=args.model, effort=args.effort)
    workspace = Path(tempfile.mkdtemp(prefix="clispecbench-codex-smoke-"))
    sandbox = DockerSandbox()
    try:
        (workspace / "prompt.md").write_text(
            "Respond with exactly the word hello.",
            encoding="utf-8",
        )
        config = ContainerConfig(
            image=adapter.image_tag,
            environment=adapter.environment({}),
            command=adapter.invoke_command(
                PurePosixPath("/workspace/prompt.md"),
                PurePosixPath("/workspace"),
            ),
            volumes=adapter.credential_mounts(resolve_host_home()),
            egress_allowlist=adapter.allowed_hosts,
        )
        sandbox.create(config)
        sandbox.copy_in(workspace, PurePosixPath("/workspace"))
        run = sandbox.start_and_wait(300)
        logs = sandbox.get_logs()
        audit = sandbox.get_network_audit_logs()
        print(logs, end="" if logs.endswith("\n") else "\n")
        print("--- restricted-egress audit ---")
        print(audit, end="" if audit.endswith("\n") else "\n")

        last_message = adapter.extract_last_agent_message(logs)
        if run.timed_out or run.exit_code != 0 or last_message is None:
            return 1
        if last_message.strip().lower() != "hello":
            print(f"Unexpected final response: {last_message!r}")
            return 1
        if '"event": "allowed"' not in audit or '"host": "chatgpt.com"' not in audit:
            print("Codex completed without an audited chatgpt.com connection")
            return 1
        return 0
    finally:
        sandbox.cleanup()
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
