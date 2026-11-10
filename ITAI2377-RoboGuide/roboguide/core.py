"""RoboGuide: deterministic, CPU-first, traceable PiDog documentation assistant.

No hardware commands are executed. No API key required. Retrieval confidence is a
heuristic evidence-strength signal, NOT a calibrated probability of correctness.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import time
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'data/curated_official_summaries.json'
ALIASES={
 'servo':['servo','servos','legs','leg','wobble','shakes','gait','calibration','zero','alignment','joint','leggy'],
 'ultrasonic':['ultrasonic','distance','obstacle','sonar','echo','-1'],
 'touch':['touch','pet','pat','touched','dual_touch','capacitive'],
 'sound':['direction','microphone','mic','listening','audio','speech','hear','voice'],
 'rgb':['rgb','led','light','strip','lamp'],
 'imu':['imu','gyroscope','accelerometer','balance','i2c'],
 'camera':['camera','lens','face','csi','ribbon'],
 'actions':['do_action','push_up','wait_all_done','movement','sequence','walk','turn','stop','sit'],
 'install':['pip','module','install','import','requirements','piper-tts','setup'],
 'power':['battery','charge','power','voltage','usb'],
}
INTENT={
 'calibration':['calibrat','zero','servo','alignment','ruler'],
 'motion':['walk','push_up','turn','action','stop','gait','wobble','stand','queue','sit'],
 'ultrasonic':['ultrasonic','distance','sonar','obstacle'],
 'touch':['touch','pet','pat','capacitive'],
 'imu':['imu','accelerometer','gyro','i2c','balance'],
 'rgb':['rgb','led','light'],
 'camera':['camera','ribbon','csi','face'],
 'audio':['speaker','audio','microphone','mic','speech','sound','voice','i2s'],
 'installation':['install','pip','package','module','piper-tts','setup'],
 'power':['battery','charging','power'],
 'hardware':['robot hat','gpio','compatib','raspberry pi 5','v2','standard'],
}
STOPWORDS=set('why what how my the is does do to not a it of for and after with can on in from your i its when no me de el la los que por mi perro como esta'.split())
RISK_WORDS=('short circuit','bypass battery','overvoltage','solder live','disable safety','force servo','remove battery protection','rewire while powered','flash firmware','burn')
OUT_OF_SCOPE=('stock price','bitcoin','weather today','sports scores','cooking pasta','make a bomb','bank account','medical diagnosis')
FINGERPRINT_TYPE=re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Warning))\s*:\s*(.*)',re.I)
PATH_RE=re.compile(r'(?:(?:[A-Za-z]:\\|/)[\w. /\\-]+?\.py|[\w.-]+\.py)(?=[:,\s]|$)',re.I)
LINE_RE=re.compile(r'\bline\s+\d+\b|\bline\s*:\s*\d+\b',re.I)
ADDR_RE=re.compile(r'0x[0-9a-f]{6,}|\b\d{4,}\b',re.I)


def normalize(text:str)->str:
    return unicodedata.normalize('NFKC',str(text or '')).replace('\u00a0',' ').strip()

def error_fingerprint(traceback:str)->str:
    """Keep exception class and stable message; discard unstable paths/line numbers.

    Do not strip short numeric literals indiscriminately (e.g. I2C 0x36 matters).
    """
    text=normalize(traceback)
    matches=FINGERPRINT_TYPE.findall(text)
    if not matches:return ''
    typ,msg=matches[-1]
    msg=PATH_RE.sub('<path>',msg)
    msg=LINE_RE.sub('<line>',msg)
    msg=ADDR_RE.sub('<id>',msg)
    msg=re.sub(r'\s+',' ',msg).casefold().strip()
    return typ.casefold()+':'+msg[:220]

def extract_version(query:str)->str|None:
    q=query.lower()
    v1=bool(re.search(r'\b(v1|standard|version 1)\b',q))
    v2=bool(re.search(r'\b(v2|version 2)\b',q))
    return 'both' if v1 and v2 else 'standard' if v1 else 'v2' if v2 else None

def entities(text:str)->set[str]:
    q=normalize(text).lower()
    results=set()
    for tag,words in ALIASES.items():
        if any(re.search(r'(?<!\w)'+re.escape(w)+r'(?!\w)',q) for w in words):results.add(tag)
    return results

def intent(text:str)->str:
    q=normalize(text).lower(); scored=[]
    for sub,words in INTENT.items():
        scored.append((sum(w in q for w in words),sub))
    return max(scored)[1] if max(x[0] for x in scored)>0 else 'other'

def tokenize(s):
    return {w for w in re.findall(r'[a-z][a-z0-9_]*',s.lower()) if len(w)>2 and w not in STOPWORDS}

@dataclass(frozen=True)
class Hit:
    id:str
    title:str
    url:str
    version:str
    subsystem:str
    content:str
    score:float
    features:dict[str,float]

@dataclass(frozen=True)
class Response:
    question:str
    answer:str
    status:str
    evidence_strength:float
    intent:str
    version:str|None
    references:list[dict[str,str]]
    hits:list[Hit]
    latency_ms:float

class RoboGuide:
    """Grounded extractive assistant with configurable linear reranker."""
    WEIGHTS={'word_similarity':0.38,'char_similarity':0.18,'entity_overlap':0.15,
             'title_overlap':0.11,'api_match':0.05,'fingerprint_match':0.04,
             'version_compatibility':0.04,'source_authority':0.05}
    def __init__(self, corpus:Path|str=CORPUS, *, variant:str='hybrid'):
        self.corpus_path=Path(corpus)
        self.docs=json.loads(self.corpus_path.read_text(encoding='utf-8'))
        self._validate()
        self.variant=variant
        self._texts=[d['title']+' '+d['content'] for d in self.docs]
        self.word=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,strip_accents='unicode',min_df=1)
        self.char=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True,min_df=1)
        self.W=self.word.fit_transform(self._texts)
        self.C=self.char.fit_transform(self._texts)
        self.title_tokens=[tokenize(d['title']) for d in self.docs]
        self.document_entities=[entities(s) for s in self._texts]
    def _validate(self):
        ids=set()
        for d in self.docs:
            for k in ('id','title','content','source_url','subsystem','version','source_type'):
                if not d.get(k):raise ValueError(f'Missing {k} in {d}')
            if d['id'] in ids:raise ValueError('Duplicate document ID: '+d['id'])
            if not d['source_url'].startswith('https://'):raise ValueError('Untrusted source URL')
            if d['version'] not in ('standard','v2','shared'):raise ValueError('Invalid version')
            ids.add(d['id'])
    def _compat(self,v:str|None,doc:str)->float:
        if v in (None,'both'):return 1.0 if doc=='shared' else 0.8
        return 1.0 if doc in ('shared',v) else 0.0
    def search(self,question:str,k:int=5,version:str|None=None)->list[Hit]:
        q=normalize(question)
        if not q:return []
        v=version or extract_version(q)
        w=np.asarray(cosine_similarity(self.word.transform([q]),self.W)).ravel()
        c=np.asarray(cosine_similarity(self.char.transform([q]),self.C)).ravel()
        qe=entities(q);qt=tokenize(q); fp=error_fingerprint(q)
        found=[]
        for i,d in enumerate(self.docs):
            compat=self._compat(v,d['version'])
            if compat==0:continue  # hard exclusion prevents wrong-version instructions
            ent=len(qe & self.document_entities[i])/max(len(qe),1)
            title=len(qt & self.title_tokens[i])/max(len(qt),1)
            api=1.0 if any(t in (d['title']+' '+d['content']).lower() for t in re.findall(r'[A-Za-z]+\.[A-Za-z_]+|[a-z]+_[a-z_]+',q)) else 0.0
            fingerprint=1.0 if fp and fp.split(':',1)[0] in d['content'].lower() else 0.0
            f={'word_similarity':float(w[i]),'char_similarity':float(c[i]),'entity_overlap':ent,
               'title_overlap':title,'api_match':api,'fingerprint_match':fingerprint,
               'version_compatibility':compat,'source_authority':float(d['authority'])}
            if self.variant=='baseline':s=float(w[i])
            else:s=sum(self.WEIGHTS[key]*val for key,val in f.items())
            found.append(Hit(id=d['id'],title=d['title'],url=d['source_url'],version=d['version'],
                             subsystem=d['subsystem'],content=d['content'],score=round(s,5),features=f))
        return sorted(found,key=lambda h:(-h.score,h.id))[:max(1,k)]
    @staticmethod
    def _ambiguous(q:str)->bool:
        short=len(tokenize(q))<5
        return short and bool(re.search(r'\b(not working|doesn.t work|broken|doesn.t move|won.t move|fails|help)\b',q.lower())) and len(entities(q))==0
    def ask(self,question:str,*,version:str|None=None,k:int=4)->Response:
        start=time.perf_counter();q=normalize(question)
        v=version or extract_version(q);it=intent(q)
        def finish(answer,status,strength,hits):
            return Response(q,answer,status,round(float(strength),3),it,v,
                [{'id':h.id,'title':h.title,'url':h.url} for h in hits],hits,
                round((time.perf_counter()-start)*1000,2))
        if not q:return finish('Please enter a PiDog question.','clarify',0,[])
        if any(phrase in q.lower() for phrase in RISK_WORDS):
            return finish('I cannot guide hazardous modifications or bypass safety protections. Power down the device and consult the current SunFounder manual or qualified support.','escalate',0,[])
        if any(phrase in q.lower() for phrase in OUT_OF_SCOPE):
            return finish('That question is outside the PiDog technical-support domain. I can help with documented PiDog setup, sensors, movement and code.','out_of_scope',0,[])
        if self._ambiguous(q):
            return finish('Which PiDog version (Standard/V1 or V2) do you have? What component fails, and what exact symptom or error appears?','clarify',0,[])
        hits=self.search(q,k=k,version=v)
        if not hits:return finish('No applicable documentation was found for that hardware version. Please verify the model and consult the manufacturer.','escalate',0,[])
        # Evidence strength: deterministic heuristic, not probability or calibration.
        top=hits[0]; margin=max(0,top.score-(hits[1].score if len(hits)>1 else 0))
        strength=min(1.0,max(0,(top.features['word_similarity']*.48+top.features['char_similarity']*.26+
                             top.features['entity_overlap']*.18+margin*.08)*1.45))
        relevant=[h for h in hits if h.score>=max(0.11,top.score*0.60) and h.features['word_similarity']>0.035]
        if not relevant or (top.features['word_similarity']<0.055 and top.features['char_similarity']<0.11):
            return finish('I cannot support a reliable answer from the available official-source summaries. Please provide a precise error, subsystem and hardware version, or consult the official PiDog documentation.','escalate',strength,hits[:2])
        relevant=relevant[:min(k,3)]
        # Extractive, not generative: never add undocumented commands or diagnoses.
        lines=[f'Based on the manufacturer documentation (hardware: {v or "not specified"}):']
        for i,h in enumerate(relevant,1):
            lines.append(f'{i}. {h.content} [S{i}]')
        if not v and any(h.version!='shared' for h in relevant):
            lines.append('Confirm whether the robot is Standard/V1 or V2 before taking version-dependent steps.')
        lines.append('Evidence strength is a retrieval heuristic, not a probability of safety or correctness. No commands are executed by RoboGuide.')
        return finish('\n\n'.join(lines),'answered',strength,relevant)

def to_dict(r:Response)->dict[str,Any]:
    v=asdict(r);return v
