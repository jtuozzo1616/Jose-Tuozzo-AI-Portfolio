# Portfolio verification — November 2026

## Reproducibility and evidence matrix

| Project | Evidence checked in portfolio review | Remaining limitations |
|---|---|---|
| PiDog Lab 10 | 8/8 offline unit tests passed; source and tests recovered | Physical course trials not independently executed |
| Buddy | Autonomy simulator/parser self-test and V9 eight-assertion self-test passed; archive syntax checked | Original hardware dependency chain incomplete |
| NewsBot final | Canonical README reports 38 passing CI tests, 90.8% historical BBC CV accuracy and 0.9079 macro-F1; executed Colab evidence linked | No new training or live-demo test in this review |
| NewsBot midterm | Published 288-article historical holdout: 96.18% accuracy | Separate experiment, not directly comparable to final |
| RoboGuide | Stored benchmark JSON confirms development MRR@5 0.7742→0.8387 and tied test MRR@5 1.0 | Small, hand-authored benchmark |
| HealthLens | Canonical README contains run steps, dependencies, fictional data and test commands | No clinical validation; no new run |
| Housing | Notebook JSON parsed: 11/11 code cells executed; no saved errors; final shape 21,609×17 | No independent fresh regression metrics |
| Matplotlib | Notebook JSON parsed: 7/7 code cells executed; no saved errors | Saved evidence, not a fresh run |
| Seaborn and three CV labs | Files exist in the public repository tree; project-level dependency/data guidance added | Large notebook payloads unavailable through connector; no fresh run |
| Waste classification | Notebook JSON parsed; stored classification output is 0.20 accuracy on 120 samples; notebook includes synthetic fallback | Real-data provenance of that output not established; not a validated real-data score, no 90% claim |

## Reviewer quick start

Clone the portfolio and run the [offline robot checks](../ITAI2374-PiDog/README.md). For flagship AI systems follow their project-local install/test instructions. For historical notebooks see each course README and dependency notes. Prefer isolated environments; GPU and public data access may be required.

## Access and submission

GitHub repository metadata confirms public visibility. The connector authenticated successfully, but anonymous web access could not be tested in this environment. The student should open the portfolio URL in an incognito window before uploading the PDF. Physical media were not available; selected historical terminal excerpts are included instead, with validation limits clearly stated.
