# Follow-up protocol: preserve the last observed terminal state

This follow-up was designed after the original 60-episode prompt experiment. It is a debugging follow-up, not a hypothesis preregistered before the first study. The original protocol and results remain unchanged.

## Observed issue
`EnvChain.run()` appends a terminal error step without `next_state` after repeated invalid proposals. `EnvState.env_state` looks only at the final step. If that step has no snapshot, it returns `init_state` instead of the preceding observed board. All 60 live episodes ended in a validation error. Some episodes contain earlier executed placements, yet their reported final board is blank.

## One isolated modification
Replace the current-state accessor with a reverse search for the latest nonempty `next_state`. Fall back to `init_state` only if no observed snapshot exists. Retain the terminal error step, error status, all model calls and all observed transitions.

## Fixed replay design
- Include all 30 original-prompt episodes, puzzle IDs 0-9 and seeds 17/42/2026.
- Reconstruct the recorded steps in the original EnvState and a subclass with only the accessor changed.
- Pair the original and fixed accessors on identical observations. Do not generate new language-model outputs or call the fixed accessor a new live agent run.
- Primary software outcome: how many episodes retain their last observed placement rather than reverting to the empty initial board.
- Secondary outcomes: final character and word accuracy, computed independently, and exact puzzle success.
- Report seed-level mean, sample SD and sample variance. Keep the terminal-error rate unchanged.
- Add a separate deterministic sanity test using known ground-truth row placements, with an appended error, to verify the environment and demonstrate the accessor defect. This is a software test using the answer key, not an LLM performance measurement.
- Show an illustrative pair with the largest character-accuracy difference, then lowest seed and puzzle ID. This is an intentionally selected example.
- Preserve the original zero word-accuracy results and the unsuccessful prompt intervention in the report.

## Scope of inference
This modification repairs state reporting. It does not improve the model's proposed words, resolve invalid outputs or establish the paper's reported performance. Any recovered score reflects already observed letters rather than new reasoning.
