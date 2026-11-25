"""Use real historical BBC records privately; publish only aggregate metrics, not article text."""
from pathlib import Path
import urllib.request,hashlib,json,csv,io,os
from newsbot2.schemas import Article
from newsbot2.engine import NewsBotEngine
from newsbot2.advanced import discover_topics,language_comparison
from newsbot2.evaluation import evaluate_classification_cv
URL='https://raw.githubusercontent.com/alvinrach/learn-ai-bbc/main/BBC%20News%20Train.csv'
ROOT=Path(__file__).resolve().parent
with urllib.request.urlopen(URL,timeout=60) as response:
    raw=response.read(8_000_001)
assert len(raw)<8_000_000
digest=hashlib.sha256(raw).hexdigest()
rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
assert len(rows)>1000 and {'ArticleId','Category'}<=set(rows[0])
# Deterministic balanced sample; remove exact duplicates before evaluation.
seen=set(); counts={};articles=[]
for row in sorted(rows,key=lambda r:int(r['ArticleId'])):
    label=row['Category'];body=row.get('Text') or row.get('Article') or ''
    key=hashlib.sha256(body.encode()).hexdigest()
    if key in seen or counts.get(label,0)>=50 or len(body)<30:continue
    seen.add(key);counts[label]=counts.get(label,0)+1
    articles.append(Article('bbc-'+row['ArticleId'],'BBC historical article '+row['ArticleId'],body,source='BBC historical research corpus',category=label,language='en',synthetic=False))
assert len(articles)==250,counts
# Optional private local demo file; never added to Git or published.
import sys
if '--export-local' in sys.argv:
    from newsbot2.io import export_jsonl
    private=ROOT/'data'/'raw'/'bbc_demo_private.jsonl'
    private.parent.mkdir(exist_ok=True)
    export_jsonl(articles,private)
    print('Local real-data demo:',private)
cv=evaluate_classification_cv(articles,folds=3)
topics={m:discover_topics(articles,5,m) for m in ('lda','nmf')}
# Save no article text or excerpts. The topic terms are aggregate statistics.
out={'source':URL,'source_sha256':digest,'n':len(articles),'class_counts':counts,'cv':cv,'topic_models':{m:{k:v for k,v in t.items() if k not in ('documents',)} for m,t in topics.items()},'scope':'Balanced historical sample, not contemporary or multilingual validation. No copyrighted article bodies republished. Dates unknown; no fabricated trend data.','commit':os.getenv('GITHUB_SHA','local')}
dest=ROOT/'evidence';dest.mkdir(exist_ok=True)
(dest/'real_bbc_final_evaluation.json').write_text(json.dumps(out,indent=2))
print('REAL BBC FINAL PIPELINE VERIFIED',len(articles),cv['accuracy'],cv['macro_f1'])
