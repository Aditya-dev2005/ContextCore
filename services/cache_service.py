import redis
import json
import hashlib
from typing import Optional, Any
from config import Config

class CacheService:
    def __init__(self):
        self.client = None
        self.ttl = Config.REDIS_TTL
        try:
            self.client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                password=Config.REDIS_PASSWORD,
                db=Config.REDIS_DB,
                decode_responses=True,
                ssl=False,  # localhost ke liye SSL nahi chahiye
                socket_connect_timeout=2,  # 2 sec mein connect nahi hua toh skip
                socket_timeout=2
            )
            self.client.ping()
            print("✅ Redis connected!")
        except Exception as e:
            print(f"⚠️ Redis unavailable, caching disabled: {e}")
            self.client = None

    def _generate_key(self, question: str) -> str:
        normalized = ' '.join(question.lower().split())
        return f"rag:q:{hashlib.md5(normalized.encode()).hexdigest()}"

    def get_cached_response(self, question: str) -> Optional[dict]:
        if not self.client:
            return None
        try:
            key = self._generate_key(question)
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        return None

    def cache_response(self, question: str, response: dict):
        if not self.client:
            return
        try:
            key = self._generate_key(question)
            self.client.setex(key, self.ttl, json.dumps(response))
        except Exception:
            pass

    def clear_cache(self, pattern: str = "rag:*"):
        if not self.client:
            return
        try:
            for key in self.client.scan_iter(pattern):
                self.client.delete(key)
        except Exception:
            pass