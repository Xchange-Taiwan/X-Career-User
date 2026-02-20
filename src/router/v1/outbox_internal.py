from fastapi import APIRouter, Depends, Path, Body
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.databse import db_session
from src.router.res.response import *
from src.domain.outbox.service.outbox_service import OutboxService
from src.domain.outbox.model import outbox_message_model as outboxMessage
from src.app._di.injection import (
    get_outbox_service
)

router = APIRouter(prefix="/internal/outbox", tags=["Internal Outbox"])

@router.put("/{message_id}", responses=idempotent_response("update_outbox", outboxMessage.OutboxMessageVO))
async def update_outbox_status(
    message_id: int = Path(..., description="The ID of the outbox message"),
    body: outboxMessage.OutboxMessageDTO = Body(...),
    db: AsyncSession = Depends(db_session),
    # It tells FastAPI: "Before running this route function, go run get_outbox_service first, and give me whatever it returns as the outbox_service variable."
    outbox_service: OutboxService = Depends(get_outbox_service),
):
    """
    Internal endpoint to update outbox status.
    """

    await outbox_service.update_message_status(
        db=db, message_id=message_id, dto=body
    )

    return res_success(msg="Status updated successfully")
