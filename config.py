import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenRouter Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    EMBEDDING_MODEL = "text-embedding-3-small"
    LLM_MODEL = "meta-llama/llama-3-8b-instruct"
    FAISS_INDEX_PATH = "faiss_index"
    TEMPERATURE = 0.3
    MAX_CHUNK_SIZE = 1500
    CHUNK_OVERLAP = 200
    
    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_TTL = int(os.getenv("REDIS_TTL", 3600))