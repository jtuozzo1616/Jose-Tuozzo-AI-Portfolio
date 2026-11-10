"""Optional online ingestion from allowlisted official URLs.

Not run in the packaged pilot because this execution environment cannot reach
the internet. Run from Google Colab and audit the resulting snapshot before
replacing curated data or claiming source coverage. No recursive web crawling.
"""
from __future__ import annotations
import argparse,hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
from .core import ROOT, normalize
URLS=[
 'https://docs.sunfounder.com/projects/pidog/en/latest/index.html',
 'https://docs.sunfounder.com/projects/pidog/en/latest/faq.html',
 'https://docs.sunfounder.com/projects/pidog/en/latest/python/play_with_python.html',
 'https://docs.sunfounder.com/projects/pidog/en/latest/python/py_0_calibrate.html',
 'https://docs.sunfounder.com/projects/pidog/en/latest/python/py_b6_preset_action.html',
 'https://docs.sunfounder.com/projects/robot-hat/en/latest/index.html',
 'https://docs.sunfounder.com/projects/robot-hat/en/latest/hardware_introduction.html',
 'https://raw.githubusercontent.com/sunfounder/pidog/main/README.md',
]
ALLOW={('docs.sunfounder.com','/projects/pidog/'),('docs.sunfounder.com','/projects/robot-hat/'),('raw.githubusercontent.com','/sunfounder/pidog/')}

def authorized(url):
    u=urlparse(url)
    return u.scheme=='https' and not u.username and any(u.hostname==host and u.path.startswith(prefix) for host,prefix in ALLOW)

def clean_html(content:str)->str:
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(content,'html.parser')
    body=soup.select_one('main article') or soup.select_one('article') or soup.select_one('main') or soup.body
    if body is None:return ''
    for node in body.select('nav,footer,aside,script,style,.headerlink,.related,.toc-tree'):
        node.decompose()
    for pre in body.find_all('pre'):
        pre.replace_with('\n```\n'+pre.get_text('\n',strip=False)+'\n```\n')
    return normalize(body.get_text('\n',strip=True))

def chunk(text,max_words=320,overlap=45):
    """Word chunks preserve code-fence blocks in the original text as best effort.

    The online snapshot is exploratory and requires manual code-integrity review.
    """
    blocks=[b.strip() for b in re.split(r'\n(?=#{1,5}\s)|\n\n+',text) if b.strip()]
    result=[];buf=[];n=0
    for block in blocks:
        length=len(block.split())
        if n+length>max_words and buf:
            result.append('\n\n'.join(buf))
            # modest carry-over; never split a fenced code block mid-block
            buf=[buf[-1]] if buf and len(buf[-1].split())<=overlap else []
            n=sum(len(x.split()) for x in buf)
        if length>max_words:
            lines=block.splitlines()
            if block.startswith('```') and block.endswith('```'):
                result.append(block);continue
            # Prose-only split; source still preserved in content hash.
            for offset in range(0,len(block.split()),max_words-overlap):
                result.append(' '.join(block.split()[offset:offset+max_words]))
            continue
        buf.append(block);n+=length
    if buf:result.append('\n\n'.join(buf))
    return [x for x in result if len(x.split())>=12]

def run(out:Path,urls=None,delay=0.7):
    import requests
    urls=urls or URLS
    out.mkdir(parents=True,exist_ok=True)
    session=requests.Session();session.headers.update({'User-Agent':'RoboGuide-Research/0.1 (educational; provenance-based)'})
    records=[];manifest=[];seen=set()
    for url in urls:
        if not authorized(url):raise ValueError(f'URL not allowlisted: {url}')
        r=session.get(url,timeout=20);r.raise_for_status()
        raw=r.text
        body=raw if url.endswith('.md') else clean_html(raw)
        sha=hashlib.sha256(raw.encode()).hexdigest()
        manifest.append({'url':url,'sha256':sha,'status':r.status_code,'bytes':len(r.content),
                         'fetched_at':datetime.now(timezone.utc).isoformat()})
        for i,part in enumerate(chunk(body)):
            key=hashlib.sha256(part.encode()).hexdigest()
            if key in seen:continue
            seen.add(key)
            records.append({'id':sha[:10]+f'-{i:03d}','title':url.rsplit('/',1)[-1] or 'index',
                'content':part,'subsystem':'unreviewed','version':'shared',
                'source_url':url,'source_type':'official_live_snapshot',
                'authority':1,'retrieved_on':datetime.now(timezone.utc).date().isoformat(),
                'review_status':'unreviewed','sha256':key})
        time.sleep(delay)
    (out/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'online_unreviewed_chunks.json').write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n')
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true',required=True)
    p.add_argument('--out',default='data/snapshots');a=p.parse_args()
    records=run(ROOT/a.out)
    print(f'Fetched {len(records)} UNREVIEWED source chunks; inspect before incorporating into benchmark or assistant.')
