# Assignment requirements and evidence check

Student: WU Yile (1155269932). Checked on 2 November 2026 (Hong Kong).

This checklist maps the instructor's Reproducibility Work instructions to actual evidence. It does not certify a grade or exact reproduction of the paper's numerical result.

| Instructor requirement | Evidence in this repository | Assessment |
| --- | --- | --- |
| Individual work using a public, runnable agentic project | LiTS, the instructor's listed project 3; upstream URL and pinned commit in README and configuration; original multi-step chain, policy and environment execute | Covered; AI assistance is disclosed |
| Run the authors' implementation and reproduce a result or behavior | 60 recorded local-model episodes; actions, environment transitions, retries and terminal-error behavior; independent evaluation | Executable behavior verified; the paper's numerical accuracy was not reproduced |
| A meaningful subset is allowed | First ten dataset puzzles, IDs 0-9; excluded pilot puzzle 10; source-data hash and selection disclosed | Covered |
| Record model substitution and settings; explain comparability limits | Model revision, provider/distribution, local MLX runtime with no API endpoint or keys, quantization, temperature, top_p, top_k, token and step budgets, exact prompt change | Covered; paper-to-local score gaps are not attributed solely to the model |
| For stochastic results, 3-5 trials and mean/variance | Seeds 17, 42 and 2026; seed-level rows; mean, sample standard deviation and sample variance in summaries and report | Covered with three trials on the same ten puzzles |
| One isolated, measurable modification | Terminal-state accessor patch; 30 paired offline replays with identical recorded steps | Preserves 8/8 affected boards; character accuracy 0% to 1.73%; word accuracy and failure flags unchanged |
| Report unsuccessful work and explain limitations | Failed prompt intervention retained; small model/subset and offline-replay limits explained; debugging diary | Covered; no claim that the repair improves model reasoning |
| Report at most 10 pages | deliverables/Reproducibility_Report.pdf | 8 pages; includes setup, metrics, reference comparison, modification, results, debug diary and conclusions |
| GitHub README with install and run steps | README.md, requirements-macos.txt, pinned setup/download scripts, audit and replay commands | Covered for the documented Apple Silicon/macOS environment; not a Windows/CUDA package |
| Reviewable changes in commits | Remote history separates protocol, setup, code, report, patches, model manifest, replay, raw evidence and summary uploads | 12 existing commits checked before this documentation update |
| No secrets/API keys committed | No API is used; model/environment excluded; credential-pattern scan of tracked files returns no matches | No matching credential patterns found; scanning is not an absolute guarantee |
| Recorded Zoom presentation link, maximum 15 minutes | Student reports a completed local recording; optional slides and scripts prepared locally | Submission remains incomplete until an accessible recording link is supplied and duration/content are checked |

## Checks rerun in this audit

- Four hand-checked scoring tests passed.
- Independent analysis verified all 60 episodes, source-data hash, official-score agreement and raw call/token totals: 227 measured calls.
- All 30 paired replays passed identical-step, last-observation and terminal-flag assertions.
- The isolated patch passed `git apply --check` against the pinned upstream checkout with its common runtime adaptation.
- All 214 files in the remote main tree matched local Git blob hashes before this documentation update.

No new model inference was performed for this audit. The deterministic known-answer software control is excluded from model performance. The source-code images in the optional revised deck are source excerpts, not screenshots of live experiment execution.

## Items outside repository completeness

Submit all three required items through the course's submission route: the PDF report, an accessible GitHub repository link and an accessible Zoom recording link. The instructor does not separately require slide or script uploads. The previously supplied local MP4 path was unavailable during this audit; do not treat this checklist as a review of the recording.

The assignment permits documented substitutions and emphasizes explaining what does and does not reproduce. This package reports a negative numerical result and a verified behavior/reporting defect. Acceptance of that reproduction scope and any course-specific AI-assistance policy remain the instructor's assessment.
