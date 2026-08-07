"""Pipeline runtime context — not immutable, filled step by step."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.core.types.enums import PipelineStatus


class PipelineContext(BaseModel):
    run_id: UUID = uuid4()
    symbol: str
    timeframe: str
    collected_data: object | None = None
    normalized_asset: object | None = None
    analysis_snapshot: object | None = None
    confidence_result: object | None = None
    setup_result: object | None = None
    validation_result: object | None = None
    risk_result: object | None = None
    recommendation_result: object | None = None
    execution_plan: object | None = None
    order_result: object | None = None
    position: object | None = None
    portfolio_snapshot: object | None = None
    status: PipelineStatus = PipelineStatus.IDLE
    error_message: str | None = None
    created_at: datetime = datetime.now(UTC)
