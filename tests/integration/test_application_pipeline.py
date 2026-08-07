"""Integration test: Orchestrator → full pipeline dengan mock minimal."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.application.orchestrator import PipelineOrchestrator
from src.core.models.account import AccountSnapshot
from src.core.models.analysis import TechnicalAnalysis
from src.core.models.candle import Candle
from src.core.models.confidence import ConfidenceResult
from src.core.models.execution import ExecutionPlan
from src.core.models.market_intelligence import (
    FuturesAnalysis,
    SentimentAnalysis,
    SupportResistanceResult,
    VolatilityAnalysis,
    VolumeAnalysis,
)
from src.core.models.normalized_asset import NormalizedAsset
from src.core.models.order import OrderResult
from src.core.models.recommendation import RecommendationResult
from src.core.models.risk import RiskResult
from src.core.models.setup import SetupResult
from src.core.models.structure import MarketStructureResult
from src.core.models.validation import ValidationResult
from src.core.types.enums import (
    ConfidenceLevel,
    ExecutionAction,
    ExecutionStatus,
    ExecutionType,
    MarketStructure,
    OrderRejectReason,
    OrderStatus,
    PipelineStatus,
    RecommendationAction,
    SentimentLevel,
    SetupType,
    Side,
    TrendDirection,
    ValidationCheck,
    VolumeSignal,
)
from src.market.in_memory_price_provider import InMemoryPriceProvider
from src.portfolio.portfolio_manager import PortfolioManager
from src.position.position_manager import PositionManager


class TestApplicationPipeline:
    async def test_full_pipeline_integration(self):
        """Semua step diisi mock → COMPLETED."""
        # Mock collectors
        registry = MagicMock()
        raw_data = {
            "symbol": "BTC",
            "binance": MagicMock(
                candles_4h=[MagicMock(spec=Candle) for _ in range(55)],
                candles_1h=[MagicMock(spec=Candle) for _ in range(10)],
                funding_rate=0.0001,
                open_interest=1e10,
                long_short_ratio=1.2,
            ),
            "coingecko": MagicMock(
                current_price=50000.0,
                total_volume=28000000000.0,
                market_cap=900000000000.0,
                price_change_24h=2.5,
                price_change_7d=-1.2,
            ),
            "fear_greed": MagicMock(value=75, classification="Greed"),
            "news": MagicMock(headlines=["BTC rally"]),
            "data_quality_score": 1.0,
        }
        registry.collect_all = AsyncMock(return_value=raw_data)

        # Normalizer
        normalizer = MagicMock()
        asset = NormalizedAsset(
            symbol="BTC",
            price=50000.0,
            volume_24h=28000000000.0,
            volume_spike_ratio=2.5,
            market_cap=900000000000.0,
            price_change_24h=2.5,
            price_change_7d=-1.2,
            funding_rate=0.0001,
            open_interest=1e10,
            long_short_ratio=1.25,
            fear_greed_value=75,
            fear_greed_classification="Greed",
            news_headlines=["BTC rally"],
            candles_4h=raw_data["binance"].candles_4h,
            candles_1h=raw_data["binance"].candles_1h,
            data_quality_score=1.0,
            timestamp=datetime.now(UTC),
        )
        normalizer.normalize.return_value = asset

        # Analysis engines
        ta_engine = MagicMock()
        ta_engine.analyze.return_value = TechnicalAnalysis(
            ema20=50500.0,
            ema50=48000.0,
            rsi14=65.0,
            atr14=1000.0,
            timestamp=datetime.now(UTC),
        )
        trend_engine = MagicMock()
        trend_engine.analyze.return_value = TrendDirection.BULLISH
        struct_engine = MagicMock()
        struct_engine.analyze.return_value = MarketStructureResult(
            structure=MarketStructure.BOS_BULLISH,
            direction=TrendDirection.BULLISH,
            swing_high=52000.0,
            swing_low=44000.0,
            timestamp=datetime.now(UTC),
        )
        vol_engine = MagicMock()
        vol_engine.analyze.return_value = VolumeAnalysis(
            state=VolumeSignal.SPIKE,
            spike_ratio=2.5,
            confidence_score=0.8,
            timestamp=datetime.now(UTC),
        )
        fut_engine = MagicMock()
        fut_engine.analyze.return_value = FuturesAnalysis(
            sentiment=SentimentLevel.GREED,
            funding_rate=0.0001,
            open_interest=1e10,
            long_short_ratio=1.2,
            confidence_score=0.7,
            timestamp=datetime.now(UTC),
        )
        vola_engine = MagicMock()
        vola_engine.analyze.return_value = VolatilityAnalysis(
            atr=1000.0,
            atr_normalized=2.0,
            risk_level="MEDIUM",
            confidence_score=1.0,
            timestamp=datetime.now(UTC),
        )
        sr_engine = MagicMock()
        sr_engine.analyze.return_value = SupportResistanceResult(
            nearest_support=45000.0,
            nearest_resistance=55000.0,
            price_position=0.3,
            confidence_score=0.8,
            timestamp=datetime.now(UTC),
        )
        sent_engine = MagicMock()
        sent_engine.analyze.return_value = SentimentAnalysis(
            overall=SentimentLevel.GREED,
            fear_greed_value=75,
            fear_greed_label="Greed",
            news_score=0.5,
            news_headline_count=1,
            confidence_score=0.8,
            timestamp=datetime.now(UTC),
        )
        conf_engine = MagicMock()
        conf_engine.calculate.return_value = ConfidenceResult(
            score=0.85,
            level=ConfidenceLevel.HIGH,
            positive_factors=["Test"],
            negative_factors=[],
            warnings=[],
            blocked_reasons=[],
            timestamp=datetime.now(UTC),
        )
        detector = MagicMock()
        detector.detect.return_value = SetupResult(
            direction=Side.LONG,
            setup_type=SetupType.TREND_FOLLOWING,
            triggered_rules=[],
            failed_rules=[],
            confidence_score=0.85,
            confidence_level=ConfidenceLevel.HIGH,
            blocked_reasons=[],
            is_valid_setup=True,
            reasoning=["Test"],
            timestamp=datetime.now(UTC),
        )
        validator = MagicMock()
        validator.validate.return_value = ValidationResult(
            approved=True,
            rejection_reasons=[],
            checks_passed={vc: True for vc in ValidationCheck},
            timestamp=datetime.now(UTC),
        )
        risk_eng = MagicMock()
        risk_eng.calculate.return_value = RiskResult(
            entry_price=50000.0,
            stop_loss=48000.0,
            stop_distance=2000.0,
            take_profit=55000.0,
            take_profit_distance=5000.0,
            position_size=0.1,
            risk_amount=200.0,
            expected_profit=500.0,
            expected_loss=200.0,
            risk_reward_ratio=2.5,
            max_loss_pct=2.0,
            direction=Side.LONG,
            risk_model="trend",
            warnings=[],
            timestamp=datetime.now(UTC),
        )
        rec_eng = MagicMock()
        rec_eng.recommend.return_value = RecommendationResult(
            action=RecommendationAction.BUY,
            summary="Test",
            reasons=[],
            warnings=[],
            confidence_score=0.85,
            confidence_level=ConfidenceLevel.HIGH,
            setup_type=SetupType.TREND_FOLLOWING,
            direction=Side.LONG,
            validation_result=ValidationResult(
                approved=True,
                rejection_reasons=[],
                checks_passed={vc: True for vc in ValidationCheck},
                timestamp=datetime.now(UTC),
            ),
            risk_result=RiskResult(
                entry_price=50000.0,
                stop_loss=48000.0,
                stop_distance=2000.0,
                take_profit=55000.0,
                take_profit_distance=5000.0,
                position_size=0.1,
                risk_amount=200.0,
                expected_profit=500.0,
                expected_loss=200.0,
                risk_reward_ratio=2.5,
                max_loss_pct=2.0,
                direction=Side.LONG,
                risk_model="trend",
                warnings=[],
                timestamp=datetime.now(UTC),
            ),
            ready_for_execution=True,
            timestamp=datetime.now(UTC),
        )
        planner = MagicMock()
        planner.plan.return_value = ExecutionPlan(
            execution_id=uuid4(),
            action=ExecutionAction.PLACE_ORDER,
            status=ExecutionStatus.READY,
            execution_type=ExecutionType.MARKET,
            side=Side.LONG,
            entry_price=50000.0,
            stop_loss=48000.0,
            take_profit=55000.0,
            position_size=0.1,
            risk_reward_ratio=2.5,
            confidence_score=0.85,
            recommendation_action=RecommendationAction.BUY,
            summary="Test",
            blocked_reasons=[],
            validation_reasons=[],
            warnings=[],
            timestamp=datetime.now(UTC),
        )
        executor = MagicMock()
        executor.execute = AsyncMock(
            return_value=OrderResult(
                execution_id=uuid4(),
                order_id=uuid4(),
                status=OrderStatus.FILLED,
                reject_reason=OrderRejectReason.NONE,
                execution_type=ExecutionType.MARKET,
                side=Side.LONG,
                symbol="BTC/USDT",
                requested_entry=50000.0,
                executed_entry=50000.0,
                position_size=0.1,
                stop_loss=48000.0,
                take_profit=55000.0,
                timestamp=datetime.now(UTC),
            )
        )
        pm = PositionManager()
        account = AccountSnapshot(
            balance=10000.0,
            equity=10000.0,
            margin_used=0.0,
            free_margin=10000.0,
            timestamp=datetime.now(UTC),
        )
        provider = InMemoryPriceProvider()
        provider.update_price("BTC/USDT", 50000.0)
        pfm = PortfolioManager()

        orch = PipelineOrchestrator(
            collector_registry=registry,
            asset_normalizer=normalizer,
            technical_engine=ta_engine,
            trend_engine=trend_engine,
            market_structure_engine=struct_engine,
            volume_engine=vol_engine,
            futures_engine=fut_engine,
            volatility_engine=vola_engine,
            support_resistance_engine=sr_engine,
            sentiment_engine=sent_engine,
            confidence_engine=conf_engine,
            setup_detector=detector,
            validator_engine=validator,
            risk_engine=risk_eng,
            recommendation_engine=rec_eng,
            execution_planner=planner,
            order_executor=executor,
            position_manager=pm,
            portfolio_manager=pfm,
            account_snapshot=account,
            price_provider=provider,
        )

        ctx = await orch.run("BTC")
        print("ERROR:", ctx.error_message)
        assert ctx.status == PipelineStatus.COMPLETED
        assert ctx.position is not None
        assert ctx.portfolio_snapshot is not None
