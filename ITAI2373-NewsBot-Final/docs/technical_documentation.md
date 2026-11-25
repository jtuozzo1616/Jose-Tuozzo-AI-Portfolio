# Technical documentation — NewsBot 2.0
## Architecture
Validated Article records → normalized source text and SHA-256 → hierarchical classifier, LDA/NMF, sentiment and entity extraction → lexical/LSA/neural retrieval → cited answers or structured queries → Streamlit, FastAPI, CLI and JSON reports. Source ID and synthetic flag travel with results. The original BBC midterm pipeline and model remain separate.
## Algorithms and controls
- Count-vector LDA and TF-IDF NMF fit the supplied corpus; normalized topic weights feed K-means, with deterministic seed 42. Monthly means use available ISO dates; missing dates are reported.
- Classification ranks uncalibrated logistic probabilities or SVM margins; fixed taxonomy maps child category to parent. Fold-local TF-IDF prevents leakage in CV.
- Extractive MMR chooses relevant, diverse source sentences. Template enhancement and transparent synonym expansion preserve traceability. Learned MiniLM retrieval and Argos ES→EN are verified in the evidence folder.
- Entity edges are within-document co-mentions; sentiment aggregates by scoring method. Compare language distributions without treating language as nationality or political bias.
- Query intent rules identify topics, sentiment, comparison, entity relationships, export, date and category. Grounded chat maintains bounded session context; HTTP requests remain stateless.
## Configuration
Python 3.11 recommended. See [configuration](../config/settings.py), [installation](../README.md), [API reference](api_reference.md), [user guide](user_guide.md), [deployment](DEPLOYMENT.md). No API key needed for defaults. NEWSBOT_DEMO_ONLY=1 forces local classifier; NEWSBOT_ENABLE_NEURAL=1 exposes opt-in model loading. Limits: 8 MB / 3,000 records, 20 batch selections, 300 records for entity co-mentions, 1,000 query characters.
## Performance and deployment
Bound inputs, cache service engine in API, separate browser sessions, CPU-first defaults. Profiling at production scale, independent benchmarks, authentication, TLS, quotas, observability and model calibration are still necessary. See [architecture and limits](ARCHITECTURE_AND_LIMITS.md).
## Attribution and research
LDA: Blei, Ng & Jordan (2003), JMLR 3, 993–1022. NMF: Lee & Seung (1999), Nature 401, 788–791. Sentence-BERT: Reimers & Gurevych (2019), EMNLP, DOI 10.18653/v1/D19-1410. MMR: Carbonell & Goldstein (1998), DOI 10.1145/290941.291025. Software: scikit-learn, Streamlit, FastAPI, Argos Translate, Sentence Transformers. AI assistance was used for code, evaluation automation, documentation and repository organization; actual individual contributions and course policy must be confirmed.
