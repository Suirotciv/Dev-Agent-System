# MODELS.md
# Model capability requirements for the agent system.
# Read before your first session.

---

## Minimum system requirement

**All roles require a 128k context window minimum.**

The agent system loads STATE.json, role prompts, feature specs, and code
files into context. Sessions that run out of context mid-task produce
incomplete work and malformed artifacts. 32k or 64k models will hit this
limit on any non-trivial project. Do not use them.

---

## Role requirements

| Role | Minimum model tier | Minimum size | Critical capability |
|------|--------------------|-------------|---------------------|
| Orchestrator | Frontier or strong local | 70B+ | Complex JSON writes, multi-step planning, conflict resolution, scoped reads of a large STATE.json |
| Feature Agent | Mid-tier local or frontier | 32B+ | Instruction following, code generation, and structured JSON output simultaneously |
| Verifier | Mid-tier local or frontier | 32B+ | Blackbox judgment, binary pass/fail on nuanced criteria, evidence writing |
| Infra / Design | Light local or frontier | 14B+ | More constrained scope, simpler outputs, fewer simultaneous demands |

**Frontier models** (Claude Sonnet+, GPT-4o, Gemini 1.5 Pro and above):
meet all role requirements. Use these if available.

**Strong local models** (70B+ at Q4 or higher): suitable for Orchestrator
and Feature Agent. Qwen3 72B, Llama 3.1 70B, Mistral Large. Context window
must be 128k - verify before use.

**Mid-tier local models** (32B-70B at Q4): suitable for Feature Agent and
Verifier. Qwen3 32B, Mistral 7B x 2 (not recommended - see note below).
Require more explicit output format instructions. Expect occasional JSON
formatting failures; the validation scripts will catch them.

**Small local models** (below 32B): not recommended for any role in this
system. They lack the instruction-following reliability needed for structured
output and multi-step planning. If this is all you have, run the system with
a frontier model for Orchestrator and a mid-tier local for Feature Agent.

---

## Known failure modes by model tier

### 70B+ local models
- Occasionally add markdown fences around JSON output (`\`\`\`json`)
- May miscount braces/brackets in complex nested JSON
- Sometimes ignore negative instructions ("do not include X") - rewrite
  as positive instructions ("include only Y")

Mitigation: the output format rules in each agent prompt address these directly.

### 32B-70B local models
- Higher rate of JSON syntax errors under long context pressure
- May truncate output on very long responses - keep sessions focused
- Verifier role works but may miss subtle criteria failures

Mitigation: smaller feature scopes, more frequent session checkpoints.

### Models with less than 128k context
**Do not use.** The system will appear to work and then fail unpredictably
as context fills. The failure mode is silent: the model drops earlier
instructions and produces outputs that look valid but are not.

---

## Tested configurations

These are configurations the system has been validated against. Use them as
a starting point and note your own findings here.

| Model | Role | Context | Notes |
|-------|------|---------|-------|
| Claude Sonnet 4.6 | All roles | 200k | Reference configuration. All features work. |
| Claude Opus 4.6 | Orchestrator | 200k | Best for complex multi-feature coordination. |
| GPT-4o | All roles | 128k | Solid across all roles. JSON output reliable. |
| Qwen3 72B (Q4) | Orchestrator, Feature | 128k | Good. Occasionally adds markdown fences - output rules fix this. |
| Llama 3.1 70B (Q4) | Feature Agent | 128k | Works well for Feature Agent. Weaker on Verifier judgment tasks. |

Add your own findings to this table as you test.

---

## Multi-model configurations

You are not required to use the same model for all roles. A practical
solo-dev configuration for cost efficiency:

```
Orchestrator: frontier model (best judgment, runs infrequently)
Feature Agent: strong local model (runs most frequently, high code output)
Verifier: frontier model (independent judgment matters here)
```

The Orchestrator and Verifier run less frequently than Feature Agents.
Spending more on a better model for those roles is a good tradeoff.

---

## Why you should not use the same model for Feature Agent and Verifier

This is worth stating explicitly because it is tempting to do.

If the Feature Agent and Verifier are the same model with the same training,
they have the same blind spots. A bug that the Feature Agent consistently
misses (due to a gap in training data, a flawed assumption about the spec,
or a common error pattern for that model) will be consistently missed by the
Verifier too.

Independent verification requires actual independence. Use a different model,
or at minimum a different context window with genuinely blackbox access to
the artifact and spec.

---

## Output format reliability

The structured output requirements (JSON envelopes, YAML frontmatter) are
the primary source of friction with local models. Every agent prompt now
includes explicit output format rules. If you encounter recurring formatting
failures with a specific model:

1. Check that the output format rules section is near the top of your
   context (first 500 tokens if possible)
2. Restate the format rule positively: "Output raw JSON only" is more
   reliable than "Do not use markdown fences"
3. Break large tasks into smaller sessions - output quality degrades as
   context fills
4. For Orchestrator sessions: consider providing a template envelope and
   asking the model to fill it in rather than generate the structure from scratch

---

## Context budget reference

| Session type | Typical context use | When to compact |
|-------------|--------------------|-----------------| 
| Orchestrator (full STATE.json read) | 20-40k tokens at start | At 70% |
| Feature Agent (active build) | Grows through session | At 70% |
| Verifier (spec + artifact + criteria) | 15-30k tokens at start | Rarely needed |

At 70% context budget, the Feature Agent should:
1. Write a `SESSION_STATE.md` in the feature directory summarizing completed work
2. Note remaining tasks
3. End the session cleanly

The next session reads `SESSION_STATE.md` first and continues from there.
