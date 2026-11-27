# House Prices Regression — Machine Learning coursework

## Problem and approach

Explore housing features and prepare data for regression using cleaning, encoding, scaling and exploratory plots. The existing notebook is an executed preprocessing artifact, not a complete independently verified model-training pipeline.

## Code, data and results

- [Preprocessing notebook](MidTerm_Group3.ipynb) — 11 executed code cells with no saved error outputs; final saved dataframe shape is 21,609 rows × 17 columns.
- [Housing CSV](Raw_Housing_Prices3.csv) — input already present in this directory.
- [Detailed analysis](Midterm_Detailed_Analysis.docx) — accompanying academic document.

## Run

Install `python -m pip install -r requirements.txt`. In Google Colab, upload Raw_Housing_Prices3.csv to /content/ and run the notebook in order. In local Jupyter, change the first CSV path from /content/Raw_Housing_Prices3.csv to Raw_Housing_Prices3.csv and run from this directory. Do not treat preprocessing artifacts as independently verified regression performance.

## Learning and next steps

The notebook illustrates data cleaning, feature preparation and visualization. For a future validated model, split before fitting preprocessing, exclude IDs and leakage features, compare regression baselines on the same holdout, and record MAE/RMSE/R² from fresh execution. The earlier README's X.XX metric placeholder has been removed; no unsupported score is claimed.
