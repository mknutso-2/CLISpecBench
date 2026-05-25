"""Editorial status labels and the ``exit_class`` buckets they map to.

This module is the single source of truth for the eval status taxonomy
defined in ``.claude/skills/run-eval/SKILL.md``. Both of the following
consume it; do NOT duplicate the literal label strings elsewhere:

  - ``clispecbench.harness.publish`` validates ``--status`` against
    :data:`VALID_STATUSES` and auto-populates ``metadata.exit_class`` from
    :data:`STATUS_TO_EXIT_CLASS`.
  - ``published_results/web/build_results_json.py`` uses
    :data:`INCLUDED_NON_COMPLETED_STATUSES` to decide which non-``completed``
    rows are surfaced in the dashboard's main table vs. its excluded section.

Per SKILL.md:

  * ``completed`` runs are Always Included.
  * ``model_*`` runs (the agent did real work but exited via something other
    than its own completion path: timeout, output-token cap, build failure,
    crash, etc.) are Included in Best/Mean tables; the score is real model
    signal.
  * ``infra_*`` runs (auth failure, rolling usage cap, host/network) are
    Never Published. There is no editorial label for them, since the
    publish CLI refuses them at the gate.

Mid-session ``infra_*`` failures
================================
Note: an ``infra_*`` failure is non-publishable *regardless of wall-time,
tool-call count, or partial test score*. The defining property is that the
agent was cut off by something outside the model's control — operator
credentials, an Anthropic usage cap, or an API connection drop. Even if the
agent ran for 17 minutes, made 14 tool calls, and the harness found a
scorable submission at /workspace/output, the score reflects when the
operator's token happened to expire (or when the rolling cap window
saturated, or when the network blipped), NOT what the model could do.
Recording such runs inflates the model's failure rate with operator/env
signal and biases comparisons across models that ran at different
times-of-day or on different links.

Concrete examples seen and confirmed non-publishable:

  * ``Failed to authenticate. API Error: 401 ...`` after substantial wall
    time — ``infra_auth`` (operator's OAuth token expired mid-run).
    Caught by ``publish._classify_unpublishable_stop_message`` (``401``
    / ``unauthorized`` / ``invalid api key`` / ``expired credential``).
  * ``You've hit your limit · resets at <time>`` — ``infra_usage_cap``
    (operator's Anthropic rolling cap window saturated). Caught by
    ``"you've hit your limit"`` substring match.
  * ``API Error: Unable to connect to API (ConnectionRefused)`` — should
    be classified as ``infra_other`` (network) but is not currently in
    the publish-gate stoplist. Add similar host/network signatures here
    as they're observed.
"""

from __future__ import annotations

from typing import Final

# Status -> exit_class. The first two ("Complete", "Incomplete") describe an
# agent that self-terminated and map to ``completed``. The rest are model-side
# failures (Included in Best/Mean) and map to ``model_*`` buckets.
STATUS_TO_EXIT_CLASS: Final[dict[str, str]] = {
    "Complete": "completed",
    "Incomplete": "completed",
    "Timeout": "model_timeout",
    "Context exhausted": "model_context_exhausted",
    "No code written": "model_no_code",
    "Build failure": "model_build_failure",
    "Agent error": "model_agent_error",
    "Output cap": "model_output_cap",
}

# All editorial statuses the publish CLI accepts. Anything outside this set
# is a typo or a deprecated/legacy label and should be rejected at publish.
VALID_STATUSES: Final[frozenset[str]] = frozenset(STATUS_TO_EXIT_CLASS.keys())

# Subset of VALID_STATUSES whose exit_class is a ``model_*`` bucket. These
# describe runs whose exit_reason is NOT "completed" but should still appear
# in the dashboard's main table (the agent produced real work, the failure
# is informative model signal). Used by build_results_json.py at the inclusion
# gate.
INCLUDED_NON_COMPLETED_STATUSES: Final[frozenset[str]] = frozenset(
    label for label, cls in STATUS_TO_EXIT_CLASS.items() if cls.startswith("model_")
)

# Deprecated labels that older published runs may carry. Document for
# migration tooling; never produce these in new publishes. The mapping says
# what each should be relabeled to under the current taxonomy.
DEPRECATED_STATUS_REPLACEMENTS: Final[dict[str, str]] = {
    # "Capped (model)" predates SKILL.md ffe81db, when model_capped was split
    # into infra_usage_cap (account billing — never publish) and
    # model_output_cap (per-message 32k output ceiling — publish as "Output cap").
    # Existing runs with this label should be re-inspected: if their
    # agent_last_message references "exceeded the 32000 output token maximum"
    # they are Output cap; if it says "you've hit your limit · resets at X"
    # they were never publishable and should be unpublished.
    "Capped (model)": "Output cap",
}
