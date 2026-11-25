from pathlib import Path
from datetime import date
import json
from newsbot2.io import import_articles
from newsbot2.engine import NewsBotEngine
from newsbot2.advanced import discover_topics,sentiment_timeline,entity_network,language_comparison,structured_query,expand_query,hierarchy,export_report
ROOT=Path(__file__).resolve().parents[1]
def corpus():return import_articles(ROOT/'data/demo_news.jsonl')
def test_both_topic_algorithms_and_cluster():
    for method in ('lda','nmf'):
        out=discover_topics(corpus(),4,method)
        assert out['status']=='ok' and len(out['documents'])==30
        assert sum(t['article_count'] for t in out['topics'])==30
        assert all(abs(sum(d['distribution'])-1)<.001 for d in out['documents'])
        assert all(0<=d['cluster_id']<4 for d in out['documents'])
def test_timeline_provenance():
    docs=corpus();t=sentiment_timeline(docs)
    assert sum(r['n'] for r in t['rows'])+t['missing_dates']==30
    ids={a.article_id for a in docs}
    assert all(set(r['article_ids'])<=ids for r in entity_network(docs))
def test_language_coverage():
    assert sum(r['n'] for r in language_comparison(corpus()))==30
def test_multipart_and_filters():
    eng=NewsBotEngine(corpus())
    r=structured_query(eng,'Show positive tech news and compare across languages',as_of=date(2026,11,25))
    assert set(r['intent']['intents'])=={'sentiment','compare'}
    assert r['intent']['category']=='tech' and 'coverage' in r and 'sentiment_timeline' in r
    assert structured_query(eng,'Show tech news this week',as_of=date(2027,1,1))['matched']==0
    assert json.loads(export_report(r))['matched']==r['matched']
def test_expansion_and_hierarchy():
    assert 'sensors' in expand_query('robot')['added_terms']
    assert hierarchy({'label':'tech'})['parent_category']=='science and technology'
