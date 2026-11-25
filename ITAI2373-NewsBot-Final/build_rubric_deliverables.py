"""Generate rubric-compliant academic deliverables with actual speaker notes.
Run only after reviewing evidence. No synthetic metric is presented as real-world performance."""
from pathlib import Path
from xml.sax.saxutils import escape
import shutil,json
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

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
        if name=='technical_report.pdf' and i==0:
            story.append(Spacer(1,10))
            data=[[P('LAYER','small'),P('PURPOSE / CONTROL','small')],[P('Input','small'),P('Schema, provenance and bounded data','small')],[P('Analysis','small'),P('LDA/NMF, classification, sentiment, entities','small')],[P('Retrieval','small'),P('Lexical, LSA or pretrained embeddings','small')],[P('Application','small'),P('Grounded chat, intent routing, reports, UI/API','small')]]
            tab=Table(data,colWidths=[100,400]);tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E1F1F0')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F1F5F8'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(tab)
        if name=='technical_report.pdf' and i==5:
            data=[[P('Experiment','small'),P('Scope','small'),P('Macro-F1','small')],[P('Historical midterm','small'),P('288 held-out BBC','small'),P('0.9605','small')],[P('Final real-data pipeline','small'),P('250 BBC, 3-fold CV','small'),P('0.9079','small')],[P('Synthetic baseline','small'),P('30 fictional, paired CV','small'),P('0.5371','small')],[P('Synthetic pivot + char','small'),P('30 fictional, paired CV','small'),P('0.6143','small')]]
            tab=Table(data,colWidths=[165,245,90]);tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E1F1F0')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F1F5F8'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP')]));story.append(tab)
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
('Multilingual evidence','The verified MiniLM model produced 384-dimensional vectors. Actual FLAN-T5-small inference produced three one-sentence editorial drafts; source IDs, extractive references and warnings are retained. In four selected synthetic probes, MRR@3 was 0.75 neural versus 0.625 lexical. Three real Argos ES-to-EN translations succeeded; these are not human-rated quality results. Language hints support EN, ES, FR, DE. Compare actual coverage by source; language is not nationality or culture.'),
('Conversation','Bounded session history resolves follow-up references. Rules identify multiple intents, category, tone, date, and user preferences. Source excerpts are returned with IDs; inadequate lexical evidence triggers abstention. JSON reports preserve filters, warnings and source identifiers.')]),
('Installation and configuration',[
('Setup','Python 3.11 recommended. Clone '+URL+' and enter final-newsbot-2.0. Run python -m pip install -r requirements-dev.txt; python -m pytest tests -q; python run_research.py; streamlit run app.py. Seven Colab tutorials clone and install dependencies when needed.'),
('Options','NEWSBOT_DEMO_ONLY=1 forces local demo classifier. NEWSBOT_ENABLE_NEURAL=1 exposes optional embedding loading after installing requirements-advanced.txt. Argos packages must be installed separately; download requires network, inference is local. Default no paid API.'),
('Deployment','Streamlit Community Cloud or Docker/Render configuration is provided. A public URL requires account authorization and health verification. A production service also needs authentication, quotas, TLS, monitoring, licensing and human review.')]),
('API reference and tests',[
('HTTP contracts','Run uvicorn newsbot2.api:app --reload; /docs exposes OpenAPI. GET /health, /overview, /articles, /articles/{id}/analysis and /topics; POST /search and /chat accept query (2–1000 characters) and k (1–10). Unknown article returns 404.'),
('Advanced endpoints','GET /advanced/topics?method=lda&n=4, /advanced/sentiment, /advanced/entities, /advanced/languages; POST /advanced/query. Stateless HTTP requests prevent cross-client conversation leakage.'),
('Library','Article, import_articles, NewsBotEngine, Classifier, Retriever, Conversation, discover_topics, sentiment_timeline, entity_network, language_comparison, structured_query, expand_query, hierarchy and export_report. Detailed signatures and controls: docs/api_reference.md; advanced.py documents each function. 33 tests passed after adding topic distributions, multi-intent filters, three-month fictional timelines and shared-event source-region context. The dated scenario is explicitly fictional.')]),
('Evaluation, limitations and references',[
('Verified historical and controlled experiments','Historical BBC 288-record holdout: 96.18% accuracy and 0.9605 macro-F1. New final-pipeline evaluation: 250 balanced real BBC articles, 90.8% accuracy and 0.9079 macro-F1 using 3-fold CV. Both topic models fitted; unknown publication dates were not invented. Synthetic 30-record CV: 0.5371 baseline macro-F1, 0.5720 pivot, 0.6143 pivot + characters. Selected 24 retrieval probes: MRR 1.0 with pivot vs 0.625 without. These are distinct experiments; no independent multilingual generalization is asserted.'),
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
# Condensed from the student's submitted first-person journal; student approval remains required.
reflection=[
('Design and critical evaluation',[
('Reflection on design and development','One of the key takeaways from the NewsBot Intelligence System 2.0 is that accuracy is only one aspect of a good NLP system. The mid project was all about classification using the historical BBC data set. The final project then built on that by adding in information retrieval, multilingual capability, conversational ability and the ability to generate evidence based responses. A classifier can be absolutely correct in its classification of an article and yet the retrieval system will have utterly failed to retrieve anything relevant.'),
('System thinking','The project changed my view of AI in that you cannot just look at individual algorithms and say that is the end of the story. The effectiveness of an intelligent application is a function of how all the various parts of the system work together. Architecture, data quality, compute and error handling are critical to reliability.'),
('Critical interpretation of results','The synthetic evaluation demonstrates why good performance on a historical classification task does not necessarily mean you will perform well in a new domain. The poor recall in business and entertainment is a clear example of a limitation an overall accuracy figure would obscure. The multilingual questions favor terms already in the dictionary. A more rigorous design would have independently constructed questions, real articles from a range of publishers and time periods, and documents in a variety of languages. A proper assessment looks at weaknesses as much as successful predictions.')]),
('Engineering, ethics and learning',[
('Engineering trade-offs','The extractive response mechanism is a compromise between computational efficiency, transparency and linguistic flexibility. It operates in a CPU environment, but extractive approaches are limited for comparative reasoning, contextual interpretation or synthesis across documents. You can retrieve a relevant passage that does not actually answer a question. The dictionary-based language pivot is simple and understandable, but depends on its vocabulary and does not reliably cope with idioms, synonyms or contextual ambiguity.'),
('Information reliability','Retrieval confidence is another major issue. A high similarity score does not guarantee that information is correct. In some circumstances the right thing to do is to ask for clarification or acknowledge that there is not enough evidence. Source citations add transparency by allowing the reader to check the source; citing a document does not ensure that it is correct, current or objective. The system should assist critical human judgment, not replace it. Historical datasets may reflect editorial policies and cultural limitations. Production deployment also requires attention to dependency security, input validation, privacy and potentially misleading documents.'),
('Personal learning and future improvements','This project has deepened my understanding of the interaction between NLP, machine learning, information retrieval and software engineering. Recognizing limitations is crucial to developing more robust, scientifically valid systems. Future work should focus on controlled feature ablation, independent multilingual queries, semantic and hybrid retrieval, confidence calibration and documented failure modes. Technology should be justified through tangible benefits and reproducible experiments.')]),
('Contributions and conclusion',[
('Individual contribution','In my original journal, I described taking responsibility for project planning, system architecture, data preprocessing, feature engineering, modeling, retrieval, multilingual and conversational capabilities, experimentation, error analysis, documentation and repository organization. These areas represent the scope of the project work for which I take responsibility; my actual personal implementation, testing and review must be distinguished from tool-assisted work. AI assistance was used in coding, debugging, documentation, evaluation automation and repository organization, in accordance with the assignment attribution requirement.'),
('Team contribution','The project is organized under the JoseGroup label. The original reflection states that I took responsibility for the technical, analytical and documentation aspects. No other member contributions are identified in the supplied record; the final individual/group arrangement must reflect actual participation and instructor approval.'),
('Conclusion','NewsBot Intelligence System 2.0 demonstrates that building AI is far more than training a model and getting good evaluation scores. It requires disciplined experiments, engineering responsibility and an understanding of automated information processing limitations. A reliable system should acknowledge what it does not know, communicate its limitations and provide supporting evidence. Responsible AI is not only about what a system can do, but how rigorously its capabilities can be assessed, validated and justified.'),
('Review note','Condensed from the November 25 student-provided journal. Confirm personal wording and contributions before submission.')])]
p3=pdf('reflective_journal_3pages.pdf','Reflective journal',reflection)
# Slide notes are meaningful oral prompts, not placeholders.
slides=[
('NewsBot Intelligence System 2.0','Evidence-first NLP for news intelligence',['Houston Community College | ITAI 2373','Final capstone | '+STUDENT,'Four modules, research, reproducibility'],'Introduce the problem: news analysis requires more than category accuracy. Explain how the historical midterm evolved into an integrated platform.'),
('Problem and value','From repetitive reading to traceable analysis',['Triage article collections','Explore topics, tone and source context','Keep editorial judgment with the user'],'Explain why repetitive source discovery and inconsistent provenance create cost. This is a proposed workflow, not a deployed customer product.'),
('Architecture','One shared engine, multiple interfaces',['Validate and fingerprint CSV/JSONL','Analyze, retrieve, route questions','Streamlit / FastAPI / CLI / exports'],'Walk through article IDs, SHA-256, synthetic flags and the separation of the API, UI and underlying reusable library.'),
('Data and lineage','Two evidence levels',['Historical BBC: 288 held-out articles','Final fixture: 30 fictional examples','Final pipeline: 250 real BBC, 3-fold CV'],'Separate historical holdout from final synthetic evaluation. Real BBC articles are not redistributed; demonstrate approved data locally.'),
('Enhanced classification','Hierarchical editorial categories',['TF-IDF + logistic classifier / historical SVM','Ranked scores and parent-child taxonomy','Uncalibrated confidence, not truth'],'Explain the classifier origin, feature representation and why margins and estimated probabilities are not calibrated confidence.'),
('LDA and NMF','Two topic-discovery approaches',['LDA: count-based latent mixture','NMF: nonnegative TF-IDF decomposition','Top words and document distributions'],'Discuss how topic model objectives differ and why topic labels are exploratory. Mention zero-weight documents explicitly flagged.'),
('Clustering and evolution','Discover similar articles over time',['K-means on topic distributions','Monthly mean topic weights','Report missing dates and insufficient periods'],'Show the Research Lab chart and explain why one month cannot establish a trend. Use dated approved inputs for meaningful evolution.'),
('Sentiment and entities','Source-linked contextual analytics',['Lexical tone aggregated by scoring method','Named entities or marked candidate fallback','Co-mention edges with source IDs'],'Distinguish sentiment from political bias and co-mention from causality. Show a source record and its digest.'),
('Language understanding','Summaries, enhancement and search',['MMR: relevance minus redundancy','FLAN-T5 drafts + extractive reference','Visible domain query expansion'],'Show an actual FLAN-T5 draft and compare it to the extractive reference. Model output is not a verified fact; lexical overlap is not factuality. Explain MMR and visible query expansion.'),
('Learned semantic retrieval','Real multilingual MiniLM',['384-dimensional pretrained embeddings','Neural MRR@3 0.75; lexical 0.625','Four selected fictional probes'],'Open the verified embedding JSON. Explain cosine similarity and the small selected benchmark limitation.'),
('Translation and coverage','Language is not culture',['Three real Argos ES-to-EN translations','Language filter and coverage comparison','Human review of regional interpretation'],'Read the actual translation evidence. Explain that this demonstrates inference, not translation accuracy across languages.'),
('Conversational intelligence','Multi-intent, context and provenance',['Cited extracts and bounded follow-up','Category / tone / date / preference filters','Abstention and downloadable JSON'],'Demonstrate a multi-part query and an unrelated query. Explain the difference between source grounding and factual verification.'),
('Web demo','Five integrated workflows',['Command Center / Article Lab','Search & Languages / Grounded Chat','Research Lab / batch export'],'Open the verified screenshots, then use the live local application. Use an approved real dataset if available; label the fictional corpus.'),
('Experimental evaluation','Do not conflate datasets',['Historical BBC accuracy 96.18%','Real BBC CV: 90.8% accuracy / 0.9079 F1','Synthetic paired CV: 0.5371 → 0.6143'],'Explain out-of-fold prediction and why the 30-record results cannot support production accuracy. Discuss class-specific weaknesses.'),
('Quality and reproducibility','Evidence, tests and tutorial notebooks',['Fresh-kernel notebook execution','Browser tests and real model inference','Seven executed tutorials; 33 tests passed'],'Open the latest completed run. Only state the actual passing test count and statuses shown in logs.'),
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
    def panel(x,y,w,h,fill='20394D'):
        sh=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
        sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(fill);sh.line.fill.background()
        return sh
    if i==3:
        for j,(a,desc) in enumerate([('01  INGEST','Validated records + provenance'),('02  ANALYZE','Classification, LDA/NMF, tone'),('03  RETRIEVE','TF-IDF / LSA / MiniLM'),('04  DELIVER','Cited chat, UI, API, exports')]):
            x=.65+j*3.12;panel(x,3.05,2.93,2.55)
            tx(slide,x+.12,3.35,2.68,.55,a,16,'59D1C6',True)
            tx(slide,x+.12,4.1,2.68,1.1,desc,19,'FFFFFF')
    elif i==13:
        shot=ROOT/'evidence'/'screenshots'/'05-research-lab.png'
        if shot.exists():
            from PIL import Image as PILImage
            with PILImage.open(shot) as im:
                w,h=im.size
            ww=min(6.5,3.65*w/h)
            slide.shapes.add_picture(str(shot),Inches(6.1+(6.5-ww)/2),Inches(2.88),width=Inches(ww))
        for j,item in enumerate(items):
            tx(slide,.72,3.12+j*.92,5.3,.86,'•  '+item,19,'FFFFFF')
        tx(slide,.72,6.02,5.2,.46,'Actual Chromium capture · verified prior run',12,'59D1C6')
    elif i==14:
        vals=[('Historical BBC holdout',.9605),('Final BBC 3-fold CV',.9079),('Synthetic word baseline',.5371),('Synthetic pivot + char',.6143)]
        for j,(label,v) in enumerate(vals):
            y=2.92+j*.76
            tx(slide,.68,y,4.35,.52,label,17,'FFFFFF')
            panel(5.0,y+.04,6.1,.35,'29465B')
            panel(5.0,y+.04,6.1*v,.35,'59D1C6' if j==1 else '7392AA')
            tx(slide,11.23,y-.04,1.4,.5,f'{v:.4f}',16,'FFFFFF',True)
        tx(slide,.68,6.13,12,.36,'Macro-F1 · different datasets and protocols; not a head-to-head comparison.',12,'B2C4D6')
    elif i==16:
        for j,(label,value,detail) in enumerate([('RECOVERED TIME','192 h','per year, assumed'),('NET VALUE','$3,360','illustrative first year'),('ROI','140%','not observed savings')]):
            x=.7+j*4.16;panel(x,3.0,3.95,2.7)
            tx(slide,x+.15,3.25,3.65,.5,label,15,'B2C4D6',True)
            tx(slide,x+.15,3.95,3.65,.8,value,32,'59D1C6',True)
            tx(slide,x+.15,4.85,3.65,.5,detail,16,'FFFFFF')
    elif i==6:
        for j,(label,desc) in enumerate([('LDA','Count vectors → probabilistic topic mixture'),('NMF','TF-IDF → nonnegative factorization')]):
            x=.72+j*6.22;panel(x,3.05,5.85,2.7)
            tx(slide,x+.2,3.35,5.4,.65,label,27,'59D1C6',True)
            tx(slide,x+.2,4.22,5.4,1.05,desc,21,'FFFFFF')
    else:
        for j,item in enumerate(items):
            panel(.72,3.0+j*.91,11.88,.75)
            tx(slide,.9,3.08+j*.91,11.45,.62,item,22,'FFFFFF')
    tx(slide,.55,6.87,11,.35,STUDENT+'   |   November 2026',12,'A1B2C6')
    tx(slide,12.15,6.87,.7,.35,f'{i:02d}',12,'59D1C6',True)
    slide.notes_slide.notes_text_frame.text=note
p4=OUT/'presentation.pptx';prs.save(p4)
# Preserve prior journal and explicitly distinguish the new three-page draft.
old=SUB/'FP_ReflectiveJournal_JoseGroup_ITAI2373.pdf'
archive=SUB/'Reflective_Journal_Original_Reading_Copy_5pages.pdf'
if old.exists() and not archive.exists():shutil.copy2(old,archive)
for src,dst in [(p1,'FP_TechnicalDoc_'+NAME+'.pdf'),(p2,'FP_ExecutiveSummary_'+NAME+'.pdf'),(p3,'FP_ReflectiveJournal_JoseGroup_ITAI2373.pdf'),(p4,'FP_Presentation_'+NAME+'.pptx')]:shutil.copy2(src,SUB/dst)
link_pages=[('Individual portfolio submission',[
('Required individual portfolio folder','https://github.com/jtuozzo1616/Jose-Tuozzo-AI-Portfolio/tree/main/ITAI2373-NewsBot-Final'),
('Canonical project repository',URL),
('Executed notebooks and model evidence',URL+'/tree/main/final-newsbot-2.0/evidence'),
('Detailed grading crosswalk',URL+'/blob/main/final-newsbot-2.0/docs/CANVAS_VERIFICATION.md'),
('Verified real-data and test run',URL+'/actions/runs/45691589156'),
('Presentation and documents',URL+'/tree/main/final-newsbot-2.0/submission')])]
link=pdf('github_submission_links.pdf','GitHub submission links',link_pages)
shutil.copy2(link,SUB/'FP_GitHub_Links_ITAI2373.pdf')
from pypdf import PdfReader
assert len(PdfReader(p3).pages)==3
assert len(prs.slides)==18 and all(s.notes_slide.notes_text_frame.text.strip() for s in prs.slides)
print('RUBRIC DOCUMENTS VERIFIED',len(PdfReader(p1).pages),len(PdfReader(p2).pages),len(PdfReader(p3).pages),len(prs.slides))
