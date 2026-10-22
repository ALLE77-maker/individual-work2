# Validation record

- All 60 live episodes independently re-evaluated against the pinned source data.
- Original evaluator agrees with independent final-grid scores in every episode.
- Raw call counts, generated-token totals and inference-time totals agree with episode records.
- Four hand-checked scoring unit tests pass.
- All 30 state-fix replays use identical recorded steps and preserve terminal-error flags.
- The deterministic answer-key control verifies five environment transitions, the original accessor defect, the fixed accessor and the empty-history fallback. It is not a model-performance result.
- The small accessor patch passes git apply --check against the pinned upstream source.
- PDF has 8 pages. All 8 rendered pages were visually inspected.
- PPTX has 10 slides, speaker notes, editable evidence tables and a native chart with an embedded data workbook. Artifact Tool package, layout, font, chart-data and re-import checks pass. All 10 slide renders were visually inspected. The deck was not opened in native PowerPoint.
- A credential-pattern scan of tracked files returned no matches. Model weights and the local environment are excluded from upload.

The paper's numerical accuracy did not reproduce with the substituted local model. The successful modification repairs terminal-state reporting and does not increase complete-word accuracy.
