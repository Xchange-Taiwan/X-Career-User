from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.infra.db.orm.init.outbox_message_init import OutboxMessage
from src.config.constant import AggregateType, EventType, OutboxStatus
from src.config.exception import NotFoundException

class OutboxMessageRepository:
    async def get_by_id(self, db: AsyncSession, outbox_id: int) -> OutboxMessage:
        """
        Fetch a specific outbox message by its primary key.
        """
        message: Optional[OutboxMessage] = await db.get(OutboxMessage, outbox_id)
        
        if message is None:
            raise NotFoundException(msg=f"Outbox message not found with id: {outbox_id}")
            
        return message
    async def get_pending_messages(
        self, db: AsyncSession, limit: int = 100
    ) -> List[OutboxMessage]:
        """
        Fetch messages that are either initial (0) or failed (2)
        and are ready for another retry.
        """
        stmt = (
            select(OutboxMessage)
            .filter(
                OutboxMessage.status.in_([0, 2]),  # Initial or Failed
                OutboxMessage.next_retry_at <= datetime.now(),
            )
            .order_by(OutboxMessage.created_at.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def mark_as_success(self, db: AsyncSession, message_id: int) -> None:
        """Update status to 3 (Success) and clear error messages."""
        stmt = (
            update(OutboxMessage)
            .where(OutboxMessage.id == message_id)
            .values(status=3, err_msg=None)
        )
        await db.execute(stmt)
        await db.commit()

    async def mark_as_failed(
        self, db: AsyncSession, message_id: int, error: str
    ) -> None:
        """
        Increment retry count, update error message, and
        schedule the next retry (e.g., in 5 minutes).
        """
        # Simple exponential backoff: retry in (retry_count * 5) minutes
        msg = await db.get(OutboxMessage, message_id)
        if msg:
            msg.status = 2
            msg.retry_count += 1
            msg.err_msg = error
            msg.next_retry_at = datetime.now() + timedelta(minutes=5 * msg.retry_count)

            await db.commit()

    async def save_message(
        self,
        db: AsyncSession,
        aggregate_id: str,
        aggregate_type: AggregateType,
        event_type: EventType,
        payload: dict,
    ) -> None:
        """Manual way to insert a message into the outbox."""
        new_msg = OutboxMessage(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            event_type=event_type,
            payload=payload,
            status=OutboxStatus.PENDING,
        )
        db.add(new_msg)
        # Note: Do not commit here if this is part of a larger transaction!
