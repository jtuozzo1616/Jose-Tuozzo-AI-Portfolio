"""Bounded, local text extraction and source-linked chunking for uploaded documents."""
from __future__ import annotations
from pathlib import Path
from io import BytesIO
from html.parser import HTMLParser
from zipfile import ZipFile
import csv,json,hashlib,re
from .schemas import Article,normalize_text

FORMATS=('pdf','docx','txt','md','html','htm','csv','json','jsonl')
MAX_BYTES=8_000_000
MAX_TEXT=250_000
MAX_PAGES=100
MAX_FILES=10
MAX_RECORDS=300
CHUNK_SIZE=3200
OVERLAP=240

class VisibleHTML(HTMLParser):
    """Collect visible text only; never execute scripts or retrieve remote resources."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript','template'):self.hidden+=1
        elif not self.hidden and tag in ('p','div','br','li','h1','h2','h3','tr','section','article'):self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style','noscript','template'):self.hidden=max(0,self.hidden-1)
    def handle_data(self,data):
        if not self.hidden:self.parts.append(data+' ')

def chunks(text):
    """Split normalized text at word boundaries, preserving overlapping context."""
    text=normalize_text(text)
    if len(text)<30:return
    pos=0
    while pos<len(text):
        end=min(len(text),pos+CHUNK_SIZE)
        if end<len(text):
            split=text.rfind(' ',pos+CHUNK_SIZE//2,end)
            if split>pos:end=split
        piece=text[pos:end].strip()
        if len(piece)>=30:yield piece
        if end==len(text):break
        pos=max(pos+1,end-OVERLAP)
        boundary=text.find(' ',pos,end)
        if boundary!=-1:pos=boundary+1

def extract_document(name,raw):
    """Return source units and explicit extraction warnings; no OCR or password bypass."""
    ext=Path(name).suffix.lower().lstrip('.')
    if ext not in FORMATS:raise ValueError('Unsupported document format')
    if not raw or len(raw)>MAX_BYTES:raise ValueError('File must contain data and be at most 8 MB')
    warnings=[]
    if ext=='pdf':
        from pypdf import PdfReader
        reader=PdfReader(BytesIO(raw))
        if reader.is_encrypted:raise ValueError('Password-protected PDF is not supported')
        if len(reader.pages)>MAX_PAGES:raise ValueError('PDF exceeds 100 pages')
        units=[];total=0
        for i,p in enumerate(reader.pages,1):
            data=p.extract_text() or ''
            total+=len(data)
            if total>MAX_TEXT:raise ValueError('Extracted text exceeds 250,000 characters')
            if len(normalize_text(data))<30:warnings.append(f'{name}: page {i} has little or no extractable text; OCR is not included.')
            else:units.append((f'page {i}',data,{}))
    elif ext=='docx':
        from docx import Document
        with ZipFile(BytesIO(raw)) as z:
            if sum(x.file_size for x in z.infolist())>25_000_000:raise ValueError('Expanded Word document exceeds safe size')
        doc=Document(BytesIO(raw))
        parts=[p.text for p in doc.paragraphs]
        parts += [' | '.join(c.text for c in row.cells) for t in doc.tables for row in t.rows]
        units=[('document','\n'.join(parts),{})]
    else:
        data=raw.decode('utf-8-sig')
        if ext in ('html','htm'):
            parser=VisibleHTML();parser.feed(data);data=''.join(parser.parts)
        if ext in ('csv','json','jsonl'):
            if ext=='csv':records=list(csv.DictReader(data.splitlines(keepends=True)))
            elif ext=='jsonl':records=[json.loads(s) for s in data.splitlines() if s.strip()]
            else:
                records=json.loads(data)
                if isinstance(records,dict):records=records.get('articles',[records])
            if not isinstance(records,list) or len(records)>MAX_RECORDS:raise ValueError('Structured input requires at most 300 article objects')
            units=[]
            for i,r in enumerate(records,1):
                if not isinstance(r,dict):raise ValueError('Each record must be an object')
                body=r.get('body') or r.get('text') or r.get('content') or r.get('Text') or r.get('Article')
                if not isinstance(body,str):raise ValueError(f'Record {i} requires a body, text or content field')
                units.append((f'record {i}',body,r))
        else:units=[('document',data,{})]
    if sum(len(x[1]) for x in units)>MAX_TEXT:raise ValueError('Extracted text exceeds 250,000 characters')
    return units,warnings

def import_documents(files):
    """Import multiple (filename, bytes) pairs with stable IDs and explicit provenance."""
    files=list(files)
    if not files or len(files)>MAX_FILES:raise ValueError('Select 1–10 files')
    if sum(len(raw) for _,raw in files)>MAX_BYTES:raise ValueError('Combined upload exceeds 8 MB')
    articles=[];warnings=[];seen=set();total_text=0
    for name,raw in files:
        name=Path(name).name[:140]
        digest=hashlib.sha256(raw).hexdigest()
        identity=hashlib.sha256(name.encode()+b'\0'+raw).hexdigest()[:16]
        if identity in seen:
            warnings.append(f'{name}: duplicate file skipped');continue
        seen.add(identity)
        units,notes=extract_document(name,raw);warnings.extend(notes)
        total_text+=sum(len(x[1]) for x in units)
        if total_text>MAX_TEXT:raise ValueError('Combined extracted text exceeds 250,000 characters')
        before=len(articles)
        for i,(locator,body,meta) in enumerate(units,1):
            title=str(meta.get('title') or meta.get('Title') or Path(name).stem)
            lang=meta.get('language') or 'auto'
            if lang not in ('en','es','fr','de','auto'):lang='auto'
            for j,part in enumerate(chunks(body),1):
                articles.append(Article(article_id=f'doc-{identity}-{i}-{j}',title=f'{title[:180]} [{locator}, part {j}]',body=part,
                    source=f'{name[:90]} | {locator} | part {j} | SHA256 {digest[:12]}',
                    category=str(meta.get('category') or meta.get('Category') or ''),language=lang,
                    published_at=str(meta.get('published_at') or ''),url=str(meta.get('url') or ''),
                    synthetic=str(meta.get('synthetic',False)).lower()=='true',
                    source_region=str(meta.get('source_region') or ''),event_id=str(meta.get('event_id') or '')))
                if len(articles)>MAX_RECORDS:raise ValueError('Upload exceeds 300 searchable fragments')
        if len(articles)==before:raise ValueError(f'{name}: no usable text extracted; scanned PDFs need OCR first')
    return articles,warnings
