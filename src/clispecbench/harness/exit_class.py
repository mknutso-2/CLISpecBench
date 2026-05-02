"""Classify a finished run into a failure-mode bucket.

The bucket determines whether the run counts toward Best/Mean per
``skills/eval-runs/SKILL.md``. The classification rule lives in one
place so the runner and any backfill script agree.

Buckets
-------

- ``completed`` — agent self-terminated cleanly. Always included.
- ``model_capped`` — agent hit a model-side cap (usage cap, daily
  quota, per-message output-token limit) AFTER doing real work.
- ``model_timeout`` — agent killed by a wall-time backstop while
  still working.
- ``model_context_exhausted`` — agent hit the context window limit.
- ``model_no_code`` — agent voluntarily exited without writing source.
- ``model_build_failure`` — agent wrote source but it doesn't compile.
- ``model_agent_error`` — agent crashed or threw an unhandled error.
- ``infra_auth`` — 401/403 (auth failure) before any real work.
- ``infra_rate_limit`` — 429 / quota exhaustion before any real work.
- ``infra_other`` — server errors, capacity errors, container startup
  crashes; any host-side failure not attributable to the model.

The line between ``model_capped`` and ``infra_rate_limit`` is wall
time + artifact presence: a "you've hit your limit" message at 5 s
with no source is ``infra_rate_limit``; the same message at 50 min
with 4,000 LOC of working code is ``model_capped``.
"""

from __future__ import annotations

# Wall-time floor under which a "limit" message is treated as
# infrastructure (agent never got going) rather than model-capped.
_REAL_WORK_THRESHOLD_SECONDS = 60.0


def classify_exit(
    *,
    exit_reason: str,
    agent_last_message: str | None,
    wall_clock_seconds: float,
    has_source_files: bool,
    build_success: bool | None,
    test_total: int,
) -> str:
    """Return the failure-mode bucket for one finished run.

    Inputs:
    - ``exit_reason``: harness-level outcome (``completed`` |
      ``timeout`` | ``error`` | ``no_output`` | ...)
    - ``agent_last_message``: the agent's last text frame, used to
      distinguish cap / auth / context-exhaustion failure modes.
    - ``wall_clock_seconds``: total agent-container wall time.
    - ``has_source_files``: did the agent write anything to ``output/``?
    - ``build_success``: did the build smoke pass? ``None`` = no build
      step (interpreted language).
    - ``test_total``: how many tests pytest collected.

    The function is pure and side-effect-free so it can be called from
    both the runner and a backfill script.
    """
    msg = (agent_last_message or "").lower()
    real_work = wall_clock_seconds >= _REAL_WORK_THRESHOLD_SECONDS and has_source_files

    # --- exit_reason == "completed" ---
    # Agent voluntarily ran to its self-terminated end.
    if exit_reason == "completed":
        if not has_source_files:
            return "model_no_code"
        if build_success is False:
            return "model_build_failure"
        return "completed"

    # --- exit_reason == "no_output" ---
    # Container produced no agent output at all. Classify by what we know
    # about why the agent went silent (auth / rate / model cap / quiet
    # crash).
    if exit_reason == "no_output":
        if "401" in msg or "invalid authentication" in msg or "unauthorized" in msg:
            return "infra_auth"
        if "429" in msg or ("rate limit" in msg and not real_work):
            return "infra_rate_limit"
        if real_work and ("usage limit" in msg or "your limit" in msg or "exceeded" in msg):
            return "model_capped"
        return "infra_other"

    # --- exit_reason == "timeout" ---
    if exit_reason == "timeout":
        return "model_timeout"

    # --- exit_reason == "error" (or anything else) ---

    # Auth / rate-limit pattern (most often a 401 fast-fail).
    if "401" in msg or "invalid authentication" in msg or "unauthorized" in msg:
        if real_work:
            # Agent did substantial work before the auth blew up — still
            # reflects model behavior; treat as a model-side cap-style
            # outcome rather than pure infrastructure.
            return "model_capped"
        return "infra_auth"

    # Per-message output-token cap (Claude Code SDK message).
    if "exceeded" in msg and "output token maximum" in msg:
        return "model_context_exhausted" if not has_source_files else "model_capped"

    # Generic "you've hit your limit" / "usage limit" / OpenAI quota.
    if "usage limit" in msg or "your limit" in msg or "purchase more credits" in msg:
        return "model_capped" if real_work else "infra_rate_limit"

    if "context" in msg and ("limit" in msg or "exhausted" in msg or "window" in msg):
        return "model_context_exhausted"

    if "rate limit" in msg or "429" in msg:
        return "model_capped" if real_work else "infra_rate_limit"

    # The agent crashed or returned a non-clean exit for some other reason.
    if has_source_files and test_total > 0:
        # We at least got a real submission scored — score the model,
        # don't blame infrastructure.
        return "model_agent_error"
    return "infra_other"


def is_included(exit_class: str | None) -> bool:
    """True if a run with this bucket counts toward Best/Mean."""
    if exit_class is None:
        return False
    return exit_class == "completed" or exit_class.startswith("model_")
