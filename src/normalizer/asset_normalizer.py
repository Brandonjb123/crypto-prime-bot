"""Asset Normalizer — mengubah raw collector output menjadi NormalizedAsset."""

from datetime import UTC, datetime

from src.core.exceptions.collector_exceptions import InsufficientDataError
from src.core.models.candle import Candle
from src.core.models.normalized_asset import NormalizedAsset


class AssetNormalizer:
    """Normalize raw data dari CollectorRegistry menjadi NormalizedAsset."""

    MIN_DATA_QUALITY_SCORE = 0.70

    def normalize(self, raw_data: dict) -> NormalizedAsset:
        """
        Normalize raw collector output menjadi single NormalizedAsset object.
        """
        symbol = raw_data.get("symbol", "UNKNOWN")
        quality_score = raw_data.get("data_quality_score", 0.0)

        if quality_score < self.MIN_DATA_QUALITY_SCORE:
            raise InsufficientDataError(
                f"Data quality {quality_score:.0%} below threshold "
                f"{self.MIN_DATA_QUALITY_SCORE:.0%} for {symbol}"
            )

        binance_data = raw_data.get("binance")
        coingecko_data = raw_data.get("coingecko")
        fear_greed_data = raw_data.get("fear_greed")
        news_data = raw_data.get("news")

        # ── Parse Binance raw klines ke Candle ──
        raw_candles_4h = binance_data.candles_4h if binance_data else []
        raw_candles_1h = binance_data.candles_1h if binance_data else []
        candles_4h = self._parse_candles(raw_candles_4h)
        candles_1h = self._parse_candles(raw_candles_1h)

        # ── Binance fields ──
        funding_rate = binance_data.funding_rate if binance_data else 0.0
        open_interest = binance_data.open_interest if binance_data else 0.0
        long_short_ratio = binance_data.long_short_ratio if binance_data else 1.0

        # ── CoinGecko fields ──
        price = coingecko_data.current_price if coingecko_data else 0.0
        volume_24h = coingecko_data.total_volume if coingecko_data else 0.0
        market_cap = coingecko_data.market_cap if coingecko_data else 0.0
        price_change_24h = coingecko_data.price_change_24h if coingecko_data else 0.0
        price_change_7d = coingecko_data.price_change_7d if coingecko_data else 0.0

        # ── Volume spike ratio ──
        volume_spike_ratio = self._calc_volume_spike_ratio(raw_candles_4h)

        # ── Fear & Greed ──
        fear_greed_value = fear_greed_data.value if fear_greed_data else 0
        fear_greed_classification = fear_greed_data.classification if fear_greed_data else "unknown"

        # ── News ──
        news_headlines = news_data.headlines if news_data else []

        return NormalizedAsset(
            symbol=symbol,
            price=price,
            volume_24h=volume_24h,
            volume_spike_ratio=volume_spike_ratio,
            market_cap=market_cap,
            price_change_24h=price_change_24h,
            price_change_7d=price_change_7d,
            funding_rate=funding_rate,
            open_interest=open_interest,
            long_short_ratio=long_short_ratio,
            fear_greed_value=fear_greed_value,
            fear_greed_classification=fear_greed_classification,
            news_headlines=news_headlines,
            candles_4h=candles_4h,
            candles_1h=candles_1h,
            data_quality_score=quality_score,
            timestamp=datetime.now(UTC),
        )

    def _parse_candles(self, raw_klines: list) -> list[Candle]:
        """
        Parse raw Binance klines ke list of Candle objects.
        Binance kline format:
        [timestamp_ms, open, high, low, close, volume, ...]
        """
        candles = []
        for kline in raw_klines:
            try:
                candles.append(
                    Candle(
                        timestamp=datetime.fromtimestamp(kline[0] / 1000, UTC),
                        open=float(kline[1]),
                        high=float(kline[2]),
                        low=float(kline[3]),
                        close=float(kline[4]),
                        volume=float(kline[5]),
                    )
                )
            except (IndexError, ValueError):
                continue
        return candles

    def _calc_volume_spike_ratio(self, raw_klines: list) -> float:
        """Hitung volume spike ratio dari raw klines."""
        if len(raw_klines) < 21:
            return 1.0

        try:
            current_volume = float(raw_klines[-1][5])
            avg_volume = sum(float(c[5]) for c in raw_klines[-21:-1]) / 20
            if avg_volume > 0:
                return round(current_volume / avg_volume, 4)
        except (IndexError, ValueError, ZeroDivisionError):
            pass

        return 1.0
