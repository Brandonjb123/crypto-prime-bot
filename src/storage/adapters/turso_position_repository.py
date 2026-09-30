"""Turso-backed Position Repository — upsert by position_id."""

from datetime import datetime
from uuid import UUID

from loguru import logger

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.storage.adapters.turso_client import TursoClient
from src.storage.repositories.position_repository import PositionRepository


class TursoPositionRepository(PositionRepository):
    def __init__(self, client: TursoClient) -> None:
        self.client = client

    # ---------- write ----------

    def save(self, position: Position) -> None:
        """UPSERT berdasarkan position_id — satu row per lifecycle."""
        sql = """
        INSERT INTO positions (
            position_id, execution_id, order_id, signal_id,
            symbol, side, status,
            entry_price, stop_loss, take_profit, tp1_price, tp2_price,
            position_size, opened_at, closed_at, close_reason,
            last_price, last_updated, realized_pnl
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(position_id) DO UPDATE SET
            status = excluded.status,
            close_reason = excluded.close_reason,
            closed_at = excluded.closed_at,
            last_price = excluded.last_price,
            last_updated = excluded.last_updated,
            realized_pnl = excluded.realized_pnl,
            position_size = excluded.position_size
        """
        params = [
            str(position.position_id),
            str(position.execution_id),
            str(position.order_id),
            str(position.signal_id) if position.signal_id else None,
            position.symbol,
            self._enum_value(position.side),
            self._enum_value(position.status),
            position.entry_price,
            position.stop_loss,
            position.take_profit,
            position.tp1_price,
            position.tp2_price,
            position.position_size,
            self._dt_to_str(position.opened_at),
            self._dt_to_str(position.closed_at),
            self._enum_value(position.close_reason),
            position.last_price,
            self._dt_to_str(position.last_updated),
            position.realized_pnl,
        ]
        self.client.execute(sql, params)
        logger.debug(f"Position persisted: {position.position_id}")

    # ---------- read ----------

    def get_open(self) -> list[Position]:
        sql = "SELECT * FROM positions WHERE status = ? ORDER BY opened_at DESC"
        return self._query(sql, [PositionStatus.OPEN.value])

    def get_closed(self) -> list[Position]:
        sql = "SELECT * FROM positions WHERE status != ? ORDER BY closed_at DESC"
        return self._query(sql, [PositionStatus.OPEN.value])

    def get_by_id(self, position_id: UUID) -> Position | None:
        sql = "SELECT * FROM positions WHERE position_id = ? LIMIT 1"
        rows = self._query(sql, [str(position_id)])
        return rows[0] if rows else None

    def get_all(self) -> list[Position]:
        sql = "SELECT * FROM positions ORDER BY opened_at DESC"
        return self._query(sql, [])

    def delete(self, position_id: UUID) -> None:
        self.client.execute(
            "DELETE FROM positions WHERE position_id = ?",
            [str(position_id)],
        )

    def exists(self, position_id: UUID) -> bool:
        result = self.client.execute(
            "SELECT 1 FROM positions WHERE position_id = ? LIMIT 1",
            [str(position_id)],
        )
        return len(result.rows) > 0

    def count(self) -> int:
        result = self.client.execute("SELECT COUNT(*) FROM positions", [])
        return int(result.rows[0][0]) if result.rows else 0

    # ---------- helpers ----------

    def _query(self, sql: str, params: list) -> list[Position]:
        result = self.client.execute(sql, params)
        positions = []
        for row in result.rows:
            try:
                positions.append(self._row_to_position(dict(zip(result.columns, row, strict=False))))
            except Exception as e:
                logger.error(f"Failed to deserialize position row: {e}, row={row}")
        return positions

    def _row_to_position(self, row: dict) -> Position:
        return Position(
            position_id=UUID(row["position_id"]),
            execution_id=UUID(row["execution_id"]),
            order_id=UUID(row["order_id"]),
            signal_id=UUID(row["signal_id"]) if row.get("signal_id") else None,
            symbol=row["symbol"],
            side=Side(row["side"]),
            status=PositionStatus(row["status"]),
            entry_price=float(row["entry_price"]),
            stop_loss=float(row["stop_loss"]),
            take_profit=float(row["take_profit"]),
            tp1_price=float(row["tp1_price"]) if row.get("tp1_price") is not None else None,
            tp2_price=float(row["tp2_price"]) if row.get("tp2_price") is not None else None,
            position_size=float(row["position_size"]),
            opened_at=datetime.fromisoformat(row["opened_at"]),
            closed_at=datetime.fromisoformat(row["closed_at"]) if row.get("closed_at") else None,
            close_reason=PositionCloseReason(row["close_reason"]) if row.get("close_reason") else PositionCloseReason.NONE,
            last_price=float(row["last_price"]) if row.get("last_price") is not None else None,
            last_updated=datetime.fromisoformat(row["last_updated"]) if row.get("last_updated") else None,
            realized_pnl=float(row["realized_pnl"]) if row.get("realized_pnl") is not None else 0.0,
        )

    @staticmethod
    def _enum_value(v):
        return v.value if hasattr(v, "value") else v

    @staticmethod
    def _dt_to_str(dt) -> str | None:
        return dt.isoformat() if dt is not None else None