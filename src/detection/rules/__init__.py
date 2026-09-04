"""Detection rules package."""

from src.detection.rules.base_rule import BaseRule, RuleResult
from src.detection.rules.breakout import BreakoutRule
from src.detection.rules.reversal import ReversalRule
from src.detection.rules.trend_following import TrendFollowingRule

__all__ = [
    "BaseRule",
    "BreakoutRule",
    "ReversalRule",
    "RuleResult",
    "TrendFollowingRule",
]
