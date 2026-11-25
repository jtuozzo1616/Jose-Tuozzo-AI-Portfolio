"""Strict evidence run: real neural models, no fallback counted as success."""
from pathlib import Path
import json, os, time
from importlib.metadata import version
import numpy as np
from argostranslate import package
from newsbot2.io import import_articles
from newsbot2.engine import NewsBotEngine
from newsbot2.evaluation import evaluate_retrieval

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'evidence'
OUT.mkdir(exist_ok=True)
model='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
articles=import_articles(ROOT/'data/demo_news.jsonl')
start=time.perf_counter()
engine=NewsBotEngine(articles,embedding_model=model)
assert engine.retriever.method.startswith('multilingual-embeddings:'), engine.retriever.method
assert engine.retriever.vectors.shape[0]==len(articles)
from sentence_transformers import SentenceTransformer
encoder=engine.retriever.embedding_model
sentences=['The university studies artificial intelligence.','La universidad investiga inteligencia artificial.','Die Universität erforscht künstliche Intelligenz.','The football team won the championship.']
v=encoder.encode(sentences,normalize_embeddings=True)
matrix=np.asarray(v@v.T).round(5).tolist()
assert matrix[0][1]>matrix[0][3],matrix
assert matrix[0][2]>matrix[0][3],matrix
probes=[('¿Qué sensores ayudan al robot a desplazarse?','demo-tech-2'),('Welche Kameras helfen bei der Roboternavigation?','demo-tech-2'),('Quel film est présenté au festival de cinéma ?','demo-entertainment-6'),('What did the AI chip researchers measure?','demo-tech-1')]
embedding_eval=evaluate_retrieval(engine,probes,k=3)
baseline_eval=evaluate_retrieval(NewsBotEngine(articles),probes,k=3)
result={'model':model,'method':engine.retriever.method,'dimension':int(v.shape[1]),'sentences':sentences,'cosine_similarity':matrix,'embedding_retrieval':embedding_eval,'lexical_retrieval':baseline_eval,'scope':'Four deliberately constructed fictional-corpus probes; not independent validation. Similarity is not factual truth.','versions':{'sentence_transformers':version('sentence-transformers'),'argostranslate':version('argostranslate')},'commit':os.getenv('GITHUB_SHA','local')}
(OUT/'embedding_results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
print('EMBEDDINGS VERIFIED',result['dimension'],matrix)
package.update_package_index()
packs=package.get_available_packages()
p=next(p for p in packs if p.from_code=='es' and p.to_code=='en')
package.install_from_path(p.download())
samples=['La universidad investiga inteligencia artificial.','El equipo de robótica probó sensores y cámaras.','Los periodistas verificaron las fuentes antes de publicar la noticia.']
translations=[]
for text in samples:
    result=engine.translate(text,'es','en')
    assert result['status']=='ok' and result['provider']=='argos-local' and result['translated_text'].strip() and result['translated_text']!=text,result
    translations.append({'source':text,**result})
(OUT/'translation_results.json').write_text(json.dumps({'pack':str(p),'source':'es','target':'en','translations':translations,'scope':'Actual machine translations; not human-rated translation accuracy.','elapsed_seconds':round(time.perf_counter()-start,2),'commit':os.getenv('GITHUB_SHA','local')},indent=2,ensure_ascii=False))
print('ARGOS TRANSLATION VERIFIED',translations)
