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

class BroadcastCooldown:
    """Track pair yang sudah di-broadcast, dengan cooldown 8 jam."""
    def __init__(self, cooldown_seconds: int = 28800):
        self.cooldown = cooldown_seconds
        self._last_broadcast = {}  # {pair: timestamp}

    def is_on_cooldown(self, pair: str) -> bool:
        """Return True kalau pair masih dalam cooldown (belum 8 jam)."""
        last = self._last_broadcast.get(pair)
        if last is None:
            return False
        return (time.time() - last) < self.cooldown

    def mark_broadcasted(self, pair: str):
        """Catat bahwa pair baru saja di-broadcast."""
        self._last_broadcast[pair] = time.time()

    def reset(self, pair: str):
        """Reset cooldown untuk pair tertentu."""
        self._last_broadcast.pop(pair, None)

# Instance global yang dipakai di broadcaster:
broadcast_cooldown = BroadcastCooldown(cooldown_seconds=28800)        

price_cache = SimpleCache(ttl=300)   # 5 menit
news_cache = SimpleCache(ttl=600)    # 10 menit