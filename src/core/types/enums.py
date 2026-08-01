from enum import Enum


class Side(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class Verdict(str, Enum):
    SETUP_VALID = "SETUP_VALID"
    NO_SETUP = "NO_SETUP"


class Timeframe(str, Enum):
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"


class TrendDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class VolumeSignal(str, Enum):
    SPIKE = "SPIKE"
    NORMAL = "NORMAL"
    WEAK = "WEAK"


class MarketStructure(str, Enum):
    BOS_BULLISH = "BOS_BULLISH"
    BOS_BEARISH = "BOS_BEARISH"
    CHOCH = "CHOCH"
    NONE = "NONE"


class SentimentLevel(str, Enum):
    GREED = "GREED"
    NEUTRAL = "NEUTRAL"
    FEAR = "FEAR"