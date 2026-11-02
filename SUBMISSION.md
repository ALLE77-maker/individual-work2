# Submission checklist

Student: WU Yile (1155269932)
Course: FTEC5660

1. Submit `deliverables/Reproducibility_Report.pdf` (8 pages).
2. Submit the repository link: https://github.com/ALLE77-maker/individual-work2
3. Check your recorded Zoom presentation. The revised local deck has 11 slides; the short English script has matching page-turn cues. Keep the video at or below 15 minutes.
4. Upload the recording to your chosen service and submit an accessible presentation link.
5. Verify repository access before submitting its link. A public repository should open without signing in; a private repository requires instructor access.

## Key findings covered by the presentation
- The live local-model study contains 60 real episodes and 227 calls, with zero paid API usage.
- Both original and letter-consistency prompts yield zero final word accuracy. This does not reproduce the paper's numerical performance.
- The debugging follow-up identifies a terminal error that makes the state accessor return the initial board.
- One isolated accessor fix preserves all 8 affected boards in the 30 original-prompt episodes. Mean character accuracy recovers to 1.73%, while word accuracy and terminal failures remain unchanged.
- The follow-up uses paired offline replay, not extra live model runs. The answer-key sanity control is a software test and is excluded from model accuracy.

## Recording outline
Slides 1-2: project and reproduction boundary.
Slides 3-5: the observed defect and isolated change.
Slides 6-7: measured replay results.
Slide 8: source-code assertions that isolate the fix.
Slide 9: a saved trajectory.
Slides 10-11: unsuccessful prompt experiment, limitations and lessons.

AI assistance supported the package. Review the code, numbers and conclusions before presenting.
