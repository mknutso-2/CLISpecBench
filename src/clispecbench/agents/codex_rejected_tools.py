"""Supplement canonical v2 counts only from proven pre-item tool rejections.

The explicit runtime tool error proves one attempted invocation. AST inspection
only verifies an unambiguous pairing; it never estimates runtime counts from
call sites. Complex failed wrappers make only the tool metric unavailable;
token totals and
cost remain independent. The parser reads JavaScript syntax but never executes it.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import Any, cast

from clispecbench.agents.codex_tool_evidence import (
    explicit_pre_item_rejection,
    failed_wrapper_blocks,
    scan,
)


def _command_matches(observed: object, expected: str) -> bool | None:
    if not isinstance(observed, str):
        return None
    if observed == expected:
        return True
    try:
        words = shlex.split(observed)
    except ValueError:
        return None
    if len(words) >= 3 and Path(words[0]).name in {"bash", "sh", "zsh", "dash"}:
        for index, word in enumerate(words[1:-1], 1):
            if word.startswith("-") and not word.startswith("--") and "c" in word[1:]:
                return words[index + 1] == expected
    # An ordinary different shell command is not the rejected request.
    return False


def supplement(audit: dict[str, Any], baseline: int | None) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    problems: list[str] = list(audit.get("evidence_errors", []))
    batches: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    if not audit.get("session_files"):
        problems.append("preserved session evidence unavailable")
    if not audit.get(
        "canonical_events_present",
        any(
            Path(m["path"]).name == "codex-events.jsonl" for m in audit.get("evidence_manifest", [])
        ),
    ):
        problems.append("canonical event evidence unavailable")
    for rejection in audit["rejections"]:
        call_id = rejection.get("call_id")
        if not isinstance(call_id, str) or not call_id:
            problems.append("rejection lacks a stable wrapper call ID")
            continue
        signature = json.dumps(
            {
                "requests": [r["payload"] for r in rejection.get("requests", [])],
                "output": rejection.get("rejection_output", {}).get("payload"),
            },
            sort_keys=True,
        )
        if call_id in seen:
            if seen[call_id] != signature:
                problems.append(f"conflicting duplicate rejection: {call_id}")
            continue
        seen[call_id] = signature
        requests = rejection.get("requests", [])
        # Duplicate byte-identical preserved request records can occur in copied
        # rollouts. A conflicting duplicate cannot identify the failed wrapper.
        payloads = {json.dumps(r["payload"], sort_keys=True) for r in requests}
        if len(payloads) != 1:
            problems.append(f"unpaired or ambiguous wrapper: {call_id}")
            continue
        request = json.loads(next(iter(payloads)))
        if request.get("name") not in {"exec", "functions.exec"} or request.get("type") not in {
            "custom_tool_call",
            "function_call",
        }:
            problems.append(f"rejection is not paired with functions.exec: {call_id}")
            continue
        source = request.get("input", request.get("arguments"))
        if not isinstance(source, str):
            problems.append(f"nontext failed wrapper: {call_id}")
            continue
        duplicate_outputs = rejection.get("rejection_outputs", [rejection["rejection_output"]])
        if len({json.dumps(value["payload"], sort_keys=True) for value in duplicate_outputs}) != 1:
            problems.append(f"conflicting duplicate tool outputs: {call_id}")
            continue
        output = rejection["rejection_output"]["payload"]
        if output.get("call_id") != call_id or output.get("type") not in {
            "custom_tool_call_output",
            "function_call_output",
        }:
            problems.append(f"rejection output does not match wrapper: {call_id}")
            continue
        matched = explicit_pre_item_rejection(output)
        if len(matched) != 1:
            problems.append(f"no single explicit pre-item process rejection: {call_id}")
            continue
        pairs.append(rejection)
        batches.append({"id": len(pairs) - 1, "source": source})
    syntax_checks: list[tuple[str, str]] = []
    seen_other: set[str] = set()
    for failed in audit.get("other_failed_wrappers", []):
        call_id = failed.get("call_id")
        if call_id in seen_other:
            continue
        seen_other.add(call_id)
        requests = failed.get("requests", [])
        payloads = {json.dumps(r["payload"], sort_keys=True) for r in requests}
        error_blocks = failed_wrapper_blocks(failed["output"]["payload"])
        if len(payloads) != 1 or not any(
            value.startswith("Script error:\nSyntaxError:") for value in error_blocks
        ):
            problems.append(f"unclassified failed wrapper: {call_id}")
            continue
        request = json.loads(next(iter(payloads)))
        source = request.get("input", request.get("arguments"))
        if request.get("name") not in {"exec", "functions.exec"} or not isinstance(source, str):
            problems.append(f"unclassified failed wrapper: {call_id}")
            continue
        syntax_checks.append((call_id, source))
    if syntax_checks:
        try:
            process = subprocess.run(
                [
                    "node",
                    "--expose-internals",
                    str(Path(__file__).with_name("single_rejected_exec.cjs")),
                ],
                input=json.dumps(
                    [
                        {"id": index, "source": source}
                        for index, (_, source) in enumerate(syntax_checks)
                    ]
                ),
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            syntax_results = json.loads(process.stdout)
            if {r["id"] for r in syntax_results} != set(range(len(syntax_checks))):
                raise ValueError("incomplete syntax inspection")
            for result in syntax_results:
                if not result.get("parse_error"):
                    problems.append(
                        "Failed wrapper syntax rejection not independently confirmed: "
                        f"{syntax_checks[result['id']][0]}"
                    )
        except (OSError, ValueError, subprocess.SubprocessError):
            problems.append("failed wrapper syntax inspection unavailable")
    parsed: list[dict[str, Any]] = []
    if batches:
        try:
            process = subprocess.run(
                [
                    "node",
                    "--expose-internals",
                    str(Path(__file__).with_name("single_rejected_exec.cjs")),
                ],
                input=json.dumps(batches),
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            parsed = json.loads(process.stdout)
            if {p["id"] for p in parsed} != set(range(len(pairs))):
                raise ValueError("incomplete AST output")
        except (OSError, ValueError, subprocess.SubprocessError):
            problems.append("failed-wrapper AST inspection unavailable")
    for parsed_item in parsed:
        pair = pairs[cast(int, parsed_item["id"])]
        call_id = pair["call_id"]
        if not parsed_item.get("available"):
            problems.append(f"{call_id}: {parsed_item.get('reason')}")
            continue
        command = parsed_item["command"]
        matches: list[str] = []
        unknown: list[str] = []
        for item in audit["canonical_items"]:
            if item["type"] != "command_execution":
                continue
            match = _command_matches(item.get("command"), command)
            if match is True:
                matches.append(item["id"])
            elif match is None:
                unknown.append(item["id"])
        if matches or unknown:
            problems.append(
                f"{call_id}: canonical overlap or unparseable command evidence; "
                f"matches={matches}, unknown={unknown}"
            )
            continue
        evidence.append(
            {
                "wrapper_call_id": call_id,
                "tool": "exec_command",
                "added_invocations": 1,
                "reason": (
                    "Explicit nested CreateProcess rejection, paired with one direct awaited "
                    "request and absent from all canonical command items."
                ),
                "request_command": command,
                "request_locations": [
                    {"path": r["path"], "line": r["line"]} for r in pair["requests"]
                ],
                "output_location": {
                    "path": pair["rejection_output"]["path"],
                    "line": pair["rejection_output"]["line"],
                },
            }
        )
    if baseline is None or isinstance(baseline, bool) or baseline < 0:
        problems.append("canonical baseline count unavailable")
    available = not problems
    return {
        "schema_version": 1,
        "definition": "underlying_tool_invocations_v2",
        "canonical_baseline": baseline,
        "additional_proven_rejections": len(evidence),
        "corrected_tool_calls": cast(int, baseline) + len(evidence) if available else None,
        "available": available,
        "evidence": evidence,
        "confirmed_preexecution_syntax_rejections": [call_id for call_id, _ in syntax_checks]
        if available
        else [],
        "problems": problems,
    }


def audit_result_tool_calls(result_path: Path, canonical_count: int | None) -> dict[str, Any]:
    """Root-facing read-only API for held rows and prior publication corrections.

    Pass the existing canonical event counter before session supplementation.
    Token/cost fields stay byte-for-value identical; unavailable evidence returns
    null tool_calls and tool_calls_definition, never a fabricated zero or unchanged success.
    """
    import copy
    import hashlib

    original_bytes = result_path.read_bytes()
    original = json.loads(original_bytes)
    evidence = scan(result_path.parent / "sessions", result_path.parent / "codex-events.jsonl")
    result = supplement(evidence, canonical_count)
    usage = copy.deepcopy(original["token_usage"])
    usage["tool_calls"] = result["corrected_tool_calls"]
    usage["tool_calls_definition"] = (
        "underlying_tool_invocations_v2" if result["available"] else None
    )
    result.update(
        run_uid=original["metadata"]["run_uid"],
        original_result_path=str(result_path.resolve()),
        original_result_sha256=hashlib.sha256(original_bytes).hexdigest(),
        original_token_usage=original["token_usage"],
        corrected_token_usage=usage,
        evidence_manifest=evidence["evidence_manifest"],
    )
    return result
