from io import BytesIO
import json,pytest
from docx import Document
from reportlab.pdfgen.canvas import Canvas
from newsbot2.documents import import_documents, chunks
from newsbot2.engine import NewsBotEngine
TEXT='The laboratory measured processing time and energy consumption using robotics sensors. Researchers recorded all measurements.'
def test_text_markdown_and_chat():
    docs,notes=import_documents([('report.txt',TEXT.encode()),('notes.md',('# Results\n'+TEXT).encode())])
    assert len(docs)==2 and not notes and not any(a.synthetic for a in docs)
    assert 'report.txt' in docs[0].source
    engine=NewsBotEngine(docs)
    assert engine.ask('What did the laboratory measure?')['citations']
def test_pdf_pages():
    buf=BytesIO();c=Canvas(buf);c.drawString(40,700,TEXT);c.showPage();c.drawString(40,700,'Second page: the experiment used cameras and distance sensors in an indoor robotics laboratory.');c.save()
    docs,notes=import_documents([('study.pdf',buf.getvalue())])
    assert len(docs)==2 and 'page 1' in docs[0].source and 'page 2' in docs[1].source
def test_docx_and_html():
    buf=BytesIO();d=Document();d.add_paragraph(TEXT);d.save(buf)
    docs,_=import_documents([('report.docx',buf.getvalue()),('article.html',('<script>HIDDEN_SECRET</script><p>'+TEXT+'</p>').encode())])
    assert len(docs)==2 and all('HIDDEN_SECRET' not in x.body for x in docs)
def test_structured_formats():
    docs,_=import_documents([('sample.json',json.dumps([{'title':'Research','text':TEXT,'category':'tech'}]).encode()),('sample.jsonl',json.dumps({'body':TEXT,'synthetic':True}).encode()),('sample.csv',('title,body\nResearch,"'+TEXT+'"\n').encode())])
    assert len(docs)==3 and docs[0].category=='tech' and docs[1].synthetic
def test_chunking_and_limits():
    content=(TEXT+' ')*100
    docs,_=import_documents([('long.txt',content.encode())])
    assert len(docs)>1 and all(len(x.body)<=3200 for x in docs)
    assert len({x.article_id for x in docs})==len(docs)
    with pytest.raises(ValueError):import_documents([('blank.txt',b'')])
    with pytest.raises(ValueError):import_documents([('unsafe.exe',TEXT.encode())])
    with pytest.raises(ValueError):import_documents([('big.txt',b'x'*8_000_001)])
