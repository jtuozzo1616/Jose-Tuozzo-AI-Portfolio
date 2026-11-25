"""Rubric-aligned analytical services. Observational summaries, never causal or bias judgments."""
from collections import Counter, defaultdict
from datetime import date,timedelta
from itertools import combinations
import re
import json
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer,TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation,NMF
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from .analysis import sentiment,entities
from .language import detect_language,pivot_terms

def month(value):
    """Return ISO month or None; never invent timestamps."""
    try: return date.fromisoformat(str(value)[:10]).strftime('%Y-%m')
    except (TypeError,ValueError): return None

def discover_topics(articles,n_topics=4,method='lda'):
    """Fit LDA on counts or NMF on TF-IDF, then cluster normalized topic weights."""
    if method not in ('lda','nmf'): raise ValueError('method must be lda or nmf')
    if len(articles)<6:return {'status':'insufficient_data','minimum':6}
    vec=(CountVectorizer if method=='lda' else TfidfVectorizer)(max_features=3000,stop_words='english',max_df=.95)
    try:
        X=vec.fit_transform([pivot_terms(a.full_text) for a in articles])
        k=min(max(2,int(n_topics)),8,X.shape[0]-1,X.shape[1]-1)
        if k<2:return {'status':'insufficient_vocabulary'}
        model=LatentDirichletAllocation(n_components=k,random_state=42,max_iter=15,learning_method='batch') if method=='lda' else NMF(n_components=k,init='nndsvda',random_state=42,max_iter=400)
        raw_weights=model.fit_transform(X)
        zero_rows=raw_weights.sum(axis=1)<=1e-12
        weights=normalize(raw_weights,norm='l1')
        # NMF may produce no active component: use an explicitly flagged uniform prior.
        weights[zero_rows]=1.0/k
        clusters=KMeans(n_clusters=k,random_state=42,n_init=10).fit_predict(weights)
        labels=weights.argmax(axis=1)
        names=vec.get_feature_names_out()
        topics=[{'topic_id':i,'terms':[str(names[j]) for j in model.components_[i].argsort()[-8:][::-1]],'article_count':int((labels==i).sum())} for i in range(k)]
        docs=[{'article_id':a.article_id,'topic_id':int(labels[i]),'cluster_id':int(clusters[i]),'uninformative_topic_weights':bool(zero_rows[i]),'distribution':weights[i].round(6).tolist(),'month':month(a.published_at)} for i,a in enumerate(articles)]
        periods=defaultdict(list)
        for d,w in zip(docs,weights):
            if d['month']:periods[d['month']].append(w)
        evolution=[{'month':m,'documents':len(v),'mean_topic_weights':np.mean(v,axis=0).round(6).tolist()} for m,v in sorted(periods.items())]
        return {'status':'ok','method':method.upper(),'topics':topics,'documents':docs,'evolution':evolution,'uninformative_documents':int(zero_rows.sum()),'missing_dates':sum(d['month'] is None for d in docs),'trend_status':'descriptive' if len(evolution)>1 else 'insufficient_time_periods','warning':'Exploratory corpus-specific topics and clusters; no independent ground truth.'}
    except ValueError as e:return {'status':'unavailable','reason':str(e)}

def sentiment_timeline(articles):
    """Aggregate lexical sentiment by month and method to avoid mixing incompatible scores."""
    groups=defaultdict(list)
    missing=0
    for a in articles:
        m=month(a.published_at)
        if m is None:missing+=1;continue
        s=sentiment(a.full_text);groups[(m,s['method'])].append(s['score'])
    rows=[{'month':m,'method':method,'n':len(v),'mean_score':round(float(np.mean(v)),5)} for (m,method),v in sorted(groups.items())]
    return {'rows':rows,'missing_dates':missing,'warning':'Descriptive lexical indicators; not evidence of editorial bias or factual accuracy.'}

def entity_network(articles,limit=40):
    """Within-document entity co-mentions, with traceable source IDs, not real relationships."""
    edges=defaultdict(list)
    for a in articles[:300]:
        names=sorted({x['text'].strip() for x in entities(a.full_text)['mentions'] if x['text'].strip()})[:15]
        for x,y in combinations(names,2):edges[(x,y)].append(a.article_id)
    return [{'entity_a':x,'entity_b':y,'co_mentions':len(ids),'article_ids':ids} for (x,y),ids in sorted(edges.items(),key=lambda e:(-len(e[1]),e[0]))[:limit]]

def language_comparison(articles):
    """Compare category coverage and lexical tone; language is not a proxy for culture."""
    groups=defaultdict(list)
    for a in articles:groups[a.language if a.language!='auto' else detect_language(a.full_text)['language']].append(a)
    return [{'language':l,'n':len(v),'categories':dict(Counter(a.category or 'unlabeled' for a in v)),'sources':sorted({a.source for a in v}),'article_ids':[a.article_id for a in v]} for l,v in sorted(groups.items())]

def query_intents(query):
    """Transparent multi-intent routing and structured filters for editorial questions."""
    q=query.casefold()
    patterns={'sentiment':r'\b(positive|negative|neutral|sentiment|tone)\b','topics':r'\b(topics?|themes?|trends?)\b','compare':r'\b(compare|comparison|versus|across languages)\b','export':r'\b(export|download|report)\b','entities':r'\b(entities|relationships|co-mentions)\b'}
    intents=[k for k,p in patterns.items() if re.search(p,q)] or ['search']
    cat=next((x for x in ('tech','business','politics','sport','entertainment') if re.search(r'\b'+x+r's?\b',q)),None)
    tone=next((x for x in ('positive','negative','neutral') if re.search(r'\b'+x+r'\b',q)),None)
    return {'intents':intents,'category':cat,'tone':tone,'this_week':'this week' in q}

def structured_query(engine,query,as_of=None,preferred_categories=()):
    """Route multi-part queries, use explicit date window, return traceable result records."""
    intent=query_intents(query);selected=list(engine.articles)
    if intent['category']:selected=[a for a in selected if a.category==intent['category']]
    elif preferred_categories:selected=[a for a in selected if a.category in preferred_categories]
    if intent['this_week']:
        now=as_of or date.today();start=now-timedelta(days=now.weekday())
        def in_week(a):
            try:return start<=date.fromisoformat(a.published_at[:10])<=now
            except (ValueError,TypeError):return False
        selected=[a for a in selected if in_week(a)]
    if intent['tone']:selected=[a for a in selected if sentiment(a.full_text)['label']==intent['tone']]
    response={'intent':intent,'matched':len(selected),'articles':[{'article_id':a.article_id,'title':a.title,'source':a.source,'published_at':a.published_at,'synthetic':a.synthetic} for a in selected[:100]],'warning':'Filters apply to corpus metadata; lexical tone is not a factual judgment.'}
    if 'topics' in intent['intents']:response['topics']=discover_topics(selected)
    if 'compare' in intent['intents']:response['coverage']=language_comparison(selected)
    if 'entities' in intent['intents']:response['co_mentions']=entity_network(selected)
    if 'sentiment' in intent['intents']:response['sentiment_timeline']=sentiment_timeline(selected)
    if intent['intents']==['search'] and not intent['category'] and not preferred_categories and not intent['this_week']:response['grounded_answer']=engine.ask(query)
    return response

def expand_query(query):
    """Expose deterministic expansion, not hidden rewriting; conservative domain synonyms."""
    lex={'robot':['robotics','navigation','sensors'],'economy':['market','economic'],'election':['voting','polling'],'climate':['energy','environment']}
    p=pivot_terms(query);terms=p.split();added=sorted({w for t in terms for w in lex.get(t,[]) if w not in terms})
    return {'original':query,'pivot':p,'added_terms':added,'expanded':' '.join([p,*added])}

def hierarchy(prediction):
    """Map first-level classifier label into explicit editorial hierarchy, not a second trained model."""
    parent={'tech':'science and technology','business':'economy','politics':'public affairs','sport':'culture and recreation','entertainment':'culture and recreation'}
    return {'parent_category':parent.get(prediction.get('label'),'unclassified'),'child_category':prediction.get('label'),'score_type':prediction.get('score_type'),'confidence_gap':prediction.get('top_margin_gap'),'method':'fixed taxonomy, classifier scores uncalibrated'}

def export_report(payload):
    """JSON report retains sources, filter settings and warnings."""
    return json.dumps(payload,indent=2,ensure_ascii=False)
