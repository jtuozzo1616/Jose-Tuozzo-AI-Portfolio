"""Public runtime configuration; no secrets."""
import os
MAX_FILE_BYTES=8_000_000
MAX_ARTICLES=3000
MAX_QUERY_CHARS=1000
RANDOM_SEED=42
DEMO_ONLY=os.getenv('NEWSBOT_DEMO_ONLY','0')=='1'
ENABLE_NEURAL=os.getenv('NEWSBOT_ENABLE_NEURAL','0')=='1'
EMBEDDING_MODEL='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
