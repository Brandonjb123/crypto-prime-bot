"""Turso/libSQL client wrapper — sync connection untuk repository."""

import libsql_client
from loguru import logger


class TursoClient:
    """Wrapper untuk libsql_client.SyncClient.

    Menyediakan interface sederhana: connect(), execute(), close().
    Tidak async karena repository interface saat ini sync.
    """

    def __init__(self, url: str, auth_token: str) -> None:
        self.url = url
        self.auth_token = auth_token
        self._client = None

    def connect(self) -> None:
        """Buka koneksi ke Turso. Raise on failure — jangan fallback."""
        if self._client is not None:
            return

        try:
            self._client = libsql_client.create_client_sync(
                url=self.url,
                auth_token=self.auth_token,
            )
            # Verifikasi koneksi
            self._client.execute("SELECT 1")
            logger.info("Turso connection established")
        except Exception as e:
            logger.error(f"Turso connection failed: {e}")
            raise RuntimeError(f"Cannot connect to Turso: {e}") from e

    def execute(self, sql: str, params: list | None = None):
        """Execute SQL. Return ResultSet dari libsql_client."""
        if self._client is None:
            raise RuntimeError("TursoClient not connected. Call connect() first.")
        return self._client.execute(sql, params or [])

    def batch(self, stmts: list):
        """Execute multiple statements atomically via libsql_client.batch().

        Delegates ke underlying SyncClient.batch() yang wrap BEGIN/COMMIT/
        ROLLBACK secara atomic di server (verified C0.0.1 blocker resolution).
        """
        if self._client is None:
            raise RuntimeError("TursoClient not connected. Call connect() first.")
        return self._client.batch(stmts)

    def close(self) -> None:
        """Tutup koneksi."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception as e:
                logger.warning(f"Error closing Turso client: {e}")
            finally:
                self._client = None