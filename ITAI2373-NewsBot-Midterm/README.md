# NewsBot Intelligence System — ITAI 2373 Midterm

**Student:** José Miguel Tuozzo Izaguirre  
**Assignment folder:** `ITAI2373-NewsBot-Midterm`, inside the [personal AI portfolio](https://github.com/jtuozzo1616/Jose-Tuozzo-AI-Portfolio).  
**Canonical repository for ongoing development:** [NewsBot Intelligence System](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System).

This folder contains the **full runnable 36-cell notebook**, Python tools, a copy of verified experimental figures and summary metrics, technical PDF report, and the two-page reflective journal. The source article text is intentionally not published.

## Launch and inspect

- [Open this folder's analytical notebook in Google Colab](https://colab.research.google.com/github/jtuozzo1616/Jose-Tuozzo-AI-Portfolio/blob/main/ITAI2373-NewsBot-Midterm/Midterm_NewsBot_Intelligence_System.ipynb).
- [One-click full project runner in Colab](https://colab.research.google.com/github/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System/blob/main/RUN_NEWSBOT_IN_COLAB.ipynb).
- [The complete original source repository](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System) and [successful end-to-end execution workflow](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System/actions/runs/38491913062).

To re-run from the copied folder:
```bash
python -m pip install -r requirements.txt nbclient nbformat reportlab pillow
python -m spacy download en_core_web_sm
python run_all_and_package.py --github "https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System"
python verify_release.py
```

## Real historical BBC results

After removing 50 exact duplicates from 1,490 labeled articles, the system evaluated 1,440 articles in **five categories** (business, entertainment, politics, sport, tech): **1,152 training; 288 independent held-out test**. The selected model was Linear SVM; train-only tuned cross-validation macro-F1 **0.9801** and holdout accuracy **96.18%** (277/288 correct), macro-F1 **0.9605**. These are measured BBC dataset results, not synthetic test scores. The BBC data are historical single-publisher news from 2004–2005; Health is **not** a trained label.

## Academic deliverables

- [Jupyter notebook](Midterm_NewsBot_Intelligence_System.ipynb), [run manifest](outputs/run_manifest.json), [model comparisons](outputs/model_cv_comparison.csv) and [per-class scores](outputs/per_class_metrics.csv).
- [Eight figures](outputs/), including [confusion matrix](outputs/06_confusion_matrix.png), [NER analysis](outputs/04_ner_analysis.png), [TF-IDF feature plots](outputs/02_tfidf_category_terms.png) and [POS/sentiment charts](outputs/03_linguistic_sentiment.png).
- [Technical report PDF](docs/MT_Report_Group_Solo_Jose_Miguel_Tuozzo_Izaguirre_ITAI2373.pdf) and [exactly two-page reflective journal PDF](docs/NewsBot_Reflection_Solo.pdf).
- [Evidence-based technical findings](docs/Technical_Results_Summary.md), [100-point rubric audit](docs/Submission_Audit_100_Point_Rubric.md), [submission checklist](docs/Execution_and_Submission_Checklist.md) and [individual contributions evidence](docs/Individual_Contributions.md).

**Important:** The journal PDF needs the student's firsthand review and personalization before submission. The instructor requires approval of the selected Kaggle dataset; the project includes an approval **request**, not proof of an approval. The work is attributed to one student, rather than falsely inventing group collaborators. A video script exists, but no optional video is claimed to have been recorded. Actual Canvas upload, grader decisions, and video bonus eligibility cannot be verified by code.

**Notes:** See the canonical README for model limitations, data rights, reproduction and the optional local Streamlit dashboard. The main Jupyter notebook is clean with no saved output cells, while the **executed** notebook is attached to the successful GitHub Actions run.
