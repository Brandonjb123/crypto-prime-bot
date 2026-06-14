# utils/cache.py
import time

class SimpleCache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self._store = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if entry:
            value, timestamp = entry
            if time.time() - timestamp < self.ttl:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value):
        self._store[key] = (value, time.time())

    def clear(self):
        self._store.clear()

price_cache = SimpleCache(ttl=300)   # 5 menit
news_cache = SimpleCache(ttl=600)    # 10 menit