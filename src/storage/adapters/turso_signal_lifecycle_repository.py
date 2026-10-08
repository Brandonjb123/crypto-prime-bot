"""Turso-backed SignalLifecycle Repository — atomic via client.batch()."""

from datetime import UTC, datetime
from uuid import UUID

from loguru import logger

from src.core.models.signal_lifecycle import SignalLifecycle
from src.core.types.enums import (
    SignalLifecycleExpireReason,
    SignalLifecycleStatus,
)
from src.storage.adapters.turso_client import TursoClient
from src.storage.repositories.signal_lifecycle_repository import (
    SignalLifecycleRepository,
)


class TursoSignalLifecycleRepository(SignalLifecycleRepository):
    def __init__(self, client: TursoClient) -> None:
        self.client = client

    # ---------- read ----------

    def get_active_by_symbol(self, symbol: str) -> SignalLifecycle | None:
        sql = """
        SELECT * FROM signal_lifecycle
        WHERE symbol = ? AND status = ?
        LIMIT 1
        """
        result = self.client.execute(
            sql, [symbol, SignalLifecycleStatus.ACTIVE.value]
        )
        if not result.rows:
            return None
        row = dict(zip(result.columns, result.rows[0], strict=False))
        return self._row_to_lifecycle(row)

    def get_all_active(self) -> list[SignalLifecycle]:
        sql = """
        SELECT * FROM signal_lifecycle
        WHERE status = ?
        """
        result = self.client.execute(sql, [SignalLifecycleStatus.ACTIVE.value])
        lifecycles: list[SignalLifecycle] = []
        for row in result.rows:
            try:
                lifecycles.append(
                    self._row_to_lifecycle(
                        dict(zip(result.columns, row, strict=False))
                    )
                )
            except Exception as e:
                logger.error(f"Failed to deserialize lifecycle row: {e}, row={row}")
        return lifecycles

    # ---------- write ----------

    def create_with_supersede(
        self, new_lifecycle: SignalLifecycle
    ) -> SignalLifecycle:
        """Atomic: BEGIN → UPDATE old ACTIVE → INSERT new ACTIVE → COMMIT.

        Menggunakan client.batch() yang wrap BEGIN/COMMIT/ROLLBACK
        secara atomic di server (verified C0.0.1 blocker resolution).
        """
        supersede_terminal_at = new_lifecycle.created_at.isoformat()

        expire_old = (
            "UPDATE signal_lifecycle "
            "SET status = ?, expire_reason = ?, terminal_at = ? "
            "WHERE symbol = ? AND status = ? AND signal_id != ?",
            [
                SignalLifecycleStatus.EXPIRED.value,
                SignalLifecycleExpireReason.SUPERSEDED.value,
                supersede_terminal_at,
                new_lifecycle.symbol,
                SignalLifecycleStatus.ACTIVE.value,
                str(new_lifecycle.signal_id),
            ],
        )

        insert_new = (
            "INSERT INTO signal_lifecycle ("
            "signal_id, symbol, status, expire_reason, "
            "created_at, expires_at, zone_low, zone_high, terminal_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                str(new_lifecycle.signal_id),
                new_lifecycle.symbol,
                new_lifecycle.status.value,
                (
                    new_lifecycle.expire_reason.value
                    if new_lifecycle.expire_reason
                    else None
                ),
                new_lifecycle.created_at.isoformat(),
                new_lifecycle.expires_at.isoformat(),
                new_lifecycle.zone_low,
                new_lifecycle.zone_high,
                (
                    new_lifecycle.terminal_at.isoformat()
                    if new_lifecycle.terminal_at
                    else None
                ),
            ],
        )

        try:
            self.client.batch([expire_old, insert_new])
            logger.debug(
                f"Lifecycle created with supersede: {new_lifecycle.signal_id}"
            )
        except Exception as e:
            logger.error(
                f"create_with_supersede failed for {new_lifecycle.signal_id}: {e}"
            )
            raise

        return new_lifecycle

    def mark_expired(
        self, signal_id: UUID, reason: SignalLifecycleExpireReason
    ) -> None:
        sql = (
            "UPDATE signal_lifecycle "
            "SET status = ?, expire_reason = ?, terminal_at = ? "
            "WHERE signal_id = ? AND status = ?"
        )
        params = [
            SignalLifecycleStatus.EXPIRED.value,
            reason.value,
            datetime.now(UTC).isoformat(),
            str(signal_id),
            SignalLifecycleStatus.ACTIVE.value,
        ]
        try:
            self.client.execute(sql, params)
            logger.debug(f"Lifecycle marked expired: {signal_id} ({reason.value})")
        except Exception as e:
            logger.error(f"mark_expired failed for {signal_id}: {e}")
            raise

    # ---------- helpers ----------

    def _row_to_lifecycle(self, row: dict) -> SignalLifecycle:
        expire_reason = row.get("expire_reason")
        return SignalLifecycle(
            signal_id=UUID(row["signal_id"]),
            symbol=row["symbol"],
            status=SignalLifecycleStatus(row["status"]),
            expire_reason=(
                SignalLifecycleExpireReason(expire_reason)
                if expire_reason
                else None
            ),
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            zone_low=float(row["zone_low"]),
            zone_high=float(row["zone_high"]),
            terminal_at=(
                datetime.fromisoformat(row["terminal_at"])
                if row.get("terminal_at")
                else None
            ),
        )