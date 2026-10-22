# Experiment protocol (written before measured runs)

## Question
Can LiTS execute multi-step Crosswords episodes with a free local model, and does one explicit letter-consistency instruction change the final word accuracy?

## Source and target
- Instructor list project 3: LiTS, https://github.com/xinzhel/lits-llm.
- Upstream commit: `1ef347bee7b3f2c10dc504342589b8c951794c2d`.
- Paper: Li and Tao (2026), https://aclanthology.org/2026.acl-demo.5/.
- Primary reported reference: Table 3 Crosswords chain, 6.67% puzzle exact match and 10.33% word accuracy on 30 examples with Claude 3.5 Sonnet.
- Reproduction type: runnable capability and metric reproduction under a substituted model, not an exact numerical replication.
- The paper does not identify the precise 30 puzzle IDs or a full chain configuration in its experimental setup. Record this as a comparability limit.

## Fixed design
- Data: first 10 puzzles (IDs 0 through 9) in upstream `demos/crosswords/data/mini0505.json`, without outcome-based selection.
- Model: public MLX Qwen2.5-3B-Instruct, 4-bit. Record resolved model revision and asset hashes.
- Agent: upstream EnvChain with EnvGroundedPolicy and CrosswordsTransition.
- Maximum steps: 10. Policy temperature: 0.8. Generation cap: 32 tokens per call. Keep the upstream validation and three-attempt retry behavior.
- Three trial seeds: 17, 42, 2026. Reset the seed at the start of each episode. Use the same seed for each paired baseline and modification run.
- Baseline: upstream crossword policy prompt.
- Modification: append one instruction requiring consistency with visible intersection letters. No ground-truth answers enter the model prompt.
- One model substitution applies equally to both conditions and is separate from the experimental prompt change.

## Outcomes
- Primary: final word accuracy = correct final horizontal and vertical words / 10, averaged over the ten puzzles per seed.
- Secondary: exact puzzle success, character accuracy, model calls, generated tokens, elapsed inference time, invalid proposal rate, and terminal errors.
- Report every trial, trial mean, sample standard deviation and sample variance. Three seeds do not establish broad statistical significance.
- Preserve every call, including retries, alongside the final trajectories and official goal-check results.
- Independently recompute word accuracy directly from the final grid and check agreement with the upstream evaluator.
- Report decreases and null effects honestly. Do not tune on measured outcomes.

## Pilot and boundary
A separate pilot may use puzzle 10 to verify imports, decoding, logs and trajectory serialization. Pilot outcomes do not enter the reported ten-puzzle comparison. If a feasibility issue forces a protocol change, record the change before the measured experiment.

## Resources
No paid API calls. Local electricity and existing hardware are not priced. Model files and virtual environments are excluded from the submission repository.
