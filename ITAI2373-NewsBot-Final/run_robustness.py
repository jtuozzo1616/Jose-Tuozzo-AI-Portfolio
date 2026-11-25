"""Paired multilingual feature ablation; controlled synthetic evaluation, not a production benchmark."""
from pathlib import Path
import json, time
from collections import Counter
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from newsbot2.io import import_articles
from newsbot2.language import pivot_terms

ROOT = Path(__file__).resolve().parent
def model(mode):
    word = TfidfVectorizer(ngram_range=(1,2), strip_accents='unicode',
                          preprocessor=pivot_terms if mode != 'baseline' else None)
    features = FeatureUnion([('word',word),('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=1))]) if mode=='pivot_char' else word
    return Pipeline([('features',features),('model',LogisticRegression(max_iter=1000,random_state=42))])
def metrics(y,p,labels):
    return {'accuracy':float(accuracy_score(y,p)), 'macro_f1':float(f1_score(y,p,labels=labels,average='macro',zero_division=0)),
            'confusion_matrix':confusion_matrix(y,p,labels=labels).tolist()}
def main():
    corpus=import_articles(ROOT/'data/demo_news.jsonl')
    texts=[a.full_text for a in corpus]; y=[a.category for a in corpus]
    langs=[a.language for a in corpus]; labels=sorted(set(y))
    folds=list(StratifiedKFold(n_splits=3,shuffle=True,random_state=42).split(texts,y))
    result={'synthetic_only':all(a.synthetic for a in corpus),'n':len(y),'labels':labels,
            'language_counts':dict(Counter(langs)), 'seed':42,
            'protocol':'Same stratified folds for all models; fit feature extraction inside each fold; language holdout is distribution-shift diagnostic.',
            'paired_oof':{},'language_holdout':{},'limits':['Tiny fictional corpus; no external validity','No tuning or selection on these reported folds','Some held-out languages may omit classes; macro F1 uses observed gold labels.']}
    for mode in ('baseline','pivot','pivot_char'):
        start=time.perf_counter()
        pred=cross_val_predict(model(mode),texts,y,cv=folds)
        result['paired_oof'][mode]={**metrics(y,pred,labels),'elapsed_seconds':round(time.perf_counter()-start,4),
             'predictions':[{'id':a.article_id,'gold':gold,'predicted':str(p)} for a,gold,p in zip(corpus,y,pred)]}
        result['language_holdout'][mode]={}
        for lang in sorted(set(langs)):
            train=[i for i,l in enumerate(langs) if l!=lang]; test=[i for i,l in enumerate(langs) if l==lang]
            if len(set(y[i] for i in train))<2: continue
            m=model(mode); m.fit([texts[i] for i in train],[y[i] for i in train])
            p=m.predict([texts[i] for i in test]); gold=[y[i] for i in test]
            result['language_holdout'][mode][lang]={'n':len(test),'labels':sorted(set(gold)),**metrics(gold,p,sorted(set(gold)))}
    target=ROOT/'artifacts/robustness_results.json'; target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:{m:v[m] for m in ('accuracy','macro_f1')} for k,v in result['paired_oof'].items()},indent=2))
if __name__=='__main__': main()
