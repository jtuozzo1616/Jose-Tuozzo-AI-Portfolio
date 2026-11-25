"""NewsBot Intelligence System 2.0 — bonus Streamlit web frontend.
Run: streamlit run app.py. Entire default demo works without API keys.
"""
from __future__ import annotations
from collections import Counter
import io,json,tempfile,os
from pathlib import Path
import streamlit as st
import pandas as pd
from newsbot2.engine import NewsBotEngine
from newsbot2.analysis import Classifier
from newsbot2.io import import_articles
from newsbot2.advanced import discover_topics,sentiment_timeline,entity_network,language_comparison,structured_query,expand_query,hierarchy,export_report

st.set_page_config(page_title='NewsBot Intelligence · 2.0',page_icon='🗞️',layout='wide',
                   initial_sidebar_state='expanded')
ROOT=Path(__file__).parent

st.markdown('''<style>
:root { --navy: #101c30; --ink: #dfe9f9; --muted: #a1b2c6; --accent: #59d1c6; }
[data-testid="stAppViewContainer"] { background:radial-gradient(ellipse at top left,#192d43 0%,#0a121f 63%);color:#e8eef7; }
[data-testid="stSidebar"] { background:#111e30; }
h1,h2,h3 { letter-spacing:-.035em; }
div[data-testid="stMetric"] { background:#15273c;border:1px solid #2a475d;padding:17px;border-radius:12px; }
.stTabs [data-baseweb="tab-list"]{gap:14px}.stTabs [data-baseweb="tab"]{padding:10px 17px}
.newshero {padding:28px 30px;border:1px solid #294960;border-radius:16px;
 background:linear-gradient(108deg,#183951,#0e1e32 65%);margin-bottom:23px}
.newshero h1{font-size:42px;margin:5px 0 9px}.eyebrow{color:#59d1c6;text-transform:uppercase;letter-spacing:.13em;font-size:12px;font-weight:700}
.caption{color:#b2c4d6;font-size:14px}
</style>''',unsafe_allow_html=True)


def get_engine():
    if 'engine' not in st.session_state:
        trusted=next((p for p in (ROOT/'outputs'/'newsbot_classifier.joblib', ROOT.parent/'outputs'/'newsbot_classifier.joblib') if p.is_file()), ROOT/'outputs'/'newsbot_classifier.joblib')
        if trusted.exists() and os.getenv('NEWSBOT_DEMO_ONLY') != '1':
            try:
                clf=Classifier.from_trusted_joblib(str(trusted))
                st.session_state.engine=NewsBotEngine(import_articles(ROOT/'data/demo_news.jsonl'),classifier=clf)
            except Exception:
                st.session_state.engine=NewsBotEngine(import_articles(ROOT/'data/demo_news.jsonl'))
                st.session_state.engine.train_local_classifier()
        else:
            st.session_state.engine=NewsBotEngine(import_articles(ROOT/'data/demo_news.jsonl'))
            st.session_state.engine.train_local_classifier()
        st.session_state.chat_history=[]
    return st.session_state.engine

eng=get_engine()
with st.sidebar:
    st.markdown('### 🗞️ NewsBot 2.0')
    st.caption('ITAI 2373 · Final capstone')
    st.markdown('**Corpus and provenance**')
    uploaded=st.file_uploader('Import your own articles (.csv / .jsonl)',type=['csv','jsonl'],
          help='Columns: article_id, title, body. Optional: category, language, source, synthetic.')
    if uploaded is not None and st.button('Load uploaded corpus',use_container_width=True):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                dest=Path(tmp)/('upload.'+uploaded.name.rsplit('.',1)[-1].lower())
                dest.write_bytes(uploaded.getvalue())
                if dest.stat().st_size>8_000_000:raise ValueError('8 MB maximum')
                articles=import_articles(dest)
            st.session_state.engine=NewsBotEngine(articles)
            st.session_state.chat_history=[]
            st.rerun()
        except Exception as exc:st.error(str(exc))
    if st.button('Restore synthetic demonstration',use_container_width=True):
        trusted=next((p for p in (ROOT/'outputs'/'newsbot_classifier.joblib', ROOT.parent/'outputs'/'newsbot_classifier.joblib') if p.is_file()), ROOT/'outputs'/'newsbot_classifier.joblib')
        clf=Classifier.from_trusted_joblib(str(trusted)) if trusted.exists() and os.getenv('NEWSBOT_DEMO_ONLY') != '1' else None
        st.session_state.engine=NewsBotEngine(import_articles(ROOT/'data/demo_news.jsonl'),classifier=clf)
        if clf is None:st.session_state.engine.train_local_classifier()
        st.session_state.chat_history=[]
        st.rerun()
    st.divider()
    if os.getenv('NEWSBOT_ENABLE_NEURAL') == '1':
        if st.button('Enable multilingual embeddings',use_container_width=True):
            with st.spinner('Loading opt-in neural model...'):
                current=st.session_state.engine
                candidate=NewsBotEngine(current.articles,classifier=current.classifier,embedding_model='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
                if candidate.retriever.method.startswith('multilingual-embeddings:'):
                    st.session_state.engine=candidate
                    st.session_state.chat_history=[]
                    st.rerun()
                else:
                    st.error('Neural model unavailable. Existing retrieval unchanged.')
    st.caption('No paid API key required · No network fetches · All default articles are fictional.')
    st.warning('This is an editorial research assistant, not a live news feed or fact-checker.',icon='⚠️')

st.markdown('''<div class="newshero"><div class="eyebrow">NLP · Multilingual search · Grounded conversational AI</div>
<h1>NewsBot Intelligence <span style="color:#59d1c6">2.0</span></h1>
<div class="caption">An explainable, local-first intelligence workspace for exploring news content and its provenance.</div></div>''',unsafe_allow_html=True)

stats=eng.overview()
m1,m2,m3,m4=st.columns(4)
m1.metric('Articles',stats['total_articles'])
m2.metric('Topics represented',len(stats['label_distribution']))
m3.metric('Synthetic records',stats['synthetic_articles'])
m4.metric('Retrieval engine','Embeddings' if 'embeddings' in stats['retrieval_method'] else 'TF-IDF')

tabs=st.tabs(['📰 Command Center','🔬 Article Lab','🔎 Search & Languages','💬 Grounded Chat','📈 Research Lab'])
with tabs[0]:
    st.subheader('Corpus intelligence at a glance')
    left,right=st.columns([1,1.7])
    with left:
        st.markdown('**Topic composition**')
        st.bar_chart(pd.Series(stats['label_distribution'],name='Articles'))
        st.markdown('**Language hints**')
        st.dataframe(pd.DataFrame({'Language':list(stats['language_hints']),
           'Documents':list(stats['language_hints'].values())}),hide_index=True,use_container_width=True)
    with right:
        st.markdown('**Browse source inventory**')
        table=pd.DataFrame([{'ID':a.article_id,'Headline':a.title,'Topic':a.category,
            'Lang':a.language,'Source':a.source,'Synthetic':a.synthetic} for a in eng.articles])
        st.dataframe(table,hide_index=True,use_container_width=True,height=410)
        st.download_button('Export corpus metadata',table.to_csv(index=False).encode('utf-8'),
                           'newsbot_corpus_manifest.csv',mime='text/csv')
    st.info('The demonstration is fictional. Midterm BBC metrics are published separately and are NOT results for this corpus. Default category model may be trained on synthetic demo records only.')

with tabs[1]:
    st.subheader('Multi-layer content analysis')
    if not eng.articles:st.info('Load a corpus to analyze an article.')
    else:
        selected=st.selectbox('Choose source article',list(eng.by_id),
         format_func=lambda i: f'{eng.by_id[i].title} ({i})')
        doc=eng.analyze(selected)
        st.caption(f"Source: {doc['provenance']['source']} · SHA-256: {doc['provenance']['sha256'][:24]}…")
        if doc['provenance']['synthetic']:st.warning('This selected item is a fictional educational fixture.')
        st.subheader(doc['article']['title'])
        st.write(doc['article']['body'])
        left,right=st.columns(2)
        with left:
            st.markdown('**Extractive summary — original sentences**')
            st.write(doc['summary']['text'])
            st.caption(f"Method: {doc['summary']['method']} · Sentence positions: {doc['summary']['selected_sentence_indices']}")
            st.markdown('**Category classifier**')
            st.json(doc['classification'])
            st.json(hierarchy(doc['classification']))
        with right:
            st.markdown('**Sentiment / language hint**')
            st.json({'sentiment':doc['sentiment'],'language':doc['language']})
            st.markdown('**Named entities**')
            if doc['entities']['mentions']:
                st.dataframe(pd.DataFrame(doc['entities']['mentions']),hide_index=True,use_container_width=True)
            else:st.caption('No entity candidates detected in available offline mode.')
            st.caption(doc['entities']['method']+' · '+doc['entities']['warning'])
        with st.expander('Content enhancement — editor review required'):
            st.write(doc['enhancement']['headlines'])
            st.code(doc['enhancement']['short_blurb'],language=None)
            st.caption(doc['enhancement']['guardrail'])
            if os.getenv('NEWSBOT_ENABLE_NEURAL') == '1' and st.button('Generate pretrained editorial draft'):
                from newsbot2.generation import generate_brief
                with st.spinner('Running opt-in pretrained model...'):
                    st.json(generate_brief(eng.by_id[selected]))

with tabs[2]:
    st.subheader('Cross-language evidence discovery')
    st.caption('EN / ES / FR / DE keyword-pivot fallback. Optional multilingual sentence embeddings enable true semantic retrieval.')
    query=st.text_input('What are you researching?',value='investigación de inteligencia artificial')
    language_filter=st.selectbox('Source language', ['All','en','es','fr','de','und'])
    expand=st.checkbox('Expand query with domain terms',value=False)
    if expand: st.json(expand_query(query))
    results=eng.search(expand_query(query)['expanded'] if expand else query,k=6,language=None if language_filter=='All' else language_filter)
    if not results:st.warning('No relevant articles found. Try a term present in the corpus.')
    for hit in results:
        with st.container(border=True):
            st.markdown(f"**{hit['title']}**  ·  `{hit['article_id']}`")
            st.write(hit['excerpt'])
            st.caption(f"{hit['source']} | method: {hit['retrieval_method']} | similarity: {hit['score']:.3f} (not probability)")
    with st.expander('Compare language coverage and source context'):
        st.dataframe(pd.DataFrame(language_comparison(eng.articles)),hide_index=True)
        st.caption('Language does not establish regional viewpoint; compare actual source context and editorial framing manually.')
    st.divider()
    st.markdown('**Optional fully offline machine translation**')
    src=st.selectbox('From',['es','en','fr','de'],index=0)
    dst=st.selectbox('To',['en','es','fr','de'],index=0)
    text=st.text_area('Text to translate',value='La universidad investiga inteligencia artificial.')
    if st.button('Translate using installed Argos pack'):
        st.json(eng.translate(text,src,dst))

with tabs[3]:
    st.subheader('Ask the corpus — answers with article IDs')
    st.caption('Answers contain extracted passages, not invented facts. Low-support questions trigger abstention.')
    for item in st.session_state.chat_history:
        with st.chat_message('user'):st.write(item['question'])
        with st.chat_message('assistant'):
            st.write(item['answer'])
            if item['citations']:st.caption('Sources: '+', '.join('['+s['article_id']+']' for s in item['citations']))
    with st.form('ask_corpus_form',clear_on_submit=True):
        q=st.text_input('Question about the loaded articles',placeholder='What did the robotics team measure?')
        send=st.form_submit_button('Ask NewsBot',type='primary')
    if send and q.strip():
        reply=eng.ask(q)
        st.session_state.chat_history.append({'question':q,**reply})
        with st.chat_message('user'):st.write(q)
        with st.chat_message('assistant'):
            st.write(reply['answer'])
            if reply['citations']:st.caption('Sources: '+', '.join('['+s['article_id']+']' for s in reply['citations']))
    with st.expander('Structured questions, preferences and report export'):
        pref=st.multiselect('Preferred categories',sorted({a.category for a in eng.articles if a.category}))
        sq=st.text_input('Editorial question',value='Compare tech topics across languages')
        if st.button('Run structured query'):
            st.session_state.structured=structured_query(eng,sq,preferred_categories=pref)
        if 'structured' in st.session_state:
            st.json(st.session_state.structured)
            st.download_button('Download query report',export_report(st.session_state.structured),'newsbot_report.json','application/json')
    if st.button('Clear conversation',key='clear_chat'):
        st.session_state.chat_history=[]
        eng.chat.history=[]
        st.rerun()

with tabs[4]:
    st.subheader('Topic modeling and transparent evaluation')
    topics=eng.topics(n_topics=5)
    if topics.get('status')=='ok':
        st.dataframe(pd.DataFrame([{'Topic':f"T{i['topic_id']}",
          'Top terms':', '.join(i['terms']),
          'Documents assigned':i['article_count_top_topic']} for i in topics['topics']]),
          hide_index=True,use_container_width=True)
    else:st.json(topics)
    st.caption('NMF is unsupervised, corpus-specific, and does not itself establish a true editorial topic.')
    if st.button('Run stratified cross-validation on loaded labels'):
        from newsbot2.evaluation import evaluate_classification_cv
        with st.spinner('Evaluating on available labeled records...'):
            ev=evaluate_classification_cv(eng.articles,folds=3)
        st.json({k:v for k,v in ev.items() if k not in ('per_class',)})
        if ev['status']=='ok':
            st.dataframe(pd.DataFrame(ev['per_class']).T,use_container_width=True)
            st.warning('If these documents are synthetic, CV metrics are a software demonstration, not real-world predictive accuracy.')
    if st.button('Train a LOCAL demonstration classifier'):
        st.json(eng.train_local_classifier())
        st.caption('Train on your approved dataset for a meaningful evaluation. This button does not create a holdout score.')

    with st.expander('Advanced topic discovery — LDA and NMF, clusters and trends'):
        method=st.selectbox('Topic algorithm',['lda','nmf'])
        result=discover_topics(eng.articles,5,method)
        if result['status']=='ok':
            st.dataframe(pd.DataFrame(result['topics']))
            st.dataframe(pd.DataFrame(result['documents'])[['article_id','topic_id','cluster_id','month']])
            if result['evolution']:
                rows=[{'month':r['month'],**{f'Topic {i}':w for i,w in enumerate(r['mean_topic_weights'])}} for r in result['evolution']]
                st.line_chart(pd.DataFrame(rows).set_index('month'))
            st.caption(result['trend_status']+' — '+result['warning'])
        else:st.json(result)
        st.download_button('Export topic analysis',export_report(result),'topics.json','application/json')
    with st.expander('Sentiment evolution and entity relationships'):
        timeline=sentiment_timeline(eng.articles)
        st.dataframe(pd.DataFrame(timeline['rows']))
        st.caption(timeline['warning'])
        edges=entity_network(eng.articles)
        st.dataframe(pd.DataFrame(edges))
        st.caption('Co-mentions are textual associations, not evidence of real relationships.')
    with st.expander('Batch article processing'):
        chosen=st.multiselect('Articles to analyze',list(eng.by_id),max_selections=20)
        if st.button('Analyze selected articles'):
            st.session_state.batch=[eng.analyze(i) for i in chosen]
        if 'batch' in st.session_state:
            st.download_button('Export batch report',export_report(st.session_state.batch),'batch.json','application/json')
