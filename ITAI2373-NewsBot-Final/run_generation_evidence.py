"""Execute actual neural generation; fail rather than pass on a fallback."""
from pathlib import Path
import json,os
from importlib.metadata import version
from newsbot2.io import import_articles
from newsbot2.generation import generate_brief
root=Path(__file__).resolve().parent
articles=import_articles(root/'data/demo_news.jsonl')
results=[generate_brief(a) for a in articles[:3]]
assert all(x['status']=='ok' and x['draft'] for x in results),results
out=root/'evidence';out.mkdir(exist_ok=True)
(out/'generation_results.json').write_text(json.dumps({'commit':os.getenv('GITHUB_SHA','local'),'transformers_version':version('transformers'),'results':results,'scope':'Three actual neural drafts from fictional articles; no human-rated factuality or summarization accuracy claimed.'},indent=2))
print('PRETRAINED GENERATION VERIFIED',[(r['source_id'],r['draft']) for r in results])
