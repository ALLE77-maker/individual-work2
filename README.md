# Reproducing LiTS Crosswords

WU Yile (1155269932), FTEC5660. All submission materials are in English.

This project executes the authors' LiTS crossword chain with a free local model. An initial letter-consistency prompt experiment returns zero word accuracy. A separate debugging follow-up tests one isolated accessor fix that preserves the last observed board after a terminal error. The original agent loop, action validation, retry logic and crossword transition run from a pinned public repository.

## Reproduction boundary

The reference is the Crosswords chain row of Table 3 in [Li and Tao (2026)](https://aclanthology.org/2026.acl-demo.5/): 10.33% word accuracy and 6.67% puzzle exact match with Claude 3.5 Sonnet on 30 puzzles. This project uses a quantized Qwen2.5-3B-Instruct model and the first ten source puzzles. It reproduces executable behavior and evaluation under changed conditions. It does not claim exact replication of the paper's numbers or its MCTS study.

Read `PROTOCOL.md` for the prespecified experiment. The only difference between measured conditions is the appended prompt instruction. Model substitution and runtime adaptations apply to both.

Read `PROTOCOL_STATE_FIX.md` for the follow-up designed after those outcomes. It replays all 30 original-prompt episodes, with identical observations and no new model calls. The fix restores all 8 affected boards and recovers 1.73% mean character accuracy (sample SD 0.83 percentage points). Word accuracy remains zero and all terminal errors remain visible. This is a state-reporting correction, not improved model reasoning. The original paper's numerical performance did not reproduce under this local setup.

## Files

- `deliverables/Reproducibility_Report.pdf`: report of at most ten pages.
- `deliverables/Reproducibility_Report.md`: editable report source.
- `deliverables/Reproducibility_Presentation.pptx`: editable slides with speaker notes.
- `deliverables/Presentation_Script.md`: English narration for a presentation below 15 minutes.
- `results/main/`: 60 measured episodes, all calls including retries, configurations and audit outputs.
- `results/main/trial_metrics.csv`: six trial-level summaries.
- `references/model_manifest.json`: model revision and asset hashes.
- `patches/lazy_imports.patch`: shared infrastructure adaptation.
- `patches/preserve_terminal_snapshot.patch`: the isolated state-accessor correction, verified against the pinned source.
- `results/state_fix/`: paired offline replay and deterministic software sanity control, separate from live LLM results.
- `scripts/`: setup, downloads, experiment, independent analysis and hand-checked scoring tests.

## Environment and installation

The measured setup uses Apple Silicon, 24 GiB memory and macOS 26.4. MLX provides local Metal inference. This runtime is not intended for Windows or a CUDA host. No API key or paid account is needed. Internet is needed for installation and public asset downloads, then inference runs offline. Model weights require about 1.74 GB. Do not add weights, virtual environments or credentials to Git.

Use Python 3.12 and Git:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-macos.txt
python scripts/setup_runtime.py
python scripts/download_assets.py
```

`setup_runtime.py` retrieves commit `1ef347bee7b3f2c10dc504342589b8c951794c2d` of [LiTS](https://github.com/xinzhel/lits-llm), then applies the lazy-import patch. It refuses to reset a checkout at a different revision. The common adaptation avoids unused training and memory imports. It does not change the agent loop or evaluation.

`download_assets.py` uses the saved model revision when a manifest is present. It verifies the complete tensor byte length and records SHA256 hashes. `download_model_parallel.py` is an optional checked-range recovery tool if a connection truncates a model file. Keep partial downloads until their integrity is resolved.

## Execute the experiment

```sh
python scripts/test_scoring.py
python scripts/run_experiment.py --pilot
python scripts/run_experiment.py
python scripts/analyze_results.py
python scripts/replay_state_fix.py
```

The pilot uses puzzle 10 and is excluded from reported outcomes. The main run uses puzzle IDs 0-9, seeds 17/42/2026 and both prompt conditions. It resets the seed for every episode and alternates condition order. Each episode has a ten-step budget, temperature 0.8, top_p 0.95, top_k 50 and a 32-token generation cap. Original validation retries can increase temperatures and call counts. A short warm-up precedes the measured episodes and is excluded from totals.

The experiment preserves raw calls before evaluation. Resume uses completed episode files, checks configuration consistency and archives interrupted call logs separately. To obtain a wholly fresh run, pass `--output results/new_run`; the analysis script currently expects `results/main`, so either adapt its input path deliberately or preserve the original evidence and compare separately.

The replay script reconstructs identical trajectories under the original accessor and a subclass with only the proposed accessor change. A separate deterministic software test fills five known-answer rows and appends a synthetic error. It verifies the defect and the fix, and is explicitly not an LLM performance result.

To apply the correction to upstream code after reproducing the original study:

```sh
git -C vendor/lits-llm apply ../../patches/preserve_terminal_snapshot.patch
```

Keep this correction separate from original baseline execution. The live experiment refuses additional upstream modifications. The replay already tests the fix through a subclass and does not require applying the patch.

## Audit without running the model

After fetching the exact upstream data with `setup_runtime.py`, these commands need only the Python standard library:

```sh
python scripts/test_scoring.py
python scripts/analyze_results.py
```

The audit recomputes final word and character scores directly from the grid and original dataset. It checks all 60 episode scores, official goal-check agreement, call counts, token totals and dataset hashes. `evidence_manifest.json` records hashes for completed episode evidence. The checked live-study and state-fix summaries supply the numbers in the report and slides.

Mean, sample standard deviation and sample variance refer to three seed-level averages on the same ten puzzles. Repeated episodes do not create additional independent puzzle samples. Invalid proposal rate includes retries. Letter conflict rate uses valid proposals as its denominator. Local inference seconds exclude downloads, model loading and warm-up.

## Report and presentation

The PDF and slide deck are prepared from audited measurements. The report builder requires ReportLab. Slide source uses the Codex bundled Artifact Tool and resides in `presentation_source/build_deck.mjs`; the distributed PPTX remains editable without that authoring environment.

```sh
python -m pip install reportlab
python scripts/build_report.py
```

The generated speaking script is designed for a short presentation, with room to demonstrate one saved trajectory. The student must personally record the Zoom presentation, keep it at or below 15 minutes, and submit a working recording link. A GitHub repository link is also required by the assignment.

## Source and assistance

LiTS source code remains the authors' Apache-2.0 work, retrieved separately at the recorded revision. Dataset content is used from the same upstream repository. The model derives from [Qwen2.5-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct), using the [MLX community 4-bit distribution](https://huggingface.co/mlx-community/Qwen2.5-3B-Instruct-4bit). Review the upstream model card and license for reuse terms.

AI assistance supported code, experiment execution, analysis and writing. The logs reflect actual local inference. The student should review the package and deliver their own explanation. No API credentials belong in this repository.
