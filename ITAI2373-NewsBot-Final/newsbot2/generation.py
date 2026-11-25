"""Opt-in pretrained text generation. Drafts are not source-verified facts."""
from functools import lru_cache
from .analysis import summarize
from .language import tokens
MODEL='google/flan-t5-small'

@lru_cache(maxsize=1)
def load_generator():
    """Load real pretrained sequence-to-sequence weights only on explicit request."""
    from transformers import AutoTokenizer,AutoModelForSeq2SeqLM
    tok=AutoTokenizer.from_pretrained(MODEL)
    model=AutoModelForSeq2SeqLM.from_pretrained(MODEL)
    model.eval()
    return tok,model

def generate_brief(article):
    """Create a neural draft and retain extractive reference and source ID."""
    try:
        tok,model=load_generator()
        import torch
        prompt='Summarize this news article in one sentence. Use only information from the article: '+article.full_text
        batch=tok(prompt,return_tensors='pt',truncation=True,max_length=512)
        with torch.inference_mode():
            ids=model.generate(**batch,max_new_tokens=64,num_beams=4,do_sample=False)
        output=tok.decode(ids[0],skip_special_tokens=True).strip()
        if not output:raise RuntimeError('empty model output')
        source=set(tokens(article.full_text));draft=set(tokens(output))
        overlap=round(len(source&draft)/max(len(draft),1),4)
        return {'status':'ok','model':MODEL,'draft':output,'source_id':article.article_id,'source_sha256':article.sha256,'synthetic':article.synthetic,'extractive_reference':summarize(article.body)['text'],'draft_vocabulary_overlap':overlap,'warning':'Unverified neural editorial draft. Lexical overlap is not factuality; verify names, numbers and claims against the source.'}
    except (ImportError,OSError,RuntimeError,ValueError) as e:
        return {'status':'unavailable','model':MODEL,'reason':type(e).__name__,'extractive_reference':summarize(article.body)['text'],'source_id':article.article_id}
