# Submission checklist

Student: WU Yile (1155269932)
Course: FTEC5660

1. Submit `deliverables/Reproducibility_Report.pdf` (8 pages).
2. Submit the repository link: https://github.com/ALLE77-maker/individual-work2
3. Record your own Zoom presentation using the 10-slide deck and English script. Keep it at or below 15 minutes.
4. Upload the recording to your chosen service and submit an accessible presentation link.
5. This repository is private. Give the instructor access before submitting its link, or change visibility deliberately if the course requires public access.

## Main findings to understand before recording
- The live local-model study contains 60 real episodes and 227 calls, with zero paid API usage.
- Both original and letter-consistency prompts yield zero final word accuracy. This does not reproduce the paper's numerical performance.
- The debugging follow-up identifies a terminal error that makes the state accessor return the initial board.
- One isolated accessor fix preserves all 8 affected boards in the 30 original-prompt episodes. Mean character accuracy recovers to 1.73%, while word accuracy and terminal failures remain unchanged.
- The follow-up uses paired offline replay, not extra live model runs. The answer-key sanity control is a software test and is excluded from model accuracy.

## Recording outline
Slides 1-2: project and reproduction boundary.
Slides 3-5: the observed defect and isolated change.
Slides 6-8: measured replay results and a saved trajectory.
Slides 9-10: unsuccessful prompt experiment, limitations and lessons.

AI assistance supported the package. Review the code, numbers and conclusions before presenting.
