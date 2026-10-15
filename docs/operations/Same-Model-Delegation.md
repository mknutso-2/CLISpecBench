# Same-model delegation

Matthew established this rule on October 9, 2026: a model may not use a subagent of a different model than itself. This applies to benchmark participants and repository-work coordinators. Delegation is permitted; cross-model assistance is not.

Use the parent's **exact model identifier and version**, not just the provider or family. This includes subagents, teammates, workflow agents, nested delegation, and other model-assisted sidecars. Inherited model selection is acceptable only when it resolves to that same exact model. Do not use a cheaper, stronger, fallback, or differently versioned model. If the exact parent model is unavailable, leave the work held; do not substitute.

## Enforcement and evidence

For Claude Code v2.1.257 or later, set both non-secret environment variables in the benchmark container:

```text
CLAUDE_CODE_SUBAGENT_MODEL=<exact parent model ID>
CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1
```

The default-model variable alone does not prevent an explicit per-call override. The force variable alone leaves the built-in Explore exception. Both variables together force subagents, teammates, and workflow agents to the selected exact model and remove per-call model selection. See [Claude Code's official subagent documentation](https://code.claude.com/docs/en/sub-agents#run-every-subagent-on-one-model).

Use the existing harness `--api-key-env NAME=value` mechanism to pass these non-secret controls without editing the benchmark's domain prompts, tests, reference code, images, resource limits, or submitted code. Verify the pinned CLI supports the controls, inspect the actual container environment, and check native/session request model identities during substantive review. Runtime controls are prevention, not a replacement for transcript validation. A configured advisor model without an actual request is not evidence of assistance.

Unknown child-model coverage remains a review hold. Actual cross-model requests make an attempt ineligible for pure-model approval. Preserve its raw result, source, transcript, scores, request accounting, identity, and launch evidence. Do not relabel it as pure-model, assume missing usage is zero, manufacture an operator omission, or automatically retry it.

## Active Haiku collection boundary

The prospective enforcement begins with the remaining unlaunched Haiku cells, starting at `iges-cpp-high`, under the exact October 9 authorization and frozen reconciliation in `automation_logs/haiku55-all-evals-oct7/`. Record this runtime-condition boundary explicitly; earlier launches remain under their truthful original conditions. The already completed ICal C++ max attempt with Sonnet child requests remains private and held. The rule does not authorize replacing or rerunning it, publishing other results, or expanding the model collection.
