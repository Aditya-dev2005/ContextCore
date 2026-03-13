import redis
import json
import hashlib
from typing import Optional, Any
from config import Config

class CacheService:
    def __init__(self):
        self.client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True
        )
        self.ttl = Config.REDIS_TTL
    
    def _generate_key(self, question: str) -> str:
        """Generate cache key from question"""
        normalized = ' '.join(question.lower().split())
        return f"rag:q:{hashlib.md5(normalized.encode()).hexdigest()}"
    
    def get_cached_response(self, question: str) -> Optional[dict]:
        """Get cached response if exists"""
        key = self._generate_key(question)
        cached = self.client.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    def cache_response(self, question: str, response: dict):
        """Cache response with TTL"""
        key = self._generate_key(question)
        self.client.setex(key, self.ttl, json.dumps(response))
    
    def clear_cache(self, pattern: str = "rag:*"):
        """Clear cache (optional)"""
        for key in self.client.scan_iter(pattern):
            self.client.delete(key)