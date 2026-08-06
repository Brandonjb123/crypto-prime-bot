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

class ValidationCheck(StrEnum):
    CONFIDENCE_CHECK = "CONFIDENCE_CHECK"
    BLOCKED_REASONS_CHECK = "BLOCKED_REASONS_CHECK"
    SETUP_COMPLETENESS = "SETUP_COMPLETENESS"
    MARKET_CONDITION = "MARKET_CONDITION"
    DUPLICATE_SIGNAL = "DUPLICATE_SIGNAL"


class ValidationReason(StrEnum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    BLOCKED_REASONS = "BLOCKED_REASONS"
    SIDEWAYS_MARKET = "SIDEWAYS_MARKET"
    NO_SETUP_DETECTED = "NO_SETUP_DETECTED"
    DUPLICATE_SIGNAL = "DUPLICATE_SIGNAL"
    # Reserved for future use:
    RISK_TOO_HIGH = "RISK_TOO_HIGH"
    SPREAD_TOO_HIGH = "SPREAD_TOO_HIGH"
    MAX_POSITION = "MAX_POSITION"
    MARKET_CLOSED = "MARKET_CLOSED"
    DUPLICATE_POSITION = "DUPLICATE_POSITION"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"    

class RiskWarning(StrEnum):
    RR_TOO_LOW = "RR_TOO_LOW"
    POSITION_SIZE_CAPPED = "POSITION_SIZE_CAPPED"
    STOP_TOO_CLOSE = "STOP_TOO_CLOSE"
    TP_TOO_FAR = "TP_TOO_FAR"
    HIGH_VOLATILITY_RISK = "HIGH_VOLATILITY_RISK"    

class RecommendationAction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"
    SKIP = "SKIP"


class RecommendationReason(StrEnum):
    VALIDATED_SETUP = "VALIDATED_SETUP"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    HIGH_RISK = "HIGH_RISK"
    SIDEWAYS_MARKET = "SIDEWAYS_MARKET"
    NO_SETUP = "NO_SETUP"
    BLOCKED_WARNING = "BLOCKED_WARNING"
    LOW_RISK_REWARD = "LOW_RISK_REWARD"    

class ExecutionAction(StrEnum):
    PLACE_ORDER = "PLACE_ORDER"
    DO_NOT_EXECUTE = "DO_NOT_EXECUTE"


class ExecutionType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class ExecutionStatus(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"    

class OrderStatus(StrEnum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class OrderRejectReason(StrEnum):
    NONE = "NONE"
    INVALID_PRICE = "INVALID_PRICE"
    INVALID_SIZE = "INVALID_SIZE"
    MARKET_CLOSED = "MARKET_CLOSED"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    UNKNOWN = "UNKNOWN"   

class PositionStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    STOPPED = "STOPPED"
    TAKE_PROFIT = "TAKE_PROFIT"


class PositionCloseReason(StrEnum):
    NONE = "NONE"
    MANUAL = "MANUAL"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    UNKNOWN = "UNKNOWN"     

class PortfolioStatus(StrEnum):
    EMPTY = "EMPTY"
    ACTIVE = "ACTIVE"
    RISK_LIMIT = "RISK_LIMIT"   