import time
from typing import Any, Optional


class SimpleCache:
    """In-memory cache dengan TTL sederhana."""

    def __init__(self, default_ttl: int = 60):
        self._cache: dict[str, tuple[float, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Ambil nilai dari cache. Return None jika expired atau tidak ada."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        expiry, value = entry
        if time.time() > expiry:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Simpan nilai ke cache dengan TTL tertentu."""
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + ttl
        self._cache[key] = (expiry, value)

    def delete(self, key: str) -> None:
        """Hapus key dari cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Hapus semua cache."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Jumlah item dalam cache."""
        return len(self._cache)