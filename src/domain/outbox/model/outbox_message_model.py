import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from src.config.constant import OutboxStatus

log = logging.getLogger(__name__)


class OutboxMessageDTO(BaseModel):
    """
    Data Transfer Object for updating Outbox status from the relay/sink.
    """

    status: int = Field(
        ..., description="0: initial, 1: pending, 2: failed, 3: success"
    )
    error_msg: Optional[str] = None

    model_config = {"from_attributes": True}


class OutboxMessageVO(BaseModel):
    """
    Value Object for returning Outbox Message details.
    """

    id: int
    aggregate_id: str
    aggregate_type: str
    event_type: str
    payload: Dict[str, Any]
    status: int
    retry_count: int
    err_msg: Optional[str] = None
    created_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    def to_json(self):
        """Converts the VO to a JSON-compatible dictionary."""
        result = self.model_dump_json()
        return json.loads(result)

    @staticmethod
    def from_model(model: Any) -> "OutboxMessageVO":
        """
        Maps a SQLAlchemy OutboxMessage model to this VO.
        """
        return OutboxMessageVO.model_validate(model)
