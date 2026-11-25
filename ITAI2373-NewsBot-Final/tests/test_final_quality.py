from newsbot2.schemas import Article
from newsbot2.engine import NewsBotEngine

def test_language_filter_applied_before_top_k():
    articles=[Article('en1','Robot sensors','Robot sensors monitor navigation and measure motion in a laboratory.',language='en'),
              Article('es1','Robot sensores','El robot usa sensores en la universidad para investigar.',language='es')]
    e=NewsBotEngine(articles)
    assert [h['article_id'] for h in e.search('robot',1,language='es')]==['es1']
    assert e.search('robot',1,language='fr')==[]
    assert e.search('robot',0)==[]

def test_relevant_late_evidence_is_retrieved():
    a=Article('a','Research report','The university opened a general public meeting. The staff welcomed attendees to the main hall. The researchers measured battery voltage and current. Their results are available for further review.',language='en')
    e=NewsBotEngine([a])
    hit=e.search('battery voltage current',1)[0]
    assert 'battery voltage and current' in hit['excerpt']
    assert hit['excerpt'] in a.body
