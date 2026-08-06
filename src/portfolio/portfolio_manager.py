"""Portfolio Manager — menghitung kondisi portfolio dari semua Position."""

from datetime import UTC, datetime
from uuid import uuid4

from config.constants import MAX_PORTFOLIO_EXPOSURE
from src.core.models.account import AccountSnapshot
from src.core.models.portfolio import PortfolioSnapshot
from src.core.models.position import Position
from src.core.types.enums import PortfolioStatus, PositionStatus, RiskWarning
from src.market.in_memory_price_provider import InMemoryPriceProvider
from src.market.pnl_engine import calculate_unrealized


class PortfolioManager:
    def create_snapshot(
        self,
        positions: list[Position],
        account: AccountSnapshot,
        price_provider: InMemoryPriceProvider,
    ) -> PortfolioSnapshot:
        open_positions = [p for p in positions if p.status == PositionStatus.OPEN]
        closed_positions = [p for p in positions if p.status != PositionStatus.OPEN]
        long_positions = [p for p in open_positions if p.side == "LONG"]
        short_positions = [p for p in open_positions if p.side == "SHORT"]

        gross_exposure = sum(p.position_size for p in open_positions)
        net_exposure = sum(p.position_size for p in long_positions) - sum(
            p.position_size for p in short_positions
        )

        realized_pnl = 0.0  # placeholder
        unrealized_pnl = calculate_unrealized(positions, price_provider)
        equity = account.balance + realized_pnl + unrealized_pnl

        warnings: list[RiskWarning] = []
        if gross_exposure > MAX_PORTFOLIO_EXPOSURE:
            warnings.append(RiskWarning.POSITION_SIZE_CAPPED)

        if len(open_positions) == 0:
            status = PortfolioStatus.EMPTY
        elif gross_exposure > MAX_PORTFOLIO_EXPOSURE:
            status = PortfolioStatus.RISK_LIMIT
        else:
            status = PortfolioStatus.ACTIVE

        return PortfolioSnapshot(
            snapshot_id=uuid4(),
            timestamp=datetime.now(UTC),
            status=status,
            total_positions=len(positions),
            open_positions=len(open_positions),
            closed_positions=len(closed_positions),
            long_positions=len(long_positions),
            short_positions=len(short_positions),
            net_exposure=net_exposure,
            gross_exposure=gross_exposure,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            equity=equity,
            warnings=warnings,
        )