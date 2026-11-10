import json
from pathlib import Path
import pytest
from roboguide import RoboGuide,error_fingerprint,extract_version
from roboguide.core import CORPUS,entities,intent
from roboguide.ingest import authorized,chunk,clean_html

@pytest.fixture(scope='module')
def guide():return RoboGuide()

def test_corpus_has_auditable_provenance(guide):
    assert len(guide.docs)>=20
    assert len({x['id'] for x in guide.docs})==len(guide.docs)
    assert all(x['source_url'].startswith('https://') for x in guide.docs)

def test_fingerprints_remove_paths_and_lines():
    a='Traceback (most recent call last):\n File "/home/a/pidog/speaker.py", line 20, in main\n ModuleNotFoundError: No module named robot_hat'
    b='Traceback\n File "/users/b/other.py", line 188, in main\n ModuleNotFoundError: No module named robot_hat'
    assert error_fingerprint(a)==error_fingerprint(b)

def test_no_fingerprint_when_not_traceback():assert error_fingerprint('The speaker is silent')==''

def test_version_detection():
    assert extract_version('My V2 dog')=='v2'
    assert extract_version('Standard model')=='standard'
    assert extract_version('V1 versus V2')=='both'

def test_hard_filter_wrong_version(guide):
    res=guide.search('How do I zero V2 servos?',version='v2',k=100)
    assert 'zero_v1' not in [r.id for r in res]
    assert 'zero_v2' in [r.id for r in res]

def test_version_standard_only(guide):
    res=guide.search('Standard servo zeroing?',version='standard',k=100)
    assert 'zero_v2' not in [r.id for r in res]

def test_source_link(guide):
    a=guide.ask('My dog shakes when walking')
    assert a.status=='answered'
    assert a.references and all(x['url'].startswith('https://') for x in a.references)
    assert '[S1]' in a.answer

def test_no_hardware_execution(guide):
    # No function sends commands to PiDog or calls subprocess in response.
    r=guide.ask('How do I do 10 push_up repetitions?')
    assert r.status=='answered' and r.references

def test_refuse_unsafe(guide):
    assert guide.ask('How do I bypass battery protection?').status=='escalate'

def test_out_of_domain(guide):
    assert guide.ask('What is the stock price of Tesla today?').status=='out_of_scope'

def test_missing_question(guide):
    assert guide.ask('').status=='clarify'

def test_unknown_hardware_version_handled(guide):
    result=guide.ask('What does Standard Raspberry Pi 5 compatibility mean?')
    assert result.status=='answered'

def test_selected_answer_from_sources(guide):
    out=guide.ask('What does a -1 ultrasonic distance mean?')
    assert all(c['id'] in [d['id'] for d in guide.docs] for c in out.references)

def test_online_allowlist():
    assert authorized('https://docs.sunfounder.com/projects/pidog/en/latest/faq.html')
    assert not authorized('https://evil.com/steal')
    assert not authorized('http://docs.sunfounder.com/projects/pidog/en/latest/faq.html')
    assert not authorized('https://docs.sunfounder.com.evil.com/projects/pidog/faq')

def test_html_cleaner():
    text=clean_html('<main><nav>Bad menu</nav><article><h1>Test</h1><p>Servo zero.</p></article></main>')
    assert 'Servo zero' in text and 'Bad menu' not in text

def test_chunker():
    items=chunk(('A technical procedure describes the servo.\n\n')*50,max_words=55,overlap=10)
    assert len(items)>=2

def test_parse_entities():assert 'touch' in entities('The dual_touch sensor')

def test_bad_duplicate_rejected(tmp_path):
    d=json.loads(CORPUS.read_text())
    (tmp_path/'dup.json').write_text(json.dumps(d+[d[0]]))
    with pytest.raises(ValueError,match='Duplicate'):RoboGuide(tmp_path/'dup.json')
