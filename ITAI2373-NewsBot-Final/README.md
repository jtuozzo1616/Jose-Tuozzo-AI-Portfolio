# ITAI 2373 Final — individual portfolio

José Miguel Tuozzo Izaguirre | JoseGroup

[Canonical repository and instructor review](https://github.com/jtuozzo1616/Final-Jose-Group-NewsBot-Intelligence-System) · [Contribution record](docs/CONTRIBUTIONS.md) · [Detailed rubric](docs/CANVAS_VERIFICATION.md) · [Submission files](submission/) · [Executed evidence](evidence/)

This is a complete source snapshot of the canonical final project. The revision is recorded in SOURCE_REVISION.md.

# NewsBot 2.0 — implementation and quick start

[Canonical instructor review and documents](https://github.com/jtuozzo1616/Final-Jose-Group-NewsBot-Intelligence-System) · [Final submission](submission/) · [Evaluation and rubric](docs/FINAL_SUBMISSION_REVIEW.md)

Python 3.11 recommended. From this directory:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python -m newsbot2.cli overview
python -m newsbot2.cli search --query "robot navigation sensors"
python -m newsbot2.cli search --retrieval-mode lsa --query "robot navigation sensors"
python -m newsbot2.cli ask --query "What did the AI chip researchers measure?"
python run_research.py
streamlit run app.py
```

The app includes 30 fictional articles, five categories and four language labels. It uses the trusted historical model from the parent repository when available. Do not load untrusted joblib files. Use the sidebar to import your own licensed CSV or JSONL records. Required fields: article_id, title, body; optional source, published_at, language, category, url, synthetic. Import caps: 8 MB / 3,000 records. The model can train on labeled imported records; a training fit is not a held-out score.

## API

```bash
uvicorn newsbot2.api:app --reload
curl -X POST http://127.0.0.1:8000/search -H "Content-Type: application/json" -d '{"query":"robot cameras sensors","k":3}'
```

Open http://127.0.0.1:8000/docs for the API schema. The HTTP chat route is stateless; the UI maintains session-scoped history.

## Optional learned multilingual models

```bash
python -m pip install -r requirements-advanced.txt
python -m newsbot2.cli search --query "robotica investigación" --multilingual-model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

The initial model download requires internet access. Argos Translate also requires local language packs. Without these assets, the system returns honest unavailable status or uses a documented lexical fallback. LSA is an offline semantic alternative, not equivalent to learned multilingual embeddings. VADER and spaCy assets are optional; sentiment and entities identify fallback methods.

## Reproducibility and scope

- [Permanent verified results](artifacts/verified_final_summary.json), [prior demo results](artifacts/research_results.json) and [current research runner](run_research.py).
- [Design contracts, threats and limitations](docs/ARCHITECTURE_AND_LIMITS.md).
- [Full final rubric crosswalk and evidence map](docs/FINAL_SUBMISSION_REVIEW.md).
- [All current deliverables](submission/).
- [Historical midterm](https://github.com/jtuozzo1616/Final-Jose-Group-NewsBot-Intelligence-System/blob/main/MIDTERM.md).

The bundled corpus and evaluation probes are fictional. The BBC midterm holdout is a separate historical experiment. Source citations do not establish factual truth. No production deployment, independently validated translation or external generalization is claimed.

## References

[scikit-learn text features](https://scikit-learn.org/stable/modules/feature_extraction.html) · [Sentence Transformers](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html) · [Streamlit](https://docs.streamlit.io/) · [Argos Translate](https://argos-translate.readthedocs.io/) · [FastAPI](https://fastapi.tiangolo.com/).
