# Verified execution evidence

| Artifact | Scope |
|---|---|
| [Master Colab notebook](NewsBot_JoseT_2_0_Master_Colab.ipynb) | Exact student-supplied executed file, pinned revision 5e415062; eight sections, 33 tests, 13 PNGs |
| [Colab integrity manifest](colab_master_verification.json) | Original SHA-256 and Git blob |
| [Latest test run](https://github.com/jtuozzo1616/Final-Jose-Group-NewsBot-Intelligence-System/actions/runs/45698267399) | 38 tests, 1 warning, 2.80 s; pypdf 6.21.4 and python-docx 1.2.0 |
| [Latest QA summary](final_qa_summary.json) | Commit and test scope |
| [BBC final pipeline](real_bbc_final_evaluation.json) | 250 historical records, 90.8% accuracy, 0.9079 macro-F1 |
| [MiniLM](embedding_results.json) | 384-dimensional vectors and four controlled retrieval probes |
| [Argos](translation_results.json) | Three actual ES→EN translations |
| [FLAN-T5](generation_results.json) | Three actual neural drafts, source references |
| [Browser screenshots](screenshots/) · [recordings](video/) | Real Chromium interactions; not the latest hosted site |
| [Executed integrated CI notebook](Final_NewsBot_2.0_Executed.ipynb) · [seven executed tutorials](tutorials/) | Supporting reproducibility evidence |

The historical BBC midterm is separate. The master notebook displays archived neural and real-data results rather than rerunning them by default. The user confirmed the hosted import workflow after the dependency fix; anonymous public access was not independently verified. 
