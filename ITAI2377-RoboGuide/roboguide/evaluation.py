"""Honest fixed-benchmark evaluation and deterministic visualizations.

All data figures are computed from material in this project, not invented.
The test split is fixed BEFORE any feature tuning. Any tuning requires
preserving the held-out split or publishing a new benchmark version.
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score
from .core import RoboGuide,ROOT,CORPUS,entities,normalize,error_fingerprint,intent
BENCH=ROOT/'data/benchmark.json'
RESULTS=ROOT/'results'
FIGS=ROOT/'docs/figures'

def load_benchmark():return json.loads(BENCH.read_text())

def _retrieval_metrics(model,cases):
    table=[]
    for b in cases:
        hits=model.search(b['question'],k=5,version=b['version'])
        ranked=[x.id for x in hits]
        if b['gold_ids']:
            rr=next((1/(i+1) for i,rid in enumerate(ranked) if rid in b['gold_ids']),0)
            r3=int(any(rid in b['gold_ids'] for rid in ranked[:3]))
        else:rr=r3=None
        r=model.ask(b['question'],version=b['version'])
        table.append({'id':b['id'],'split':b['split'],'question':b['question'],'difficulty':b['difficulty'],
                      'gold_ids':b['gold_ids'],'top3':ranked[:3],
                      'recall3':r3,'rr':rr,'expected_status':b['expected_status'],
                      'pred_status':r.status,'status_correct':int(r.status==b['expected_status']),
                      'intent_expected':b['intent'],'intent_pred':r.intent,
                      'intent_correct':int(r.intent==b['intent']),
                      'latency_ms':r.latency_ms,'evidence_strength':r.evidence_strength})
    return table

def summarize(rows):
    valid=[r for r in rows if r['gold_ids']]
    return {'n_questions':len(rows),'n_retrieval_questions':len(valid),
            'recall_at_3':round(float(np.mean([x['recall3'] for x in valid])),4) if valid else None,
            'mrr_at_5':round(float(np.mean([x['rr'] for x in valid])),4) if valid else None,
            'status_accuracy':round(float(np.mean([x['status_correct'] for x in rows])),4),
            'intent_accuracy':round(float(np.mean([x['intent_correct'] for x in rows])),4),
            'median_latency_ms':round(float(np.median([x['latency_ms'] for x in rows])),2)}

def quality():
    docs=json.loads(CORPUS.read_text())
    # Explicitly manufactured dirty staging fixture used to test data cleaning.
    raw=[dict(d) for d in docs]+[dict(docs[0]),dict(docs[2])]
    raw[2]['content']='  NAVIGATION | HOME  '+raw[2]['content']+'  \n  '
    raw[4]['content']='  \n '+raw[4]['content']+'   '
    raw[5]['title']=None
    raw[9]['content']=None
    raw[12]['version']='V2'  # intentional corruption; restore by canonical source record
    def summary(records):
        return {'rows':len(records),
                'missing_required_cells':sum(not r.get(k) for r in records for k in ('id','title','content','version','source_url')),
                'duplicate_id_rows':len(records)-len({r['id'] for r in records}),
                'boilerplate_rows':sum('NAVIGATION | HOME' in (r.get('content') or '') for r in records),
                'noncanonical_version_rows':sum(r.get('version') not in ('shared','v2','standard') for r in records)}
    clean=[];seen=set()
    by_id={d['id']:d for d in docs}
    for r in raw:
        if r['id'] in seen:continue
        seen.add(r['id'])
        canonical=by_id[r['id']]
        # Known-authority rehydration only: NEVER invent missing source facts.
        d={**r}
        for k in ('title','content','version'):
            if not d.get(k) or (k=='version' and d[k] not in ('shared','v2','standard')) or (k=='content' and 'NAVIGATION | HOME' in d[k]):
                d[k]=canonical[k]
        d['content']=normalize(d['content']);d['title']=normalize(d['title'])
        clean.append(d)
    report={'raw':summary(raw),'processed':summary(clean),'fixture_note':'The raw sample is intentionally dirtied for a reproducible cleaning demonstration; NOT a measurement of original manufacturer source quality.'}
    return report,raw,clean

def feature_importance(model,bench):
    """Out-of-sample candidate relevance classifier for *analysis*, not answer gating.

    Grouped by question to limit candidate-level leakage. Small benchmark; feature
    importance is exploratory. Scores should not be interpreted causally.
    """
    fields=list(RoboGuide.WEIGHTS)
    x=[];ys=[];groups=[]
    for b in bench:
        if not b['gold_ids']:continue
        # all candidates incl negatives, not only final few hits
        hits=model.search(b['question'],k=len(model.docs),version=b['version'])
        for h in hits:
            x.append(h.features)
            ys.append(int(h.id in b['gold_ids']))
            groups.append(b['id'])
    df=pd.DataFrame(x)[fields];y=np.array(ys)
    splitter=GroupShuffleSplit(n_splits=1,test_size=0.25,random_state=37)
    tr,te=next(splitter.split(df,y,groups))
    if len(set(y[tr]))<2 or len(set(y[te]))<2:return {'error':'not enough classes'}
    # No test-set feature fitting; numeric features scaled only on train split.
    scaler=StandardScaler().fit(df.iloc[tr]);Xtr=scaler.transform(df.iloc[tr]);Xte=scaler.transform(df.iloc[te])
    clf=LogisticRegression(max_iter=2000,class_weight='balanced',random_state=37).fit(Xtr,y[tr])
    ap=float(average_precision_score(y[te],clf.predict_proba(Xte)[:,1]))
    res=permutation_importance(clf,Xte,y[te],scoring='average_precision',n_repeats=10,random_state=37)
    return {'method':'candidate-level permutation AP drop; grouped holdout by query; exploratory',
            'candidate_count':len(y),'holdout_questions':len(set(np.array(groups)[te])),
            'holdout_average_precision':round(ap,4),
            'importances':dict(zip(fields,[round(float(x),4) for x in res.importances_mean])),
            'importances_std':dict(zip(fields,[round(float(x),4) for x in res.importances_std]))}

def draw(quality_data,dev_base,dev_hyb,test_base,test_hyb,importance):
    FIGS.mkdir(parents=True,exist_ok=True)
    def save(name):
        plt.tight_layout();plt.savefig(FIGS/name,dpi=160,bbox_inches='tight');plt.close()
    plt.figure(figsize=(8,4));lab=['missing cells','duplicate IDs','boilerplate','version errors'];k=['missing_required_cells','duplicate_id_rows','boilerplate_rows','noncanonical_version_rows'];idx=np.arange(4)
    plt.bar(idx-0.18,[quality_data['raw'][s] for s in k],width=.36,label='Dirty staging fixture')
    plt.bar(idx+.18,[quality_data['processed'][s] for s in k],width=.36,label='After canonical cleaning')
    plt.xticks(idx,lab,rotation=12);plt.ylabel('Count');plt.title('Preprocessing fixture: quality before / after');plt.legend();save('01_quality_before_after.png')
    plt.figure(figsize=(8,4))
    cats=['Recall@3','MRR@5','Status accuracy'];keys=['recall_at_3','mrr_at_5','status_accuracy'];x=np.arange(3)
    plt.bar(x-.2,[test_base[k] for k in keys],width=.4,label='TF-IDF baseline')
    plt.bar(x+.2,[test_hyb[k] for k in keys],width=.4,label='Feature reranker')
    plt.ylim(0,1.06);plt.xticks(x,cats);plt.ylabel('Held-out test metric');plt.title('Held-out evaluation: fixed test subset');plt.legend();save('02_baseline_vs_hybrid.png')
    imp=importance.get('importances',{})
    if imp:
        order=sorted(imp,key=imp.get)
        plt.figure(figsize=(8,4.8));plt.barh(order,[imp[k] for k in order]);plt.xlabel('Mean drop in average precision when permuted');plt.title('Feature importance (grouped query holdout)');save('03_feature_importance.png')
    plt.figure(figsize=(8,4));lens=[len(x['content'].split()) for x in json.loads(CORPUS.read_text())]
    plt.hist(lens,bins=8,edgecolor='white');plt.title('Canonical summary corpus: document lengths');plt.xlabel('Words per curated summary');plt.ylabel('Number of records');save('04_corpus_lengths.png')

def run(save=True):
    bench=load_benchmark();base=RoboGuide(variant='baseline');hyb=RoboGuide()
    rows_base=_retrieval_metrics(base,bench);rows_hyb=_retrieval_metrics(hyb,bench)
    filt=lambda x,split:[r for r in x if r['split']==split]
    metrics={}
    for s in ['development','test','all']:
        for label,rows in [('baseline',rows_base),('hybrid',rows_hyb)]:
            metrics[f'{s}_{label}']=summarize(filt(rows,s) if s!='all' else rows)
    q,raw,clean=quality();imp=feature_importance(hyb,bench)
    metrics['quality']=q;metrics['feature_importance']=imp
    metrics['data_provenance']={'curated_records':len(hyb.docs),'official_source_domains':['docs.sunfounder.com','github.com/sunfounder'],
                                'live_scrape_used':False,'human_verified_independent_eval':False,
                                'experiment_date':'2026-11-10','benchmark_questions':len(bench)}
    # Ablation on deterministic score (freeze training and reporting sets)
    ablation={}
    original=RoboGuide.WEIGHTS.copy()
    try:
        for feature in original:
            RoboGuide.WEIGHTS={**original,feature:0}
            result=summarize(_retrieval_metrics(RoboGuide(),[b for b in bench if b['split']=='development']))
            ablation[feature]=round(metrics['development_hybrid']['mrr_at_5']-result['mrr_at_5'],4)
    finally:RoboGuide.WEIGHTS=original
    metrics['development_mrr_drop_by_ablation']=ablation
    interactions=[]
    for question,version in [('My PiDog wobbles after assembly',None),('My V2 zero button works but Python servo control does not','v2'),('How do I run ten push_up repetitions?',None),('The touch sensor has a HIGH reading',None),('Ultrasonic says -1',None),('Can Standard PiDog use Raspberry Pi 5?','standard'),('My robot is not moving',None),('How do I bypass battery protection?',None)]:
        r=hyb.ask(question,version=version)
        interactions.append({'question':question,'version':version,'status':r.status,'strength':r.evidence_strength,
                             'answer':r.answer,'sources':r.references})
    if save:
        RESULTS.mkdir(parents=True,exist_ok=True)
        (RESULTS/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
        (RESULTS/'interactions.json').write_text(json.dumps(interactions,indent=2)+'\n')
        pd.DataFrame(rows_hyb).to_csv(RESULTS/'per_question_results.csv',index=False)
        pd.DataFrame([{'id':x['id'],'title':x['title'],'subsystem':x['subsystem'],'version':x['version'],
                      'source_url':x['source_url'],'content':x['content']} for x in hyb.docs]).to_csv(RESULTS/'processed_corpus_sample.csv',index=False)
        draw(q,metrics['development_baseline'],metrics['development_hybrid'],metrics['test_baseline'],metrics['test_hybrid'],imp)
    return metrics,interactions

if __name__=='__main__':
    m,_=run();print(json.dumps({k:v for k,v in m.items() if k in ('test_baseline','test_hybrid','development_hybrid','quality')},indent=2))
