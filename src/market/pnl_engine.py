"""PnL Engine — menghitung unrealized PnL dari posisi dan price provider."""


def calculate_unrealized(
    positions: list,
    provider,
) -> float:
    """
    Hitung total unrealized PnL dari semua posisi OPEN.

    LONG:  (current_price - entry_price) * size
    SHORT: (entry_price - current_price) * size
    Missing price → kontribusi 0.
    """
    from src.core.types.enums import PositionStatus, Side

    total_pnl = 0.0
    for pos in positions:
        if pos.status != PositionStatus.OPEN:
            continue

        current_price = provider.get_price(pos.symbol)
        if current_price is None:
            continue  # missing price → kontribusi 0

        if pos.side == Side.LONG:
            total_pnl += (current_price - pos.entry_price) * pos.position_size
        else:  # SHORT
            total_pnl += (pos.entry_price - current_price) * pos.position_size

    return total_pnl


def calculate_position_unrealized(position, provider) -> float | None:
    """Per-position unrealized PnL.

    Reuse formula sama dengan calculate_unrealized (LONG/SHORT semantics).
    Return None jika:
      - position bukan OPEN
      - current price unavailable
    Return 0.0 kalau PnL aktual nol.
    Tidak mutate state/repository. Tidak call Binance.
    """
    from src.core.types.enums import PositionStatus, Side

    if position.status != PositionStatus.OPEN:
        return None

    current_price = provider.get_price(position.symbol)
    if current_price is None:
        return None

    if position.side == Side.LONG:
        return (current_price - position.entry_price) * position.position_size
    else:  # SHORT
        return (position.entry_price - current_price) * position.position_size