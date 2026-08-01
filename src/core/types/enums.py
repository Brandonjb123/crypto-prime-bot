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