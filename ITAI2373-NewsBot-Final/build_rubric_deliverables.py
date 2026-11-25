"""Generate rubric-compliant academic deliverables with actual speaker notes.
Run only after reviewing evidence. No synthetic metric is presented as real-world performance."""
from pathlib import Path
from xml.sax.saxutils import escape
import shutil,json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reports';OUT.mkdir(exist_ok=True)
SUB=ROOT/'submission';SUB.mkdir(exist_ok=True)
NAME='JoseMiguelTuozzo_JoseGroup_ITAI2373'
STUDENT='José Miguel Tuozzo Izaguirre'
URL='https://github.com/jtuozzo1616/Final-Jose-Group-NewsBot-Intelligence-System'
navy=colors.HexColor('#14243A');teal=colors.HexColor('#087E84');gray=colors.HexColor('#4C6073')
styles={
 'title':ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=25,leading=29,textColor=navy,spaceAfter=14),
 'sub':ParagraphStyle('sub',fontName='Helvetica',fontSize=10,leading=14,textColor=gray,spaceAfter=18),
 'h':ParagraphStyle('h',fontName='Helvetica-Bold',fontSize=14,leading=18,textColor=teal,spaceBefore=13,spaceAfter=6),
 'body':ParagraphStyle('body',fontName='Helvetica',fontSize=10.5,leading=15,spaceAfter=8,textColor=navy),
 'small':ParagraphStyle('small',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=7,textColor=gray)}
def P(s,kind='body'):return Paragraph(escape(s).replace('\n','<br/>'),styles[kind])
def foot(canvas,doc):
    canvas.setFillColor(navy);canvas.rect(0,letter[1]-30,letter[0],30,fill=1,stroke=0)
    canvas.setFont('Helvetica-Bold',9);canvas.setFillColor(colors.white);canvas.drawString(42,letter[1]-19,'HOUSTON COMMUNITY COLLEGE  /  ITAI 2373  /  NEWSBOT 2.0')
    canvas.setStrokeColor(colors.HexColor('#CBD5DF'));canvas.line(42,42,570,42)
    canvas.setFillColor(gray);canvas.setFont('Helvetica',8);canvas.drawString(42,28,STUDENT+'  |  November 2026');canvas.drawRightString(570,28,str(doc.page))
def pdf(name,title,pages):
    story=[]
    for i,(heading,sections) in enumerate(pages):
        if i:story.append(PageBreak())
        story.extend([P(title if i==0 else heading,'title'),P(STUDENT+'  |  JoseGroup  |  Final capstone' if i==0 else 'NewsBot Intelligence System 2.0','sub')])
        if i==0 and heading!=title:story.append(P(heading,'h'))
        for h,text in sections:
            story.extend([P(h,'h'),P(text)])
    path=OUT/name
    SimpleDocTemplate(str(path),pagesize=letter,leftMargin=46,rightMargin=46,topMargin=51,bottomMargin=53).build(story,onFirstPage=foot,onLaterPages=foot)
    return path

def textfile(name):return (ROOT/'docs'/name).read_text()
technical=[
('Architecture and scope',[
('Purpose','NewsBot 2.0 extends the historical BBC midterm into a modular analysis workspace. Four integrated capabilities: content analysis, language understanding/generation, multilingual discovery and conversational exploration. Data are imported as CSV or JSONL; every article has stable ID, normalized title/body, source and SHA-256. The fixture contains 30 fictional records. Real historical BBC evaluation is reported separately.'),
('System design','Input validation -> provenance -> classification / topic discovery / sentiment / entities -> retrieval -> source-grounded response and structured reports -> Streamlit, API, CLI. The src/ namespace provides course-aligned interfaces to the canonical newsbot2/ package; config, seven notebooks, tests and reports are separate.'),
('Trust boundaries','No automatic remote article fetching by API. Import capped at 8 MB and 3,000 records; model files are pickle-backed and must be trusted. Synthetic source flags survive analysis. Source citation establishes provenance, not truth. No production security or external validation is claimed.')]),
('Advanced analysis',[
('LDA and NMF','LDA uses count vectors and a probabilistic topic mixture. NMF decomposes nonnegative TF-IDF features. Both report top terms, normalized document distributions and dominant topics. K-means groups documents by topic distribution. Fixed seed 42 supports reproducibility. Zero NMF weights receive an explicitly flagged uniform prior.'),
('Temporal and entity analysis','Monthly topic means and lexical sentiment trends use only supplied dates. Missing dates and insufficient periods are reported; sentiment methods are kept separate. Entity pairs represent within-document co-mentions and retain source IDs. They are not causal relationships.'),
('Classification','Local logistic regression and historical SVM expose ranked uncalibrated scores. An explicit taxonomy maps each predicted label to a broader parent. Stratified out-of-fold predictions fit TF-IDF only inside training folds; no final-test selection.')]),
('Understanding and multilingual intelligence',[
('Summary and enhancement','MMR ranks source sentences by centroid relevance minus redundancy, then restores order. Templates propose editorial headlines. Query expansion adds visible domain synonyms. Search supports TF-IDF pivot, LSA and actual pretrained MiniLM vectors.'),
('Multilingual evidence','The verified MiniLM model produced 384-dimensional vectors. In four selected synthetic probes, MRR@3 was 0.75 neural versus 0.625 lexical. Three real Argos ES-to-EN translations succeeded; these are not human-rated quality results. Language hints support EN, ES, FR, DE. Compare actual coverage by source; language is not nationality or culture.'),
('Conversation','Bounded session history resolves follow-up references. Rules identify multiple intents, category, tone, date, and user preferences. Source excerpts are returned with IDs; inadequate lexical evidence triggers abstention. JSON reports preserve filters, warnings and source identifiers.')]),
('Installation and configuration',[
('Setup','Python 3.11 recommended. Clone '+URL+' and enter final-newsbot-2.0. Run python -m pip install -r requirements-dev.txt; python -m pytest tests -q; python run_research.py; streamlit run app.py. Seven Colab tutorials clone and install dependencies when needed.'),
('Options','NEWSBOT_DEMO_ONLY=1 forces local demo classifier. NEWSBOT_ENABLE_NEURAL=1 exposes optional embedding loading after installing requirements-advanced.txt. Argos packages must be installed separately; download requires network, inference is local. Default no paid API.'),
('Deployment','Streamlit Community Cloud or Docker/Render configuration is provided. A public URL requires account authorization and health verification. A production service also needs authentication, quotas, TLS, monitoring, licensing and human review.')]),
('API reference and tests',[
('HTTP contracts','Run uvicorn newsbot2.api:app --reload; /docs exposes OpenAPI. GET /health, /overview, /articles, /articles/{id}/analysis and /topics; POST /search and /chat accept query (2–1000 characters) and k (1–10). Unknown article returns 404.'),
('Advanced endpoints','GET /advanced/topics?method=lda&n=4, /advanced/sentiment, /advanced/entities, /advanced/languages; POST /advanced/query. Stateless HTTP requests prevent cross-client conversation leakage.'),
('Library','Article, import_articles, NewsBotEngine, Classifier, Retriever, Conversation, discover_topics, sentiment_timeline, entity_network, language_comparison, structured_query, expand_query, hierarchy and export_report. Detailed signatures and controls: docs/api_reference.md; advanced.py documents each function. Tests cover data validation, source grounding, API, distributions and multi-intent queries.')]),
('Evaluation, limitations and references',[
('Verified historical and controlled experiments','Historical BBC 288-record holdout: 96.18% accuracy and 0.9605 macro-F1. Synthetic 30-record CV: 0.5371 baseline macro-F1, 0.5720 pivot, 0.6143 pivot + characters. Selected 24 retrieval probes: MRR 1.0 with pivot vs 0.625 without. These are distinct experiments; no independent multilingual generalization is asserted.'),
('Further evaluation','Use an approved licensed corpus, publisher- and time-separated independent samples, human-rated translation and summary faithfulness, calibrated uncertainty and answerability, measured latency and realistic load tests. See evidence/ for actual run outputs.'),
('References and integrity','Blei et al. (2003), Latent Dirichlet Allocation, JMLR 3; Lee & Seung (1999), Nature 401; Reimers & Gurevych (2019), Sentence-BERT, EMNLP; Carbonell & Goldstein (1998), MMR, SIGIR. Libraries: scikit-learn, FastAPI, Streamlit, Argos Translate, Sentence Transformers. AI assistance was used for code, documentation, experiments and repository organization. Individual contributions and instructor approval must reflect actual work.')])]
executive=[('Executive decision brief',[
('Business value','NewsBot consolidates approved article collections into a traceable analysis workflow. Editorial teams can triage content, compare topic coverage, search sources across languages and export structured evidence. Local-first operation avoids mandatory paid API inference.'),
('Use cases','Newsroom: review overlapping stories and source excerpts. Policy analyst: compare coverage by language and date. Academic researcher: reproduce NLP experiments and inspect model limitations. These are proposed scenarios, not customer deployments.'),
('ROI and payback — illustrative','Assume two analysts, 10 review hours each/week, 20% savings, 48 weeks and $30/hour. Recovered time: 192 hours/year; gross value $5,760. Assume $1,800 setup/training plus $600 hosting/support, total $2,400. Net $3,360; ROI 140%; simple payback 5 months if all cost is upfront. At 10% savings ROI is 20%; at 30%, 260%. No savings have been measured.'),
('Competitive position','Manual search: high human control but repetitive triage. Commercial monitoring: managed feeds/support but licensing and less internal control. General LLM: flexible synthesis but requires privacy, grounding and evaluation engineering. NewsBot: transparent provenance, offline analysis and reproducible experiments; lacks licensed live feeds and production controls.'),
('Decision and risk','Pilot on approved sources; measure review time, citation precision, class/language performance and costs before deployment. Historical and fictional metrics are not production guarantees. Human editorial review remains essential.')])]
reflection=[
('Design and learning',[
('Reflection on development','The supplied journal explains that accuracy is only one part of a useful NLP system. Moving from the historical BBC classification task to retrieval, multilingual access, conversational interaction and evidence-based responses revealed distinct failure modes. A correct category does not guarantee relevant retrieval, and a plausible response does not guarantee evidence. System architecture, data quality, compute and error handling matter together.'),
('Critical interpretation','The fictional evaluation cannot establish generalization to real journalism. Business and entertainment weaknesses may be concealed by overall accuracy, while hand-selected vocabulary probes favor the dictionary. Independent questions, publishers, languages and time periods would improve experimental validity. Macro-F1, class-level precision and recall, confusion matrices and error analysis should be reported together.'),
('Engineering trade-offs','Extractive answers preserve source passages and are CPU-friendly, but may not fully answer comparative questions. A finite dictionary is interpretable and efficient but cannot reliably resolve synonyms, idioms and context. Similarity is not evidence of truth; uncertainty may justify clarification or abstention.')]),
('Ethics and improvement',[
('Information reliability','Historical datasets can reflect editorial choices and cultural limitations. Citations allow inspection but cannot establish that an article is correct, current or objective. The system should distinguish recorded statements, interpretations, conflicting evidence and uncertainty. Human critical judgment is essential.'),
('Personal learning','The supplied reflection identifies a more mature understanding of the interaction between NLP, machine learning, information retrieval and software engineering. A reliable system should acknowledge limitations rather than conceal them. More sophisticated technology should be justified through reproducible results, not novelty alone.'),
('Future work','Prioritize controlled feature ablations, independent multilingual queries, semantic and hybrid retrieval, calibrated confidence, documented failure modes, automated integration tests, dependency security and privacy. New production features require external validation and appropriate safeguards.')]),
('Accountability and conclusion',[
('Individual and team contributions','The November 25 student-supplied journal reports responsibility for planning, architecture, data processing, feature engineering, modeling, retrieval, multilingual capability, conversational response, testing, error analysis, technical documentation and repository organization under the JoseGroup label. This is self-reported; no additional members or instructor-approved solo arrangement are asserted. AI assistance was used in coding, debugging, writing, evaluation and repository organization and must be attributed according to the course rules. The student should confirm the exact personal contributions before submission.'),
('Conclusion','Responsible AI is more than producing predictions. The supplied reflection emphasizes rigorous assessment, supporting evidence, transparent limitations and the capacity to acknowledge uncertainty. These principles connect the project to future academic and professional work.'),
('Review note','This three-page condensed reading draft is derived from the student-provided five-page November 25 journal. Review it personally, revise the wording to reflect actual experiences and contributions, and confirm group policy before submitting. The original remains available separately.')])]
p1=pdf('technical_report.pdf','Technical documentation',technical)
p2=pdf('executive_summary.pdf','Executive summary',executive)
p3=pdf('reflective_journal_3pages.pdf','Reflective journal',reflection)
# Slide notes are meaningful oral prompts, not placeholders.
slides=[
('NewsBot Intelligence System 2.0','Evidence-first NLP for news intelligence',['Houston Community College | ITAI 2373','Final capstone | '+STUDENT,'Four modules, research, reproducibility'],'Introduce the problem: news analysis requires more than category accuracy. Explain how the historical midterm evolved into an integrated platform.'),
('Problem and value','From repetitive reading to traceable analysis',['Triage article collections','Explore topics, tone and source context','Keep editorial judgment with the user'],'Explain why repetitive source discovery and inconsistent provenance create cost. This is a proposed workflow, not a deployed customer product.'),
('Architecture','One shared engine, multiple interfaces',['Validate and fingerprint CSV/JSONL','Analyze, retrieve, route questions','Streamlit / FastAPI / CLI / exports'],'Walk through article IDs, SHA-256, synthetic flags and the separation of the API, UI and underlying reusable library.'),
('Data and lineage','Two evidence levels',['Historical BBC: 288 held-out articles','Final fixture: 30 fictional examples','Real corpus extension: aggregate-only evidence'],'Separate historical holdout from final synthetic evaluation. Real BBC articles are not redistributed; demonstrate approved data locally.'),
('Enhanced classification','Hierarchical editorial categories',['TF-IDF + logistic classifier / historical SVM','Ranked scores and parent-child taxonomy','Uncalibrated confidence, not truth'],'Explain the classifier origin, feature representation and why margins and estimated probabilities are not calibrated confidence.'),
('LDA and NMF','Two topic-discovery approaches',['LDA: count-based latent mixture','NMF: nonnegative TF-IDF decomposition','Top words and document distributions'],'Discuss how topic model objectives differ and why topic labels are exploratory. Mention zero-weight documents explicitly flagged.'),
('Clustering and evolution','Discover similar articles over time',['K-means on topic distributions','Monthly mean topic weights','Report missing dates and insufficient periods'],'Show the Research Lab chart and explain why one month cannot establish a trend. Use dated approved inputs for meaningful evolution.'),
('Sentiment and entities','Source-linked contextual analytics',['Lexical tone aggregated by scoring method','Named entities or marked candidate fallback','Co-mention edges with source IDs'],'Distinguish sentiment from political bias and co-mention from causality. Show a source record and its digest.'),
('Language understanding','Summaries, enhancement and search',['MMR: relevance minus redundancy','Template headlines with editor review','Visible domain query expansion'],'Explain why the extractive summary is traceable but not a complete reasoning system. Show a source sentence and original location.'),
('Learned semantic retrieval','Real multilingual MiniLM',['384-dimensional pretrained embeddings','Neural MRR@3 0.75; lexical 0.625','Four selected fictional probes'],'Open the verified embedding JSON. Explain cosine similarity and the small selected benchmark limitation.'),
('Translation and coverage','Language is not culture',['Three real Argos ES-to-EN translations','Language filter and coverage comparison','Human review of regional interpretation'],'Read the actual translation evidence. Explain that this demonstrates inference, not translation accuracy across languages.'),
('Conversational intelligence','Multi-intent, context and provenance',['Cited extracts and bounded follow-up','Category / tone / date / preference filters','Abstention and downloadable JSON'],'Demonstrate a multi-part query and an unrelated query. Explain the difference between source grounding and factual verification.'),
('Web demo','Five integrated workflows',['Command Center / Article Lab','Search & Languages / Grounded Chat','Research Lab / batch export'],'Open the verified screenshots, then use the live local application. Use an approved real dataset if available; label the fictional corpus.'),
('Experimental evaluation','Do not conflate datasets',['Historical BBC accuracy 96.18%','Synthetic macro-F1: 0.5371 → 0.6143','Paired folds; +0.0772 absolute gain'],'Explain out-of-fold prediction and why the 30-record results cannot support production accuracy. Discuss class-specific weaknesses.'),
('Quality and reproducibility','Evidence, tests and tutorial notebooks',['Fresh-kernel notebook execution','Browser tests and real model inference','Seven tutorial notebooks and CI logs'],'Open the latest completed run. Only state the actual passing test count and statuses shown in logs.'),
('Business impact','Illustrative ROI scenario',['192 hours/year recovered at 20% savings','$5,760 gross; $2,400 first-year cost','140% ROI; 5-month simple payback'],'Explain the assumptions and sensitivity. No time savings were measured. Compare manual search, commercial monitoring and general LLM workflows.'),
('Limitations and accountability','Responsible deployment',['Independent publisher/time benchmarks','Calibration, licensing, security, review','Actual contributions and AI attribution'],'Describe the real contributions personally, disclose AI assistance as required and confirm individual/team arrangement. Avoid overstating deployment readiness.'),
('Conclusion and Q&A','A reproducible research assistant',['Traceable answers, not automatic truth','Evidence: GitHub / notebook / browser / models','Questions and live demonstration'],'Invite technical questions. Explain one algorithm, one failure case and one future evaluation without notes. Close by linking to the final repository.')]
prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
def tx(slide,x,y,w,h,text,size,color,bold=False):
    box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=box.text_frame;tf.word_wrap=True
    p=tf.paragraphs[0];p.text=text;p.font.name='Aptos';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color)
for i,(title,sub,items,note) in enumerate(slides,1):
    slide=prs.slides.add_slide(prs.slide_layouts[6]);fill=slide.background.fill;fill.solid();fill.fore_color.rgb=RGBColor.from_string('101C30')
    tx(slide,.55,.35,12,.45,'NEWSBOT 2.0     /     ITAI 2373     /     FINAL CAPSTONE',13,'59D1C6',True)
    tx(slide,.55,1.03,12.1,1.1,title,36,'FFFFFF',True)
    tx(slide,.55,2.05,12,.65,sub,22,'B2C4D6')
    for j,item in enumerate(items):
        tx(slide,.8,3.08+j*.86,11.8,.75,'•  '+item,23,'FFFFFF')
    tx(slide,.55,6.87,11,.35,STUDENT+'   |   November 2026',12,'A1B2C6')
    tx(slide,12.15,6.87,.7,.35,f'{i:02d}',12,'59D1C6',True)
    slide.notes_slide.notes_text_frame.text=note
p4=OUT/'presentation.pptx';prs.save(p4)
# Preserve prior journal and explicitly distinguish the new three-page draft.
old=SUB/'FP_ReflectiveJournal_JoseGroup_ITAI2373.pdf'
archive=SUB/'Reflective_Journal_Original_Reading_Copy_5pages.pdf'
if old.exists() and not archive.exists():shutil.copy2(old,archive)
for src,dst in [(p1,'FP_TechnicalDoc_'+NAME+'.pdf'),(p2,'FP_ExecutiveSummary_'+NAME+'.pdf'),(p3,'FP_ReflectiveJournal_JoseGroup_ITAI2373.pdf'),(p4,'FP_Presentation_'+NAME+'.pptx')]:shutil.copy2(src,SUB/dst)
from pypdf import PdfReader
assert len(PdfReader(p3).pages)==3
assert len(prs.slides)==18 and all(s.notes_slide.notes_text_frame.text.strip() for s in prs.slides)
print('RUBRIC DOCUMENTS VERIFIED',len(PdfReader(p1).pages),len(PdfReader(p2).pages),len(PdfReader(p3).pages),len(prs.slides))
