"""Turso-backed SignalLifecycle Repository — atomic via client.batch()."""

from datetime import UTC, datetime
from uuid import UUID

from loguru import logger

from config.settings import settings
from src.core.models.lifecycle_lookup import (
    LifecycleLookupResult,
    LifecycleRecord,
)
from src.core.models.signal_lifecycle import SignalLifecycle
from src.core.types.enums import (
    SignalLifecycleExpireReason,
    SignalLifecycleStatus,
)
from src.notification.recipient_config import parse_recipient_ids
from src.storage.adapters.turso_client import TursoClient
from src.storage.repositories.signal_lifecycle_repository import (
    SignalLifecycleRepository,
)


class TursoSignalLifecycleRepository(SignalLifecycleRepository):
    def __init__(
        self,
        client: TursoClient,
        outbox_enabled: bool | None = None,
        recipient_ids: list[str] | None = None,
    ) -> None:
        self.client = client
        if outbox_enabled is None:
            outbox_enabled = getattr(settings, "NOTIFICATION_OUTBOX_ENABLED", False)
        if recipient_ids is None:
            recipient_ids = parse_recipient_ids(
                getattr(settings, "NOTIFICATION_RECIPIENT_IDS", "")
            )
        self.outbox_enabled = outbox_enabled
        self.recipient_ids = recipient_ids

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
        """Atomic supersede.

        Flag OFF: 2 statements (UPDATE old + INSERT new). superseded_by still populated.
        Flag ON:  4 statements (INSERT REPLACEMENT via SELECT + UPDATE old + INSERT new
                  + INSERT NEW_SIGNAL multi-row VALUES ON CONFLICT DO NOTHING).
        """
        supersede_terminal_at = new_lifecycle.created_at.isoformat()
        outbox_ts = new_lifecycle.created_at.isoformat()

        # Statement 1 (only if outbox enabled AND recipients configured):
        #   reads-before-writes REPLACEMENT via INSERT...SELECT from old NEW_SIGNAL
        statements = []

        if self.outbox_enabled and self.recipient_ids:
            # Use original outbox_id prefix → ensures per-row unique PK
            # (single `?` would give same uuid to ALL selected rows → PK conflict)
            repl_select = (
                "INSERT INTO notification_outbox "
                "(signal_id, event_type, telegram_id, status, attempts, "
                " created_at, updated_at) "
                "SELECT o.signal_id, 'REPLACEMENT', o.telegram_id, "
                "       'PENDING', 0, ?, ? "
                "FROM notification_outbox o "
                "WHERE o.event_type='NEW_SIGNAL' "
                "  AND o.signal_id=(SELECT signal_id FROM signal_lifecycle "
                "                   WHERE symbol=? AND status='ACTIVE' LIMIT 1) "
                "ON CONFLICT(signal_id, event_type, telegram_id) DO NOTHING",
                [outbox_ts, outbox_ts, new_lifecycle.symbol],
            )
            statements.append(repl_select)

        # Statement (N): UPDATE old lifecycle
        statements.append((
            "UPDATE signal_lifecycle "
            "SET status = ?, expire_reason = ?, terminal_at = ?, "
            "    superseded_by_signal_id = ? "
            "WHERE symbol = ? AND status = ? AND signal_id != ?",
            [
                SignalLifecycleStatus.EXPIRED.value,
                SignalLifecycleExpireReason.SUPERSEDED.value,
                supersede_terminal_at,
                str(new_lifecycle.signal_id),
                new_lifecycle.symbol,
                SignalLifecycleStatus.ACTIVE.value,
                str(new_lifecycle.signal_id),
            ],
        ))

        # Statement (N+1): INSERT new lifecycle
        statements.append((
            "INSERT INTO signal_lifecycle ("
            "signal_id, symbol, status, expire_reason, "
            "created_at, expires_at, zone_low, zone_high, terminal_at, "
            "superseded_by_signal_id"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                str(new_lifecycle.signal_id),
                new_lifecycle.symbol,
                new_lifecycle.status.value,
                new_lifecycle.expire_reason.value if new_lifecycle.expire_reason else None,
                new_lifecycle.created_at.isoformat(),
                new_lifecycle.expires_at.isoformat(),
                new_lifecycle.zone_low,
                new_lifecycle.zone_high,
                new_lifecycle.terminal_at.isoformat() if new_lifecycle.terminal_at else None,
                str(new_lifecycle.superseded_by_signal_id) if new_lifecycle.superseded_by_signal_id else None,
            ],
        ))

        # Statement (N+2, only if outbox enabled AND recipients):
        #   NEW_SIGNAL multi-row VALUES ON CONFLICT DO NOTHING
        if self.outbox_enabled and self.recipient_ids:
            values_ph = ",".join(
                ["(?, 'NEW_SIGNAL', ?, 'PENDING', 0, ?, ?)"]
                * len(self.recipient_ids)
            )
            params: list = []
            for rid in self.recipient_ids:
                params.extend(
                    [str(new_lifecycle.signal_id), int(rid), outbox_ts, outbox_ts]
                )
            statements.append((
                "INSERT INTO notification_outbox "
                "(signal_id, event_type, telegram_id, status, attempts, "
                " created_at, updated_at) "
                f"VALUES {values_ph} "
                "ON CONFLICT(signal_id, event_type, telegram_id) DO NOTHING",
                params,
            ))

        try:
            self.client.batch(statements)
            logger.debug(
                f"Lifecycle created with supersede: {new_lifecycle.signal_id} "
                f"(statements={len(statements)}, outbox={self.outbox_enabled})"
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
        """Mark EXPIRED.

        TIME reason + flag ON + recipients: 2 statements (INSERT EXPIRY via SELECT + UPDATE).
        Otherwise: 1 statement (UPDATE only).
        """
        terminal_ts = datetime.now(UTC).isoformat()

        # Only TIME expiry enqueues. SUPERSEDED is enqueued by create_with_supersede.
        if (
            reason == SignalLifecycleExpireReason.TIME
            and self.outbox_enabled
            and self.recipient_ids
        ):
            statements = [
                (
                    "INSERT INTO notification_outbox "
                    "(signal_id, event_type, telegram_id, status, attempts, "
                    " created_at, updated_at) "
                    "SELECT o.signal_id, 'EXPIRY', o.telegram_id, "
                    "       'PENDING', 0, ?, ? "
                    "FROM notification_outbox o "
                    "WHERE o.event_type='NEW_SIGNAL' "
                    "  AND o.signal_id=? "
                    "  AND EXISTS (SELECT 1 FROM signal_lifecycle lc "
                    "              WHERE lc.signal_id=o.signal_id AND lc.status='ACTIVE') "
                    "ON CONFLICT(signal_id, event_type, telegram_id) DO NOTHING",
                    [terminal_ts, terminal_ts, str(signal_id)],
                ),
                (
                    "UPDATE signal_lifecycle "
                    "SET status = ?, expire_reason = ?, terminal_at = ? "
                    "WHERE signal_id = ? AND status = ?",
                    [
                        SignalLifecycleStatus.EXPIRED.value,
                        reason.value,
                        terminal_ts,
                        str(signal_id),
                        SignalLifecycleStatus.ACTIVE.value,
                    ],
                ),
            ]
            try:
                self.client.batch(statements)
                logger.debug(
                    f"Lifecycle marked expired (TIME+outbox): {signal_id}"
                )
            except Exception as e:
                logger.error(f"mark_expired (TIME+outbox) failed for {signal_id}: {e}")
                raise
        else:
            # Original single-statement path
            sql = (
                "UPDATE signal_lifecycle "
                "SET status = ?, expire_reason = ?, terminal_at = ? "
                "WHERE signal_id = ? AND status = ?"
            )
            params = [
                SignalLifecycleStatus.EXPIRED.value,
                reason.value,
                terminal_ts,
                str(signal_id),
                SignalLifecycleStatus.ACTIVE.value,
            ]
            try:
                self.client.execute(sql, params)
                logger.debug(
                    f"Lifecycle marked expired: {signal_id} ({reason.value})"
                )
            except Exception as e:
                logger.error(f"mark_expired failed for {signal_id}: {e}")
                raise

    _LIFECYCLE_CHUNK_SIZE = 500

    def get_lifecycle_lookup(
        self, signal_ids: list[UUID]
    ) -> LifecycleLookupResult:
        if not signal_ids:
            return LifecycleLookupResult()

        unique_ids = list(dict.fromkeys(signal_ids))

        found: dict[UUID, LifecycleRecord] = {}
        absent: set[UUID] = set()
        failed: set[UUID] = set()

        for i in range(0, len(unique_ids), self._LIFECYCLE_CHUNK_SIZE):
            chunk = unique_ids[i : i + self._LIFECYCLE_CHUNK_SIZE]
            try:
                placeholders = ",".join(["?"] * len(chunk))
                sql = (
                    f"SELECT signal_id, status, expires_at FROM signal_lifecycle "
                    f"WHERE signal_id IN ({placeholders})"
                )
                result = self.client.execute(sql, [str(sid) for sid in chunk])
            except Exception as e:
                logger.warning(
                    f"[lifecycle_lookup] chunk failed for {len(chunk)} ids: {e}"
                )
                for sid in chunk:
                    failed.add(sid)
                continue

            chunk_found: set[UUID] = set()
            chunk_ambiguous = False
            per_row_failed: set[UUID] = set()

            for row in result.rows:
                raw_id = row[0] if len(row) > 0 else None
                sid: UUID | None = None
                try:
                    sid = UUID(raw_id)
                except Exception as e:
                    logger.error(
                        f"[lifecycle_lookup] cannot parse signal_id "
                        f"from row: {raw_id!r} — chunk marked ambiguous ({e})"
                    )
                    chunk_ambiguous = True
                    continue

                try:
                    status = row[1]
                    expires_at = None
                    if len(row) > 2 and row[2] is not None:
                        expires_at = datetime.fromisoformat(row[2])
                    # R6: reject unknown status before adding to found
                    if status not in ("ACTIVE", "EXPIRED"):
                        logger.error(
                            f"[lifecycle_lookup] invalid lifecycle status "
                            f"'{status}' for {sid} — treating as failed"
                        )
                        per_row_failed.add(sid)
                        continue
                    # B1: ACTIVE rows must have a valid expires_at
                    if status == "ACTIVE" and expires_at is None:
                        logger.error(
                            f"[lifecycle_lookup] ACTIVE row for {sid} "
                            f"missing expires_at — treating as failed"
                        )
                        per_row_failed.add(sid)
                        continue
                    found[sid] = LifecycleRecord(sid, status, expires_at)
                    chunk_found.add(sid)
                except Exception as e:
                    logger.error(
                        f"[lifecycle_lookup] failed to parse row for "
                        f"{sid}: {e}"
                    )
                    per_row_failed.add(sid)

            # R5: chunk_ambiguous overrides everything in this chunk
            if chunk_ambiguous:
                for sid in chunk:
                    failed.add(sid)
                    found.pop(sid, None)
            else:
                for sid in chunk:
                    # R8: failed wins over found/absent for same id
                    if sid in per_row_failed:
                        failed.add(sid)
                        found.pop(sid, None)
                        continue
                    if sid in chunk_found:
                        continue
                    absent.add(sid)

        # R8: final guarantee — each id in exactly one bucket
        for sid in failed:
            found.pop(sid, None)
            absent.discard(sid)

        return LifecycleLookupResult(found=found, absent=absent, failed=failed)

    # ---------- helpers ----------

    def _row_to_lifecycle(self, row: dict) -> SignalLifecycle:
        expire_reason = row.get("expire_reason")
        superseded_by = row.get("superseded_by_signal_id")
        return SignalLifecycle(
            signal_id=UUID(row["signal_id"]),
            symbol=row["symbol"],
            status=SignalLifecycleStatus(row["status"]),
            expire_reason=(
                SignalLifecycleExpireReason(expire_reason) if expire_reason else None
            ),
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            zone_low=float(row["zone_low"]),
            zone_high=float(row["zone_high"]),
            terminal_at=(
                datetime.fromisoformat(row["terminal_at"]) if row.get("terminal_at") else None
            ),
            superseded_by_signal_id=UUID(superseded_by) if superseded_by else None,
        )