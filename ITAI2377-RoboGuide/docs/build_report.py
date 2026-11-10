"""Generate a verified-metrics-first ITAI 2377 final PDF via ReportLab."""
import json,os,sys,re
from pathlib import Path
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph,Table,TableStyle,Image,Spacer,PageBreak,KeepTogether,HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.units import inch
root=Path(__file__).resolve().parents[1]
metrics=json.loads((root/'results/metrics.json').read_text())
interactions=json.loads((root/'results/interactions.json').read_text())
M=metrics
FIG=root/'docs/figures';FIG.mkdir(exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DejaVu',FONT))
pdfmetrics.registerFont(TTFont('DejaVu-Bold',FONTB))
NAVY=colors.HexColor('#10263C');TEAL=colors.HexColor('#136F7B');DARK=colors.HexColor('#132338');MID=colors.HexColor('#5A6B7A');ICE=colors.HexColor('#EAF4F6');PAPER=colors.HexColor('#F4F7FA');BORDER=colors.HexColor('#CAD7E1')
page_w,page_h=595.28,841.89
S={
 'body':ParagraphStyle('body',fontName='DejaVu',fontSize=9.0,leading=14.4,textColor=DARK,spaceAfter=9),
 'small':ParagraphStyle('small',fontName='DejaVu',fontSize=8,leading=12.1,textColor=DARK,spaceAfter=6),
 'muted':ParagraphStyle('muted',fontName='DejaVu',fontSize=8,leading=12.1,textColor=MID,spaceAfter=6),
 'h1':ParagraphStyle('h1',fontName='DejaVu-Bold',fontSize=20,leading=26,textColor=NAVY,spaceBefore=6,spaceAfter=11),
 'h2':ParagraphStyle('h2',fontName='DejaVu-Bold',fontSize=12.2,leading=16.2,textColor=TEAL,spaceBefore=11,spaceAfter=6),
 'h3':ParagraphStyle('h3',fontName='DejaVu-Bold',fontSize=10.5,leading=14,textColor=NAVY,spaceBefore=9,spaceAfter=5),
 'cap':ParagraphStyle('cap',fontName='DejaVu',fontSize=7.4,leading=10.5,textColor=MID,spaceAfter=9),
 'table':ParagraphStyle('table',fontName='DejaVu',fontSize=7.8,leading=11.7,textColor=DARK),
 'tableh':ParagraphStyle('tableh',fontName='DejaVu-Bold',fontSize=7.7,leading=11.2,textColor=colors.white),
 'code':ParagraphStyle('code',fontName='DejaVu',fontSize=8,leading=12.3,textColor=NAVY,leftIndent=10),
}

def P(s,style='body'):
 return Paragraph(s,S[style])
def ptxt(s):return escape(str(s)).replace('\n','<br/>')
def bullets(items):
 return [P('<font color="#136F7B">●</font> '+escape(str(t)),'small') for t in items]
def tab(rows,widths,header=True):
 data=[]
 for j,row in enumerate(rows):data.append([P(str(v),'tableh' if header and j==0 else 'table') for v in row])
 t=Table(data,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
 rules=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,-1),(-1,-1),.6,BORDER)]
 if header:rules.extend([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PAPER])])
 else:rules.append(('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white,PAPER]))
 t.setStyle(TableStyle(rules));return t

def figure(path,width=500,caption=''):
 from PIL import Image as PI
 im=PI.open(path);w,h=im.size; img=Image(str(path),width=width,height=width*h/w)
 return [img,P(caption,'cap')]

def page_header(canvas,doc):
 canvas.saveState();w,h=doc.pagesize
 canvas.setFillColor(NAVY);canvas.rect(0,h-43,w,43,fill=1,stroke=0)
 canvas.setFont('DejaVu-Bold',8.7);canvas.setFillColor(colors.white);canvas.drawString(44,h-26,'ROBOGUIDE  /  EVIDENCE-FIRST TECHNICAL SUPPORT')
 canvas.setFont('DejaVu',7.3);canvas.drawRightString(w-44,h-26,'ITAI 2377   ·   NOV 2026')
 canvas.setStrokeColor(BORDER);canvas.line(44,48,w-44,48)
 canvas.setFillColor(MID);canvas.setFont('DejaVu',7.8);canvas.drawString(44,31,'Tung Tung Tung Sahar  |  Houston City College')
 canvas.drawRightString(w-44,31,f'Page {doc.page}')
 canvas.restoreState()

def architecture():
 fig,ax=plt.subplots(figsize=(13.3,3.0));ax.set_xlim(0,13.3);ax.set_ylim(0,3);ax.axis('off')
 labels=[('Official source\nsummary + URL',.5),('Clean + validate\nversion metadata',2.7),('TF-IDF word\n+ character',4.9),('8 feature\nreranker',7.1),('Safety +\nabstention',9.3),('Cited\nresponse',11.5)]
 for j,(label,x) in enumerate(labels):
  ax.add_patch(FancyBboxPatch((x,.95),1.66,.95,boxstyle='round,pad=0.14,rounding_size=0.15',fc=('#dff0f2' if j in (0,5) else '#ecf1f7'),ec='#40838a',lw=1.1));ax.text(x+.83,1.425,label,ha='center',va='center',fontsize=9,color='#10263c',fontweight='bold')
  if j<5:ax.add_patch(FancyArrowPatch((x+1.8,1.42),(x+2.13,1.42),arrowstyle='-|>',mutation_scale=15,color='#66808f',lw=1.5))
 ax.text(6.6,.3,'CPU-only  •  no API key  •  no robot command execution  •  provenance preserved',ha='center',fontsize=9,color='#445b6c')
 fig.savefig(FIG/'00_architecture.png',dpi=150,bbox_inches='tight',facecolor='white');plt.close(fig)
architecture()
output=root/'FN_JoseTuozzo_TungTungTungSahar_ITAI2377.pdf'
doc=SimpleDocTemplate(str(output),pagesize=(page_w,page_h),leftMargin=44,rightMargin=44,topMargin=61,bottomMargin=65,title='RoboGuide — Domain-Specific AI Assistant: Implementation and Evaluation',author='Group Tung Tung Tung Sahar (contributions pending verification)')
W=page_w-88
st=[]
def add(*items):st.extend(items)
def section(title):add(P(title,'h1'))
def sub(title):add(P(title,'h2'))
def new():add(PageBreak())

# Cover
add(Spacer(1,47),P('APPLIED ARTIFICIAL INTELLIGENCE  /  TECHNICAL REPORT','h3'),Spacer(1,14),
    Paragraph('<font color="#10263C">RoboGuide AI</font>',ParagraphStyle('cover',fontName='DejaVu-Bold',fontSize=37,leading=48,textColor=NAVY)),
    P('A traceable, version-aware PiDog troubleshooting assistant','h1'),
    P('Functional CPU-first prototype | Data engineering | Hybrid retrieval | Safety gating | Reproducible evaluation','body'),
    HRFlowable(width=W,thickness=2.2,color=TEAL,spaceBefore=20,spaceAfter=20))
add(*figure(FIG/'00_architecture.png',500,'Figure 1. Actual offline prototype workflow: version-aware evidence retrieval and extractive citation generation.'))
add(Spacer(1,15),tab([
 ['COURSE','GROUP / AUTHORS'],['ITAI 2377 — Data Science for AI','Tung Tung Tung Sahar\nJosé Tuozzo • Kim Nguyen • Huu Huynh'],
 ['REPORT STATUS','SUBMISSION CONVENTION'],['Reproducible technical draft; teammate statements need sign-off','FN_JoseTuozzo_TungTungTungSahar_ITAI2377.pdf'],
 ['DATE','PLANNED COURSE DELIVERY'],['November 10, 2026','December 2, 2026 (Canvas course overview)']],[245,260]))
add(Spacer(1,12),P('<b>Integrity statement:</b> All quantitative results in this report were generated by executing the included scripts locally. This is an educational prototype, not a deployed support service, and not a manufacturer-endorsed product.','small'))
new()

section('01  Executive summary')
add(P('RoboGuide transforms symptom-level PiDog questions into source-linked, actionable manufacturer guidance. The key problem is that students describe a shaky gait, silent speaker or sensor failure in everyday language while the manual is organized by components, versions and APIs. The implemented prototype indexes 24 labeled, source-attributed summaries of official SunFounder documentation and retrieves relevant evidence without a GPU, API key or robot connection.'))
sub('Measured pilot results')
D=M['development_hybrid'];B=M['development_baseline'];T=M['test_hybrid'];TB=M['test_baseline']
add(tab([['Metric','Development (35 queries)','Fixed test slice (8 queries)'],
 ['Hybrid Recall@3',f"{D['recall_at_3']:.1%}",f"{T['recall_at_3']:.1%}"],
 ['Hybrid MRR@5',f"{D['mrr_at_5']:.1%}",f"{T['mrr_at_5']:.1%}"],
 ['TF-IDF baseline MRR@5',f"{B['mrr_at_5']:.1%}",f"{TB['mrr_at_5']:.1%}"],
 ['Status classification accuracy',f"{D['status_accuracy']:.1%}",f"{T['status_accuracy']:.1%}"],
 ['Median response latency',f"{D['median_latency_ms']} ms",f"{T['median_latency_ms']} ms"]],[196,158,151]))
add(P('Development MRR improved from 0.7742 to 0.8387 (+0.0645 absolute). The fixed test slice has identical retrieval metrics for both methods (MRR@5 = 1.0), so there is <b>no demonstrated held-out retrieval gain</b> in these eight cases. Stronger claims require more independent queries.','small'))
sub('What is implemented')
add(*bullets(['Auditable knowledge schema with version, subsystem, authority and direct source URLs.',
 'Canonical cleaning, staged data-quality comparisons and a safe online source-ingestion utility.',
 'Word/character TF-IDF retrieval plus eight explicit engineered ranking signals; categorical encoding and numeric normalization.',
 'Deterministic safety escalation, low-evidence abstention and cited extractive answers.',
 '43-question benchmark, Recall@3, MRR@5, error tables, permutation feature importance, ablation experiments, 19 passing automated tests and Colab notebook.']))
add(P('<b>Not demonstrated:</b> a 150–250 independently labeled benchmark, full 80–150-source crawl, FAISS/Sentence Transformers evaluation, human citation scoring, calibrated probabilistic confidence or physical PiDog validation. Those were planned targets, not outcomes.','small'))
new()

section('02  Alignment with the midterm plan and assignment')
add(P('The instructor praised the original feature engineering table, particularly error fingerprinting, evidence confidence gating and a CPU-only fallback, but requested <b>who completed the plan-writing, diagrams and references</b> in addition to future job ownership. This report retains these strengths and includes a contribution-verification protocol.'))
add(tab([['Midterm design / final requirement','Implementation evidence','Status'],
 ['Manufacturer knowledge base; data schema','24 curated official-source summaries with source_url, version and subsystem','Implemented pilot'],
 ['Missing values / duplicates / text cleaning','Intentionally dirtied staging fixture, canonical restoration, before/after metrics','Demonstrated'],
 ['Numerical scaling and categorical encoding','StandardScaler + OneHotEncoder fit on development candidates','Implemented'],
 ['3–5 engineered features + importance','8 features, grouped-question permutation AP and MRR ablation','Implemented'],
 ['Semantic embeddings and FAISS','CPU TF-IDF word + character vectors; no neural/FAISS benchmark','Adapted'],
 ['Evidence-based interface and five demos','Command-line + Gradio; eight reproducible conversations','Implemented'],
 ['Evaluation / comparison to baseline','43 manually authored questions; deterministic fixed split','Pilot scope'],
 ['Team contributions for completed work','Signed statements still needed from each named member','Pending verification']],[195,244,66]))
sub('Why the architecture changed')
add(P('The plan proposed 384-dimensional MiniLM embeddings, a FAISS vector index, and an optional small instruction generator. With restricted network access and CPU-first requirements, the evaluated build instead uses scikit-learn TF-IDF and deterministic extractive synthesis. This lowers setup friction, eliminates generative hallucination from the answer-writing step, and exposes interpretable ranking signals. It also reduces semantic paraphrase capacity and must not be represented as having evaluated MiniLM, FAISS or a language model.'))
new()

section('03  Data provenance and quality')
add(P('The offline corpus has 24 manually curated, <b>paraphrased summaries</b> of sections in the SunFounder PiDog FAQ, calibration guide, Python API lessons, official PiDog GitHub repository and Robot HAT documentation. These are not 24 live HTML downloads. URLs, source_type, document IDs, hardware version, subsystem, review status and attribution are retained in each record.'))
sub('Schema and update strategy')
add(tab([['Field','Purpose / validation'],['id / title','Unique document key and concise human-readable evidence title'],['content','Text summary preserving important commands and model names'],['version','One of standard, v2, shared; hard exclude incompatible chunks'],['subsystem','Hardware/software category for diagnostics and analysis'],['source_url / source_type','HTTPS source provenance and explicit curated-summary label'],['authority / retrieved_on','Manufacturer-backed status and a date of documentation review'],['review_status','Reminder that physical steps require human cross-check']],[152,353]))
sub('Controlled data corruption experiment')
q=M['quality'];add(P('The raw staging fixture intentionally introduces two duplicate IDs, two missing required cells, one boilerplate record and one invalid version tag. The cleaning stage uses a trusted canonical key to restore those fields, strips noise and drops repeats. This verifies a repair mechanism; it is <b>not</b> an observation that official documentation was corrupt.'))
add(*figure(FIG/'01_quality_before_after.png',486,'Figure 2. Explicitly simulated data-quality defects before versus after preprocessing.'))
new()

section('04  Data transformation and engineered features')
add(P('Two vectorizers are independently fitted to the canonical corpus: word unigrams/bigrams and character 3–5-grams with sublinear TF-IDF weights. Each candidate evidence record receives eight numeric features. For exploratory relevance modeling, numeric values are standardized using development-only statistics, and version/subsystem categories are encoded with a development-only one-hot vocabulary. The ranking formula itself consumes its directly interpretable raw [0,1]-scale features.'))
add(tab([['Feature','Signal','Why it exists'],
 ['Word similarity','TF-IDF cosine','Lexical evidence matching; baseline'],
 ['Character similarity','Character-gram cosine','Robustness to spelling and token variations'],
 ['Entity overlap','PiDog terminology dictionary','Sensors, servo, RGB, API names'],
 ['Title overlap','Normalized meaningful words','Boosts exact procedure matches'],
 ['API match','Methods/function identifiers','Preserves code-token specificity'],
 ['Error fingerprint match','Exception class + normalized message','Merges path/line-variant failures'],
 ['Version compatibility','Standard / V2 / shared','Blocks incompatible hardware steps'],
 ['Source authority','Explicit source score','Prioritizes manufacturer-supported evidence']],[155,166,184]))
add(P('<b>Fingerprint demonstration:</b> different stack-trace paths and line numbers with the same <i>ModuleNotFoundError: No module named robot_hat</i> normalize to the same stable signature. This behavior is tested; benchmark attribution to fingerprint is zero because the tiny corpus contains no matching traceback documents. A zero measured importance is not the same as an unimplemented feature.','small'))
new()

section('05  Feature importance and interpretability')
imp=M['feature_importance'];add(P(f"A candidate-level logistic relevance model was trained on ranking features for exploratory permutation analysis. Train/test candidate sets were grouped by query ID to limit leakage. The query-group holdout average precision was {imp.get('holdout_average_precision',0):.3f} over {imp.get('holdout_questions',0)} questions. The plot reports change in average precision when one feature is shuffled: positive values indicate helpful signal under this specific setup; negative values indicate instability, redundancy or possible overfit, not intrinsic harm."))
add(*figure(FIG/'03_feature_importance.png',480,'Figure 3. Grouped-query permutation importance on candidate relevance. Small-sample estimate; not a causal explanation.'))
sub('Ranking-feature ablations')
abl=M['development_mrr_drop_by_ablation']
order=sorted(abl,key=lambda k:-abl[k])
add(tab([['Feature disabled','Development MRR@5 decrease'],*[[k,f'{abl[k]:+.4f}'] for k in order]],[315,190]))
# Avoid forced overflow: include this caveat in README for extended analysis.
new()

section('06  Core interaction, guardrails and UI')
add(P('The system exposes `RoboGuide.search()` to retrieve scored evidence and `RoboGuide.ask()` to deliver a structured status, cited extractive response and latency. A Gradio interface and Python CLI exercise the same core service. The application never opens a serial port, calls PiDog movement methods, executes the supplied traceback, or connects to user hardware.'))
add(*figure(FIG/'00_architecture.png',500,'Figure 4. Retrieval and answer control flow (the local implementation does not use a generative LLM).'))
sub('Answer decision contract')
add(tab([['Condition','Behavior'],
 ['Hazardous modification language','Escalate; do not provide bypass/rewiring instructions'],
 ['Recognized clearly unrelated request','Out-of-scope answer, no spurious robot solution'],
 ['Vague unresolved symptom','Ask for version, subsystem and exact error'],
 ['No applicable evidence / weak matching','Escalate and request more specific context'],
 ['Supported evidence found','Return selected manufacturer-attributed summaries, source IDs and URLs']],[204,301]))
add(P('<b>Evidence-strength limitation:</b> the visible numerical signal is an uncalibrated score built from top result similarity, entity overlap and rank margin. It is intentionally labeled <i>evidence strength</i> instead of implying a validated probability that the instructions are true or safe. No hallucination-rate benchmark was conducted.','small'))
new()

section('07  Retrieval and decision evaluation')
add(P('A manually authored 43-question set covers calibration, version compatibility, action scheduling, installation, sensors, I2C, audio, power, ambiguous prompts, non-PiDog topics and unsafe requests. The fixed split includes 35 development and 8 test examples. Retrieval scores exclude examples without gold source IDs, while status and intent scores use all examples. The corpus and questions both originate from the same documentation domain, limiting external validity.'))
add(*figure(FIG/'02_baseline_vs_hybrid.png',480,'Figure 5. Eight-question fixed test slice: neither system has an advantage in retrieval here.'))
add(tab([['Metric','Baseline (dev)','Hybrid (dev)','Baseline (test)','Hybrid (test)'],
 ['Recall@3',f"{B['recall_at_3']:.3f}",f"{D['recall_at_3']:.3f}",f"{TB['recall_at_3']:.3f}",f"{T['recall_at_3']:.3f}"],
 ['MRR@5',f"{B['mrr_at_5']:.3f}",f"{D['mrr_at_5']:.3f}",f"{TB['mrr_at_5']:.3f}",f"{T['mrr_at_5']:.3f}"],
 ['Status accuracy',f"{B['status_accuracy']:.3f}",f"{D['status_accuracy']:.3f}",f"{TB['status_accuracy']:.3f}",f"{T['status_accuracy']:.3f}"],
 ['Intent accuracy',f"{B['intent_accuracy']:.3f}",f"{D['intent_accuracy']:.3f}",f"{TB['intent_accuracy']:.3f}",f"{T['intent_accuracy']:.3f}"]],[140,91,91,91,91]))
add(P('Development results support the hypothesis that inexpensive engineered signals can improve early ranking. The eight-query test slice was inspected during prototype work, so it must be treated as exploratory rather than a genuinely untouched external test. There is no claim that the planned Recall@3 ≥0.85 target generalizes to real-world failures.','small'))
new()

section('08  Representative assistant interactions')
add(P('The following examples are literal records from `results/interactions.json` produced by calling the implemented code. Source citations are provided as links in the JSON and in the notebook. Text excerpts below are abbreviated to fit this report.'))
for j,item in enumerate(interactions[:6],1):
 add(P(f'{j}. {escape(item["question"])}','h3'),P(f'<b>Outcome:</b> {item["status"]}  |  evidence strength: {item["strength"]:.3f}  |  sources: '+', '.join(escape(x['id']) for x in item['sources']),'small'))
 excerpt=item['answer'].split('[S1]')[0].split('\n\n')[-1]
 add(P(escape(excerpt[:270]+('…' if len(excerpt)>270 else '')),'small'))
new()

section('09  Safety, errors and failure analysis')
add(P('Version filtering is mandatory before ranking. A Standard/V1 zeroing procedure is excluded for V2-specific prompts; a V2 zero-button instruction is excluded for Standard-specific prompts. The assistant cannot certify a hardware diagnosis. Camera advice explicitly prohibits live cable changes; servo calibration favors manufacturer instructions; battery-protection bypass requests are escalated.'))
sub('Representative development and test failures')
add(*bullets(['Very short ambiguous prompts can still fail the heuristic classifier and be escalated rather than clarified.',
 'Intent-label rules can confuse sound/audio, RGB/I2C and hardware-version questions; ranking success and intent labeling are evaluated separately.',
 'Out-of-domain detection combines lexical heuristics with a similarity gate and is not robust against all adversarial prompts.',
 'High source relevance is not sufficient evidence that real-world instructions are electrically safe for an unknown robot model.',
 'When a source contains an error or an outdated instruction, extraction faithfully reproduces it; a source-review workflow is necessary.']))
add(P('The benchmark contains intentionally unsafe and out-of-scope prompts. The outcomes and failures are preserved per question in `results/per_question_results.csv` rather than silently cherry-picking successful demos.'))
sub('What was not independently verified')
add(P('Human groundedness rubric, citation correctness percent, real-world PiDog task-resolution rate, hardware calibration accuracy and error-reduction time have not been measured. These must remain marked as <b>not evaluated</b>; converting target thresholds from the midterm plan into “achieved” values would be misleading.'))
new()

section('10  Engineering reproducibility and testing')
add(P('The repository includes structured Python modules, a Colab notebook with executed outputs, a Gradio interface, pytest tests, source provenance, feature tables, visualizations, benchmark files and JSON/CSV evaluation artifacts. Environment requirements are provided in `pyproject.toml` and `requirements.txt`.'))
add(tab([['Task','Reproducible command'],
 ['Install project and tests',"python -m pip install -e '.[test,ui,online]'"],
 ['Run test suite','python -m pytest -q'],
 ['Evaluate and regenerate plots','python -m roboguide.evaluation'],
 ['Ask a question','python -m roboguide "My PiDog wobbles"'],
 ['Launch browser UI','python -m roboguide.app'],
 ['Optional live docs acquisition','python -m roboguide.ingest --online']],[196,309]))
add(P('<b>Observed execution in this sandbox:</b> 19 pytest tests passed; the Colab-format notebook executed successfully using the local Python kernel; evaluation generated CSV, JSON, and four performance/data-quality figures. Internet-only data acquisition and external Gradio hosting were not executed here.'))
sub('Dataset/version controls')
add(*bullets(['Rebuild the curated corpus from `data/make_corpus.py` and benchmark from `data/make_benchmark.py`.',
 'Keep source URL, fetch date, digest and human-reviewed version tag on expanded online snapshots.',
 'Never commit robot credentials, personal telemetry, private logs or API secrets.',
 'Freeze new evaluation questions before changing scoring thresholds; maintain a documented change log.',
 'Review any hardware procedure and source terms before publishing lengthy copied code.']))
new()

section('11  Reflection and prioritized roadmap')
add(P('The strongest outcome is a reproducible retrieval engine with transparent feature attribution, controlled version gating and extractive answers. The main trade-off is scale and semantic richness: a small manually curated corpus demonstrates engineering discipline but cannot prove broad coverage. The CPU-only design remains valuable because it works without cloud credits and fails safely when stronger generation is unavailable.'))
add(tab([['Priority','Milestone','Acceptance test'],
 ['P0','Independent source ingestion; version/code review','80+ official pages/files with hashes, provenance, code-fidelity review'],
 ['P0','External issue benchmark','150–250 labeled, non-template, held-out real questions'],
 ['P1','MiniLM + FAISS comparison','CPU memory, Recall@3 and MRR compared to lexical baseline'],
 ['P1','Calibrated abstention','Separate validation threshold + false-answer/false-refusal analysis'],
 ['P1','Citation review','Blind check per adjacent claim and command against exact source'],
 ['P2','Optional local LLM grounded synthesis','Answer supports only verified evidence; no invented API calls'],
 ['P2','Real user study','Instructor-reviewed tasks on powered-down/safe robot setup and survey']],[64,190,251]))
add(P('The above milestones are proposals, not delivered capabilities. A full professional release should also add accessibility checks, software bill of materials and dependency scanning, licenses for source excerpts, model cards, incident logging without personal identifiers and a hard human-in-the-loop procedure for hazardous instructions.'))
new()

section('12  Team collaboration and contribution verification')
add(P('The course and instructor require an account of work <b>already performed</b> by each member, including who drafted the plan, diagrams and references—not only who was assigned upcoming tasks. The midterm lists the roster and planned ownership but does not establish each student’s actual authored portions. Statements below are therefore proposed verification prompts; team members must revise them before submission.'))
for name,assignment in [
 ('José Tuozzo','pipeline integration, evaluation framework, end-to-end QA and technical editing'),
 ('Kim Nguyen','source collection, manifest and version tagging, parsing, deduplication and quality review'),
 ('Huu Huynh','retrieval/index research, response/UI features, feature extraction and user testing')]:
 add(P(name,'h3'),P(f'<b>Ownership assigned in the midterm:</b> {escape(assignment)}. <b>Completed work to verify:</b> describe 2–3 sentences covering actual implementation/code changes, authored report sections, midterm plan writing, diagrams, references, experiments and dates. Cite Git commits or a shared document revision history where available. Do not attribute the current code to this student unless verified.','small'))
add(P('<b>Draft provenance:</b> This prototype/report was prepared with AI coding and editing assistance. José and teammates should inspect it, run it, independently verify sources, and correct the author and contribution statements before presenting it as group work. Academic responsibility remains with the submitting students.','small'))
add(tab([['Verification checklist','Team confirmation'],['Who drafted midterm executive, methodology and references?','[To be completed]'],['Who designed the three midterm architecture/schema/pipeline diagrams?','[To be completed]'],['Who wrote, reviewed, tested or corrected implementation modules?','[To be completed]'],['Who ran independent tests and checked numeric evidence?','[To be completed]'],['Agreement by José / Kim / Huu with dates','[To be completed]']],[353,152]))
new()

section('13  References and submission inventory')
refs=[
 ('SunFounder','PiDog Documentation','https://docs.sunfounder.com/projects/pidog/en/latest/'),
 ('SunFounder','PiDog FAQ','https://docs.sunfounder.com/projects/pidog/en/latest/faq.html'),
 ('SunFounder','Calibrating PiDog','https://docs.sunfounder.com/projects/pidog/en/latest/python/py_0_calibrate.html'),
 ('SunFounder','Preset Action API','https://docs.sunfounder.com/projects/pidog/en/latest/python/py_b6_preset_action.html'),
 ('SunFounder','Robot HAT Documentation','https://docs.sunfounder.com/projects/robot-hat/en/latest/'),
 ('SunFounder','PiDog GitHub Repository','https://github.com/sunfounder/pidog'),
 ('scikit-learn','TF-IDF Vectorizer Documentation','https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html'),
 ('scikit-learn','Permutation Importance Documentation','https://scikit-learn.org/stable/modules/permutation_importance.html'),
]
for i,(au,title,url) in enumerate(refs,1):
 add(P(f'[{i}] {escape(au)}. <i>{escape(title)}</i>. <link href="{escape(url)}" color="#136F7B">{escape(url)}</link>','small'))
sub('Submission inventory')
add(*bullets(['This PDF: FN_JoseTuozzo_TungTungTungSahar_ITAI2377.pdf',
 'notebooks/RoboGuide_Colab.ipynb — complete, executed, well-commented notebook',
 'roboguide/ — reusable Python package, Gradio app, preprocessing and evaluation',
 'data/ — explicit source-attributed curated corpus and manually authored benchmark',
 'docs/figures/ — before/after quality, baseline, importance, corpus/architecture plots',
 'results/ — exact metrics.json, case-level results CSV, processed sample and interaction traces',
 'docs/CONTRIBUTIONS_TEMPLATE.md — sign-off required to finalize group authorship.']))
add(P('<b>Important:</b> The original assignment paste contains a contradictory old May 1, 2025 timestamp below a November 2026 Canvas due date. Use the current Canvas course due-date setting (December 2, 2026, 11:59 p.m.) as your reference, and verify with the instructor before final submission.','small'))

# Last PDF narrative
try:
 doc.build(st,onFirstPage=page_header,onLaterPages=page_header)
 print('REPORT',output,output.stat().st_size)
except Exception as e:
 print('Build report error:',e);raise
