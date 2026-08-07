"""Telegram message and response models."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.core.types.enums import TelegramCommand, TelegramResponseType


class TelegramMessage(BaseModel):
    message_id: UUID = uuid4()
    chat_id: str
    command: TelegramCommand
    text: str = ""
    timestamp: datetime


class TelegramResponse(BaseModel):
    response_id: UUID = uuid4()
    response_type: TelegramResponseType
    text: str
    timestamp: datetime
