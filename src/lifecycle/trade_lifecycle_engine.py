"""Trade Lifecycle Engine — evaluasi TP/SL untuk posisi OPEN."""


from src.core.models.position import Position
from src.core.types.enums import PositionStatus, Side


class TradeLifecycleEngine:
    """Evaluasi posisi OPEN terhadap harga saat ini.

    Return:
        action: "HOLD", "SL", "TP1", "TP2"
        fraction: fraksi posisi yang harus ditutup (1.0 untuk SL/TP2, 0.5 untuk TP1)
    """

    def evaluate(self, position: Position, current_price: float) -> tuple[str, float]:
        if position.status != PositionStatus.OPEN:
            return "HOLD", 0.0

        # Gunakan tp2_price jika tersedia, fallback ke take_profit lama
        tp2_price = position.tp2_price or position.take_profit
        tp1_price = position.tp1_price

        if position.side == Side.LONG:
            if current_price <= position.stop_loss:
                return "SL", 1.0
            if tp2_price and current_price >= tp2_price:
                return "TP2", 1.0
            if tp1_price and current_price >= tp1_price:
                return "TP1", 0.5
        else:  # SHORT
            if current_price >= position.stop_loss:
                return "SL", 1.0
            if tp2_price and current_price <= tp2_price:
                return "TP2", 1.0
            if tp1_price and current_price <= tp1_price:
                return "TP1", 0.5

        return "HOLD", 0.0