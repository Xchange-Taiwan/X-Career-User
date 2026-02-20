import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.outbox.dao.outbox_message_repository import OutboxMessageRepository
from src.domain.outbox.model.outbox_message_model import OutboxMessageDTO
from src.config.exception import NotFoundException
from src.config.constant import OutboxStatus

log = logging.getLogger(__name__)


class OutboxService:
    def __init__(self, outbox_repository: OutboxMessageRepository):
        self.__outbox_repository = outbox_repository

    async def update_message_status(
        self, db: AsyncSession, message_id: int, dto: OutboxMessageDTO
    ) -> None:
        try:
            outbox_message: OutboxMessageRepository = await self.__outbox_repository.get_by_id(
                db, message_id
            )
            if not outbox_message:
                raise NotFoundException(msg=f"Outbox message {message_id} not found")

            if dto.status == OutboxStatus.SUCCESS:
                outbox_message.status = OutboxStatus.SUCCESS
                outbox_message.err_msg = None
                log.info(f"Outbox {message_id} marked as success.")

            else:
                # TODO: Notify function when retry reach some limits
                outbox_message.status = OutboxStatus.FAILED
                outbox_message.retry_count += 1
                outbox_message.next_retry_at = datetime.now(timezone.utc)
                new_err = dto.error_msg or "Unknown error"
                if outbox_message.err_msg:
                    outbox_message.err_msg = f"{outbox_message.err_msg}; {new_err}"
                else:
                    outbox_message.err_msg = new_err

                log.warning(f"Outbox {message_id} failed. History: {outbox_message.err_msg}")

            await db.commit()

        except Exception as e:
            await db.rollback()
            log.error(f"Update failed for outbox {message_id}: {str(e)}")
            raise e
