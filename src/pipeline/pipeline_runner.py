"""Pipeline Runner — orchestration satu siklus analisis pasar."""

from datetime import UTC, datetime

from src.core.models.analysis_result import AnalysisResult as PipelineResult
from src.core.models.signal_lifecycle import SignalLifecycle
from src.core.types.enums import PipelineStatus, SignalLifecycleStatus
from src.logging.logger import get_logger
from src.signal.lifecycle_expiry_calculator import calculate_expires_at

logger = get_logger("pipeline.runner")

# === C0.0.2 — Zone calculation + RR validation ===

ZONE_HALF_WIDTH_ATR = 0.25
MIN_EFFECTIVE_RR = 2.5


def _calculate_zone_with_clipping(
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    atr: float,
    side: str,
) -> tuple[float, float, float | None]:
    """Calculate symmetric ±0.25 ATR entry zone with RR-based clipping.

    Returns (zone_low, zone_high, worst_rr).
    worst_rr is None if RR < MIN_EFFECTIVE_RR even after maximum clipping
    (degenerate → caller demotes to INVALID).

    LONG: unsafe side = zone_high (bayar tertinggi)
    SHORT: unsafe side = zone_low (jual terendah)
    """
    if atr <= 0:
        # No valid actionable zone without positive ATR.
        # Caller must demote signal to INVALID — no fallback zone.
        return None, None, None

    half = ZONE_HALF_WIDTH_ATR * atr
    zone_low = entry_price - half
    zone_high = entry_price + half

    if side == "BUY":
        risk = zone_high - stop_loss
        reward = take_profit - zone_high
    else:  # SELL
        risk = stop_loss - zone_low
        reward = zone_low - take_profit

    if risk <= 0 or reward <= 0:
        return zone_low, zone_high, None

    worst_rr = reward / risk
    if worst_rr >= MIN_EFFECTIVE_RR:
        return zone_low, zone_high, worst_rr

    # Clip unsafe side only, preserve safe side at ±0.25 ATR
    if side == "BUY":
        sl_dist = entry_price - stop_loss
        tp_dist = take_profit - entry_price
    else:  # SELL
        sl_dist = stop_loss - entry_price
        tp_dist = entry_price - take_profit

    d_max = (tp_dist - MIN_EFFECTIVE_RR * sl_dist) / (1 + MIN_EFFECTIVE_RR)
    if d_max < 0:
        return zone_low, zone_high, None

    d_clipped = min(half, d_max)

    if side == "BUY":
        zone_high = entry_price + d_clipped
        risk = zone_high - stop_loss
        reward = take_profit - zone_high
    else:  # SELL
        zone_low = entry_price - d_clipped
        risk = stop_loss - zone_low
        reward = zone_low - take_profit

    if risk <= 0 or reward <= 0:
        return zone_low, zone_high, None

    worst_rr = reward / risk
    if worst_rr < MIN_EFFECTIVE_RR:
        return zone_low, zone_high, None

    return zone_low, zone_high, worst_rr

class PipelineRunner:
    def __init__(
        self,
        collector=None,
        indicator_engine=None,
        analysis_engine=None,
        decision_engine=None,
        validation_engine=None,
        risk_engine=None,
        signal_engine=None,
        notification_engine=None,
        paper_trading_engine=None,
        health_monitor=None,
        price_provider=None,
        lifecycle_engine=None,
        signal_repository=None,
        lifecycle_repository=None,
    ):
        self.collector = collector
        self.indicator_engine = indicator_engine
        self.analysis_engine = analysis_engine
        self.decision_engine = decision_engine
        self.validation_engine = validation_engine
        self.risk_engine = risk_engine
        self.signal_engine = signal_engine
        self.notification_engine = notification_engine
        self.paper_trading_engine = paper_trading_engine
        self.health_monitor = health_monitor
        self.price_provider = price_provider
        self.signal_repository = signal_repository
        self.lifecycle_repository = lifecycle_repository
        self.lifecycle_engine = lifecycle_engine

        # Runtime state untuk Telegram
        self.last_pipeline_status = "IDLE"
        self.last_pipeline_started_at: datetime | None = None
        self.last_pipeline_completed_at: datetime | None = None
        self.last_pipeline_error: str | None = None
        self.last_market_snapshot = None

    async def run(self, symbol: str, timeframe: str = "4h") -> PipelineResult:
        logger.info(f"Pipeline started for {symbol} ({timeframe})")

        # Update status
        self.last_pipeline_status = "RUNNING"
        self.last_pipeline_started_at = datetime.now(UTC)
        self._record_pipeline_status(PipelineStatus.RUNNING)

        signal = None

        # Step 1 — Collect
        try:
            logger.info("Collecting market data...")
            if self.collector:
                snapshot = await self.collector.collect(symbol, timeframe)
                self.last_market_snapshot = snapshot
    
                if self.price_provider and snapshot:
                    self.price_provider.update_price(symbol, snapshot.current_price)
                logger.info("MarketSnapshot created")
                if self.lifecycle_engine and snapshot:
                    await self._evaluate_positions(symbol, snapshot.current_price)
            else:
                snapshot = None
        except Exception as e:
            logger.error(f"Collector failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 2 — Indicators
        try:
            if self.indicator_engine and snapshot:
                logger.info("Calculating indicators...")
                indicators = self.indicator_engine.calculate(snapshot)
                logger.info("IndicatorResult created")
            else:
                indicators = None
        except Exception as e:
            logger.error(f"Indicator calculation failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 3 — Analysis
        try:
            if self.analysis_engine and indicators:
                logger.info("Running market analysis...")
                analysis = self.analysis_engine.analyze(indicators)
                logger.info("AnalysisResult created")
            else:
                analysis = None
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 4 — AI Decision
        try:
            if self.decision_engine and analysis:
                logger.info("Running AI decision...")
                decision = await self.decision_engine.decide(analysis)
                logger.info("DecisionResult created")
            else:
                decision = None
        except Exception as e:
            logger.error(f"AI decision failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 5 — Validation
        try:
            if self.validation_engine and decision:
                logger.info("Running validation...")
                validated = self.validation_engine.validate(decision)
                logger.info("Validation complete")
            else:
                validated = None
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 6 — Risk
        try:
            if self.risk_engine and validated and indicators:
                logger.info("Running risk calculation...")
                entry = snapshot.current_price if snapshot else 0
                atr = indicators.atr14 or 0
                trade_plan = self.risk_engine.calculate(validated, entry, atr)
                logger.info("TradePlan created")
            else:
                trade_plan = None
        except Exception as e:
            logger.error(f"Risk calculation failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 6.5 — Zone calculation + RR validation (C0.0.2)
        zone_low: float | None = None
        zone_high: float | None = None
        if (
            trade_plan
            and trade_plan.decision in ("BUY", "SELL")
            and trade_plan.entry_price is not None
            and trade_plan.stop_loss is not None
            and trade_plan.take_profit is not None
        ):
            zone_low, zone_high, worst_rr = _calculate_zone_with_clipping(
                entry_price=trade_plan.entry_price,
                stop_loss=trade_plan.stop_loss,
                take_profit=trade_plan.take_profit,
                atr=atr,
                side=trade_plan.decision,
            )
            if worst_rr is None:
                logger.warning(
                    f"RR validation failed after clipping for {symbol} "
                    f"(demoting to INVALID via position_size=0)"
                )
                trade_plan = trade_plan.model_copy(
                    update={"position_size": 0.0}
                )
                zone_low = None
                zone_high = None
            else:
                logger.info(
                    f"Zone: [{zone_low:.2f}, {zone_high:.2f}] "
                    f"worst_rr={worst_rr:.3f}"
                )

        # Step 7 — Signal
        try:
            if self.signal_engine and trade_plan:
                logger.info("Generating trading signal...")
                signal = self.signal_engine.generate(trade_plan, decision)
                logger.info("TradingSignal created")

                if self.signal_repository is not None:
                    self.signal_repository.append(signal)
                    logger.info(f"Signal appended to repository: {signal.signal_id}")
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            self._set_failed(str(e))
            return PipelineResult(
                symbol=symbol,
                timeframe=timeframe,
                status="failed",
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

        # Step 7.5 — Lifecycle creation (C0.0.2, only for ACTIVE)
        # INVARIANT: ACTIVE signal MUST have a valid lifecycle before paper execution.
        lifecycle_created = False
        if signal is not None and signal.status == "ACTIVE":
            if self.lifecycle_repository is None:
                msg = "ACTIVE signal but lifecycle_repository is not wired"
                logger.error(msg)
                self._set_failed(msg)
                return PipelineResult(
                    symbol=symbol,
                    timeframe=timeframe,
                    status="failed",
                    error_message=msg,
                    timestamp=datetime.now(UTC),
                )
            if zone_low is None or zone_high is None:
                msg = (
                    "ACTIVE signal but no valid entry zone "
                    "(zone calculation failed) — refusing to execute"
                )
                logger.error(msg)
                self._set_failed(msg)
                return PipelineResult(
                    symbol=symbol,
                    timeframe=timeframe,
                    status="failed",
                    error_message=msg,
                    timestamp=datetime.now(UTC),
                )

            try:
                expires_at = calculate_expires_at(signal.created_at)
                lifecycle = SignalLifecycle(
                    signal_id=signal.signal_id,
                    symbol=signal.symbol,
                    status=SignalLifecycleStatus.ACTIVE,
                    expire_reason=None,
                    created_at=signal.created_at,
                    expires_at=expires_at,
                    zone_low=zone_low,
                    zone_high=zone_high,
                    terminal_at=None,
                )
                self.lifecycle_repository.create_with_supersede(lifecycle)
                lifecycle_created = True
                logger.info(f"SignalLifecycle created: {signal.signal_id}")
            except Exception as e:
                logger.error(f"Lifecycle creation failed: {e}")
                self._set_failed(str(e))
                return PipelineResult(
                    symbol=symbol,
                    timeframe=timeframe,
                    status="failed",
                    error_message=str(e),
                    timestamp=datetime.now(UTC),
                )

        # Step 8 — Paper Execution
        # INVARIANT: paper execution only after lifecycle_created == True for ACTIVE signals.
        if (
            self.paper_trading_engine
            and signal
            and getattr(signal, "status", None) == "ACTIVE"
            and lifecycle_created
        ):
            try:
                logger.info("Executing paper trade...")
                _ = self.paper_trading_engine.execute(signal)
                logger.info("Paper trade executed")
            except Exception as e:
                logger.error(f"Paper execution failed: {e}")

        # Notification
        if self.notification_engine and signal:
            try:
                self.notification_engine.notify_signal(signal)
            except Exception as e:
                logger.error(f"Notification failed: {e}")

        logger.info(f"Pipeline finished for {symbol}")

        # Success
        self.last_pipeline_status = "COMPLETED"
        self.last_pipeline_completed_at = datetime.now(UTC)
        self._record_pipeline_status(PipelineStatus.COMPLETED)

        return PipelineResult(
            symbol=symbol,
            timeframe=timeframe,
            status="completed",
            timestamp=datetime.now(UTC),
        )

    def _set_failed(self, error: str) -> None:
        self.last_pipeline_status = "FAILED"
        self.last_pipeline_error = error
        self.last_pipeline_completed_at = datetime.now(UTC)
        self._record_pipeline_status(PipelineStatus.FAILED)

    def _record_pipeline_status(self, status: PipelineStatus) -> None:
        if self.health_monitor:
            try:
                self.health_monitor.record_pipeline_status(status)
            except Exception:
                pass

    async def _evaluate_positions(self, symbol: str, current_price: float) -> None:
        """Evaluasi TP/SL untuk posisi open terkait symbol."""
        if not self.paper_trading_engine or not self.lifecycle_engine:
            return

        portfolio = getattr(self.paper_trading_engine, "portfolio_manager", None)
        if not portfolio:
            return

        positions = portfolio.get_open_positions()
        for pos in positions:
            if pos.symbol != symbol:
                continue

            action, fraction = self.lifecycle_engine.evaluate(pos, current_price)
            if action != "HOLD":
                logger.info(f"Lifecycle action={action} for {pos.symbol} {pos.side}")
                self.paper_trading_engine.apply_lifecycle_action(
                    pos.position_id, action, current_price, fraction
                )        