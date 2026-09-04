"""Pipeline Orchestrator — menjalankan seluruh pipeline untuk satu symbol."""

from datetime import UTC, datetime

from src.application.pipeline_context import PipelineContext
from src.core.models.snapshot import AnalysisSnapshot
from src.core.types.enums import PipelineStatus


class PipelineOrchestrator:
    """Orchestrate full analysis-to-execution pipeline."""

    def __init__(
        self,
        collector_registry=None,
        asset_normalizer=None,
        technical_engine=None,
        trend_engine=None,
        market_structure_engine=None,
        volume_engine=None,
        futures_engine=None,
        volatility_engine=None,
        support_resistance_engine=None,
        sentiment_engine=None,
        confidence_engine=None,
        setup_detector=None,
        validator_engine=None,
        risk_engine=None,
        recommendation_engine=None,
        execution_planner=None,
        order_executor=None,
        position_manager=None,
        portfolio_manager=None,
        account_snapshot=None,
        price_provider=None,
    ):
        self.collector_registry = collector_registry
        self.asset_normalizer = asset_normalizer
        self.technical_engine = technical_engine
        self.trend_engine = trend_engine
        self.market_structure_engine = market_structure_engine
        self.volume_engine = volume_engine
        self.futures_engine = futures_engine
        self.volatility_engine = volatility_engine
        self.support_resistance_engine = support_resistance_engine
        self.sentiment_engine = sentiment_engine
        self.confidence_engine = confidence_engine
        self.setup_detector = setup_detector
        self.validator_engine = validator_engine
        self.risk_engine = risk_engine
        self.recommendation_engine = recommendation_engine
        self.execution_planner = execution_planner
        self.order_executor = order_executor
        self.position_manager = position_manager
        self.portfolio_manager = portfolio_manager
        self.account_snapshot = account_snapshot
        self.price_provider = price_provider

    async def run(self, symbol: str, timeframe: str = "4h") -> PipelineContext:
        ctx = PipelineContext(symbol=symbol, timeframe=timeframe, status=PipelineStatus.RUNNING)

        try:
            # Step 1 — Collect
            if self.collector_registry:
                raw_data = await self.collector_registry.collect_all(symbol)
                ctx.collected_data = raw_data

            # Step 2 — Normalize
            if self.asset_normalizer and ctx.collected_data:
                ctx.normalized_asset = self.asset_normalizer.normalize(ctx.collected_data)

            # Step 3 — Analysis (8 engines) + Confidence (gabung)
            if all(
                [
                    ctx.normalized_asset,
                    self.technical_engine,
                    self.trend_engine,
                    self.market_structure_engine,
                    self.volume_engine,
                    self.futures_engine,
                    self.volatility_engine,
                    self.support_resistance_engine,
                    self.sentiment_engine,
                ]
            ):
                asset = ctx.normalized_asset
                technical = self.technical_engine.analyze(asset)
                trend = self.trend_engine.analyze(technical, asset.price)
                structure = self.market_structure_engine.analyze(asset.candles_4h, trend)
                volume = self.volume_engine.analyze(asset)
                futures = self.futures_engine.analyze(asset)
                volatility = self.volatility_engine.analyze(technical, asset.price)
                sr = self.support_resistance_engine.analyze(asset.candles_4h, asset.price)
                sentiment = self.sentiment_engine.analyze(asset)

                # Hitung confidence dulu
                confidence = None
                if self.confidence_engine:
                    confidence = self.confidence_engine.calculate(
                        technical=technical,
                        trend=trend,
                        structure=structure,
                        volume=volume,
                        futures=futures,
                        volatility=volatility,
                        sr=sr,
                        sentiment=sentiment,
                        price=asset.price,
                    )
                    ctx.confidence_result = confidence

                snapshot = AnalysisSnapshot(
                    symbol=asset.symbol,
                    price=asset.price,
                    technical=technical,
                    trend=trend,
                    structure=structure,
                    volume=volume,
                    futures=futures,
                    volatility=volatility,
                    support_resistance=sr,
                    sentiment=sentiment,
                    confidence=confidence,
                    timestamp=datetime.now(UTC),
                )
                ctx.analysis_snapshot = snapshot

            # Step 4 — Detection
            if self.setup_detector and ctx.analysis_snapshot:
                ctx.setup_result = self.setup_detector.detect(ctx.analysis_snapshot)

            # Step 5 — Validation
            if self.validator_engine and ctx.setup_result and ctx.analysis_snapshot:
                ctx.validation_result = self.validator_engine.validate(
                    ctx.setup_result, ctx.analysis_snapshot
                )

            # Step 6 — Risk
            if (
                self.risk_engine
                and ctx.analysis_snapshot
                and ctx.setup_result
                and ctx.validation_result
            ):
                ctx.risk_result = self.risk_engine.calculate(
                    ctx.analysis_snapshot, ctx.setup_result, ctx.validation_result
                )

            # Step 7 — Recommendation
            if (
                self.recommendation_engine
                and ctx.analysis_snapshot
                and ctx.setup_result
                and ctx.validation_result
                and ctx.risk_result
            ):
                ctx.recommendation_result = self.recommendation_engine.recommend(
                    ctx.analysis_snapshot, ctx.setup_result, ctx.validation_result, ctx.risk_result
                )

            # Step 8 — Execution Plan
            if (
                self.execution_planner
                and ctx.recommendation_result
                and ctx.risk_result
                and ctx.validation_result
            ):
                ctx.execution_plan = self.execution_planner.plan(
                    ctx.recommendation_result, ctx.risk_result, ctx.validation_result
                )

            # Step 9 — Order
            if self.order_executor and ctx.execution_plan:
                ctx.order_result = await self.order_executor.execute(ctx.execution_plan)

            # Step 10 — Position
            if self.position_manager and ctx.order_result:
                try:
                    ctx.position = self.position_manager.open_position(ctx.order_result)
                except Exception:
                    pass  # Bisa jadi REJECTED — skip

            # Step 11 — Portfolio
            if (
                self.portfolio_manager
                and self.position_manager
                and self.account_snapshot
                and self.price_provider
            ):
                positions = self.position_manager.get_all_positions()
                ctx.portfolio_snapshot = self.portfolio_manager.create_snapshot(
                    positions, self.account_snapshot, self.price_provider
                )

            ctx.status = PipelineStatus.COMPLETED

        except Exception as e:
            ctx.status = PipelineStatus.FAILED
            ctx.error_message = str(e)[:500]

        return ctx
