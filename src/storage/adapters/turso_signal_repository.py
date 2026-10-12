"""Turso-backed Signal Repository — append-only."""

import json
from datetime import datetime
from uuid import UUID

from loguru import logger

from src.core.models.trading_signal import TradingSignal
from src.storage.adapters.turso_client import TursoClient
from src.storage.repositories.signal_repository import SignalRepository


class TursoSignalRepository(SignalRepository):
    def __init__(self, client: TursoClient) -> None:
        self.client = client

    # ---------- write ----------

    def append(self, signal: TradingSignal) -> None:
        """Append signal — never overwrite existing signal_id."""
        sql = """
        INSERT INTO trading_signals (
            signal_id, symbol, side, status,
            entry_price, stop_loss, take_profit, take_profit_1, take_profit_2,
            position_size, risk_percent, confidence, risk_level,
            reasoning, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            str(signal.signal_id),
            signal.symbol,
            signal.side,
            signal.status,
            signal.entry_price,
            signal.stop_loss,
            signal.take_profit,
            signal.take_profit_1,
            signal.take_profit_2,
            signal.position_size,
            signal.risk_percent,
            signal.confidence,
            signal.risk_level,
            json.dumps(signal.reasoning or []),
            signal.created_at.isoformat(),
        ]
        try:
            self.client.execute(sql, params)
            logger.debug(f"Signal appended: {signal.signal_id}")
        except Exception as e:
            # Append-only: signal_id adalah PK, duplicate akan raise
            logger.error(f"Signal append failed for {signal.signal_id}: {e}")
            raise

    # ---------- read ----------

    def latest_by_symbol(self, symbol: str) -> TradingSignal | None:
        sql = """
        SELECT * FROM trading_signals
        WHERE symbol = ?
        ORDER BY created_at DESC
        LIMIT 1
        """
        rows = self._query(sql, [symbol])
        return rows[0] if rows else None

    def history(
        self,
        symbol: str | None = None,
        since: datetime | None = None,
    ) -> list[TradingSignal]:
        conditions = []
        params: list = []
        if symbol is not None:
            conditions.append("symbol = ?")
            params.append(symbol)
        if since is not None:
            conditions.append("created_at >= ?")
            params.append(since.isoformat())

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM trading_signals {where} ORDER BY created_at DESC"
        return self._query(sql, params)

    def count(self) -> int:
        result = self.client.execute("SELECT COUNT(*) FROM trading_signals", [])
        return int(result.rows[0][0]) if result.rows else 0

    # ---------- helpers ----------

    def _query(self, sql: str, params: list) -> list[TradingSignal]:
        result = self.client.execute(sql, params)
        signals = []
        for row in result.rows:
            try:
                signals.append(self._row_to_signal(dict(zip(result.columns, row, strict=False))))
            except Exception as e:
                logger.error(f"Failed to deserialize signal row: {e}, row={row}")
        return signals

    def _row_to_signal(self, row: dict) -> TradingSignal:
        reasoning_raw = row.get("reasoning")
        if reasoning_raw:
            try:
                reasoning = json.loads(reasoning_raw)
            except (json.JSONDecodeError, TypeError):
                reasoning = []
        else:
            reasoning = []

        return TradingSignal(
            signal_id=UUID(row["signal_id"]),
            symbol=row["symbol"],
            side=row["side"],
            status=row["status"],
            entry_price=float(row["entry_price"]) if row.get("entry_price") is not None else None,
            stop_loss=float(row["stop_loss"]) if row.get("stop_loss") is not None else None,
            take_profit=float(row["take_profit"]) if row.get("take_profit") is not None else None,
            take_profit_1=float(row["take_profit_1"]) if row.get("take_profit_1") is not None else None,
            take_profit_2=float(row["take_profit_2"]) if row.get("take_profit_2") is not None else None,
            position_size=float(row["position_size"]) if row.get("position_size") is not None else 0.0,
            risk_percent=float(row["risk_percent"]) if row.get("risk_percent") is not None else 0.0,
            confidence=int(row["confidence"]) if row.get("confidence") is not None else 0,
            risk_level=row["risk_level"] or "MEDIUM",
            reasoning=reasoning,
            created_at=datetime.fromisoformat(row["created_at"]),
        )