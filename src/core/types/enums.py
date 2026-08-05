from enum import StrEnum


class Side(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


class Verdict(StrEnum):
    SETUP_VALID = "SETUP_VALID"
    NO_SETUP = "NO_SETUP"


class Timeframe(StrEnum):
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"


class TrendDirection(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"


class ConfidenceLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class VolumeSignal(StrEnum):
    SPIKE = "SPIKE"
    NORMAL = "NORMAL"
    WEAK = "WEAK"


class MarketStructure(StrEnum):
    BOS_BULLISH = "BOS_BULLISH"
    BOS_BEARISH = "BOS_BEARISH"
    CHOCH = "CHOCH"
    NONE = "NONE"


class SentimentLevel(StrEnum):
    GREED = "GREED"
    NEUTRAL = "NEUTRAL"
    FEAR = "FEAR"   


class ConfidenceWarning(StrEnum):
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLUME = "LOW_VOLUME"
    STRUCTURE_CONFLICT = "STRUCTURE_CONFLICT"
    SENTIMENT_CONFLICT = "SENTIMENT_CONFLICT"
    FUNDING_EXTREME = "FUNDING_EXTREME"
    PRICE_NEAR_RESISTANCE = "PRICE_NEAR_RESISTANCE"
    PRICE_NEAR_SUPPORT = "PRICE_NEAR_SUPPORT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class SetupType(StrEnum):
    TREND_FOLLOWING = "trend_following"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"


class RuleType(StrEnum):
    TREND_FOLLOWING = "trend_following"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"    