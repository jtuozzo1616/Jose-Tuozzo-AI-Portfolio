# NewsBot Intelligence System — ITAI 2373 Midterm

**José Miguel Tuozzo Izaguirre**

This is the course portfolio entry for **NewsBot Intelligence System**. The [main repository](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System) contains the maintained source, eight NLP modules, evaluation artifacts and research documentation.

**[Launch in Google Colab](https://colab.research.google.com/github/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System/blob/main/RUN_NEWSBOT_IN_COLAB.ipynb)** · **[Read the research results](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System/blob/main/docs/Technical_Results_Summary.md)** · **[View completed execution](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System/actions/runs/38775732890)**

## Project at a glance

NewsBot uses historical BBC articles to classify stories into business, entertainment, politics, sport and technology. Its eight modules cover data preparation, preprocessing, TF-IDF, POS tagging, syntax, sentiment, supervised classification and named entity recognition.

The recorded experiment retained **1,440 articles** after exact-text deduplication and reserved 288 for testing. The tuned Linear SVM achieved **96.18% holdout accuracy** (277 correct) and **0.9605 macro-F1**. These results describe one historical news dataset; they do not establish how the system would perform on today's reporting.

## Where to find everything

| Deliverable | Link |
|---|---|
| Course notebook | [Midterm_NewsBot_Intelligence_System.ipynb](Midterm_NewsBot_Intelligence_System.ipynb) |
| Reproducible setup | [QUICK_START_EN.md](QUICK_START_EN.md) |
| Figures and evaluation | [outputs/](outputs/) |
| Technical report | [Latest technical report](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System/blob/main/docs/MT_Report_Group_Solo_Jose_Miguel_Tuozzo_Izaguirre_ITAI2373.pdf) |
| Reflection | [Latest two-page PDF](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System/blob/main/docs/NewsBot_Reflection_Solo.pdf) · [Personal reading copy](docs/Personal_Reflection_Reading_Copy.md) |
| Evidence from a completed execution | [GitHub Actions run](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System/actions/runs/38775732890) |
| Reviewer navigation | [Professor's guide in main repository](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System/blob/main/docs/PROFESSOR_REVIEW_GUIDE.md) |

The notebook source is intentionally saved without execution outputs. The successful workflow includes a downloadable executed notebook; figures and summary tables are also visible directly in this folder.

For scope, source attribution, limitations and the optional Streamlit interface, see the [main README](https://github.com/jtuozzo1616/Mid-Term-Jose-Group-NewsBot-Intelligence-System). The professor's dataset-use approval and final submission arrangement should be confirmed separately.
