# User guide and FAQ
## Quick start
Clone the repository, cd final-newsbot-2.0, install `pip install -r requirements-dev.txt`, run `streamlit run app.py`. Open the printed localhost URL. Start with the fictional corpus, or import approved CSV/JSONL with article_id,title,body and optional category, language, source, published_at (ISO), synthetic, url.
## Five workflows
1. Command Center: review corpus and download metadata. Import your own permitted articles in the sidebar.
2. Article Lab: choose source, read summary, taxonomy and ranked classifier scores, inspect entity candidates and digest.
3. Search & Languages: search in English/Spanish/French/German, filter language, optionally expand domain terms, compare coverage and translate if pack installed.
4. Grounded Chat: ask about AI chip measurements, inspect IDs, ask “Tell me more”; unrelated queries should abstain. Expand structured questions, choose preferences, run “Compare tech topics across languages” and export JSON.
5. Research Lab: run stratified CV, select LDA or NMF, inspect clusters and available dated trend chart, co-mentions and batch report.
## FAQ
- No result? Change the query or import relevant documents. Relevance is not truth.
- No translation? Install Argos language packs; never treat lexical pivot as translation.
- No neural model? Enable the environment flag and install optional requirements; download requires network.
- No trend? Supply correctly dated records spanning multiple months. Unknown dates stay unknown.
- Classifier unavailable? Train on sufficient labeled data; training fit is not an independent test.
- Memory pressure? Use a smaller corpus; batch export is bounded. Do not publish confidential/copyrighted text.
## Tutorials and demonstration
See [executed integrated notebook](../evidence/Final_NewsBot_2.0_Executed.ipynb), [seven tutorials](../notebooks/), [browser captures](../evidence/screenshots/), [oral demonstration](ORAL_DEFENSE.md). A student-recorded video is still required for the video-demonstration documentation item; screenshots are not a recording.

## Real-data live demonstration
Run `python run_real_evidence.py --export-local` from final-newsbot-2.0. With instructor-approved access to the historical BBC data, import `data/raw/bbc_demo_private.jsonl` using the sidebar. This file is excluded from Git; do not redistribute copyrighted content. For the optional neural editorial draft install requirements-generation.txt and set NEWSBOT_ENABLE_NEURAL=1; model output is an unverified draft.
