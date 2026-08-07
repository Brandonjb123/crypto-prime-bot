"""Base Repository interface — generic CRUD."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class BaseRepository(ABC):
    @abstractmethod
    def save(self, obj: Any) -> None:
        """Simpan object (insert atau update jika ID sudah ada)."""
        ...

    @abstractmethod
    def get_by_id(self, obj_id: UUID) -> Any | None:
        """Ambil object berdasarkan ID."""
        ...

    @abstractmethod
    def get_all(self) -> list:
        """Ambil semua object."""
        ...

    @abstractmethod
    def delete(self, obj_id: UUID) -> None:
        """Hapus object berdasarkan ID."""
        ...

    @abstractmethod
    def exists(self, obj_id: UUID) -> bool:
        """Cek apakah object dengan ID tertentu ada."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Jumlah object yang tersimpan."""
        ...
