# API and public library reference
Start: `uvicorn newsbot2.api:app --reload`. Interactive schema: http://127.0.0.1:8000/docs.
| Method | Endpoint | Contract |
|---|---|---|
| GET | /health | version and status |
| GET | /overview | corpus counts, model method |
| GET | /articles | source inventory |
| GET | /articles/{article_id}/analysis | category, sentiment, entities, summary, provenance; 404 for unknown |
| POST | /search | JSON query, k (1–10); ranked source IDs |
| POST | /chat | JSON query, k; stateless cited excerpts |
| GET | /topics?n=4 | baseline NMF |
| GET | /advanced/topics?method=lda&n=4 | LDA/NMF, weights, clusters, evolution |
| GET | /advanced/sentiment | monthly scores by method |
| GET | /advanced/entities | source-linked co-mentions |
| GET | /advanced/languages | coverage by language |
| POST | /advanced/query | intent, filters and structured evidence |
Library: Article validates fields and computes sha256; import_articles(path) validates CSV/JSONL; NewsBotEngine(articles,classifier,embedding_model,retrieval_mode) exposes overview, analyze(id), search(query,k,language), ask(question), topics(n_topics), train_local_classifier(), translate(text,src,dst). Classifier.train(articles) fits labeled input, predict(text) ranks scores. Retriever.search returns SearchHit objects. Conversation.ask maintains bounded history. Advanced functions are documented in advanced.py. evaluate_classification_cv returns out-of-fold accuracy, macro-F1, confusion matrix and per-class report; evaluate_retrieval returns MRR and recall. Invalid inputs return validation errors; unavailable models do not fabricate results. No network article fetching through API.
