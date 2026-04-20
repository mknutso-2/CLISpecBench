"""Print repo-relative auth smoke script paths from the agent registry."""

from __future__ import annotations

from clispecbench.agents.registry import list_auth_smoke_scripts


def main() -> None:
    for script_path in list_auth_smoke_scripts():
        print(script_path)


if __name__ == "__main__":
    main()
