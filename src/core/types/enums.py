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

class ExchangeOrderStatus(StrEnum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class ExchangeErrorType(StrEnum):
    NETWORK_ERROR = "NETWORK_ERROR"
    AUTH_ERROR = "AUTH_ERROR"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    INVALID_ORDER = "INVALID_ORDER"
    RATE_LIMIT = "RATE_LIMIT"
    UNKNOWN = "UNKNOWN"

class SyncStatus(StrEnum):
    SYNCED = "SYNCED"
    MISMATCH = "MISMATCH"
    UPDATED = "UPDATED"
    FAILED = "FAILED"


class SyncEntityType(StrEnum):
    POSITION = "POSITION"
    ORDER = "ORDER"
    PORTFOLIO = "PORTFOLIO"


class SyncReason(StrEnum):
    LOCAL_MISSING = "LOCAL_MISSING"
    EXCHANGE_MISSING = "EXCHANGE_MISSING"
    STATUS_CHANGED = "STATUS_CHANGED"
    SIZE_CHANGED = "SIZE_CHANGED"
    PRICE_CHANGED = "PRICE_CHANGED"
    MANUAL_CHANGE = "MANUAL_CHANGE"
    UNKNOWN = "UNKNOWN"

class BacktestStatus(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TradeOutcome(StrEnum):
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"
    OPEN = "OPEN"

class TelegramCommand(StrEnum):
    STATUS = "status"
    POSITIONS = "positions"
    PORTFOLIO = "portfolio"
    LAST_SIGNAL = "last_signal"
    HELP = "help"


class TelegramResponseType(StrEnum):
    TEXT = "text"
    ERROR = "error"
    UNKNOWN = "unknown"        

class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


class AuditEventType(StrEnum):
    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"
    PIPELINE_FAILED = "pipeline_failed"
    ORDER_CREATED = "order_created"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    PIPELINE_SKIPPED = "pipeline_skipped"


class RuntimeStatus(StrEnum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"

class ShutdownReason(StrEnum):
    MANUAL = "manual"
    SIGTERM = "sigterm"
    EXCEPTION = "exception"
    RESTART = "restart"

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

class NotificationLevel(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class PipelineStatus(StrEnum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"    

class PositionEvent(StrEnum):
    NONE = "NONE"
    STOP_LOSS_HIT = "STOP_LOSS_HIT"
    TAKE_PROFIT_HIT = "TAKE_PROFIT_HIT"
    HOLD = "HOLD"


     