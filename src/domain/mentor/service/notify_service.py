from src.infra.mq.sqs_mq_adapter import SqsMqAdapter
from src.infra.databse import SessionLocal
from src.domain.mentor.service.mentor_service import MentorService
from src.domain.mentor.model import mentor_model as mentor
from src.config.conf import (
    SEARCH_SERVICE_URL,
    DEFAULT_LANGUAGE,
)
import logging

log = logging.getLogger(__name__)


POST_MENTOR_URL = SEARCH_SERVICE_URL + "/v1/internal/mentor"


class NotifyService:
    def __init__(
        self,
        mentor_service: MentorService,
        mq_adapter: SqsMqAdapter,
    ):
        self.mentor_service = mentor_service
        self.mq_adapter = mq_adapter

    async def updated_user_profile(self, user_id: int):
        """Triggered by PUT /users/profile — syncs the full mentor profile document."""
        try:
            async with SessionLocal() as db:
                mentor_profile: mentor.MentorProfileVO = (
                    await self.mentor_service.get_mentor_profile_by_id(
                        db, user_id, DEFAULT_LANGUAGE
                    )
                )
            # to_dto_json flattens the 5 hydrated tag buckets into top-level
            # subject_group arrays — Search filters by canonical key, so the
            # full TagVO would be wasted bytes on the wire.
            payload = {
                **mentor_profile.to_dto_json(),
                "action": "UPSERT_MENTOR_PROFILE",
            }
            await self.mq_adapter.publish_message(payload, group_id=str(user_id))
            log.info(f"[NotifyService] published UPSERT_MENTOR_PROFILE, user_id={user_id}")

        except Exception as e:
            log.error(f"[NotifyService] failed to publish user profile update, user_id={user_id}: {e}")

    async def updated_mentor_profile(self, mentor_profile: mentor.MentorProfileVO):
        """Triggered by PUT /mentors/mentor_profile — updates mentor-specific fields,
        including experiences (which now ride inline on the profile row)."""
        try:
            user_id = mentor_profile.user_id
            payload = {
                **mentor_profile.to_dto_json(),
                "action": "PUT_MENTOR_PROFILE",
            }
            await self.mq_adapter.publish_message(payload, group_id=str(user_id))
            log.info(f"[NotifyService] published PUT_MENTOR_PROFILE, user_id={user_id}")
        except Exception as e:
            log.error(f"[NotifyService] failed to publish mentor profile update, user_id={user_id}: {e}")

    async def notify_delete_mentor_profile(self, user_id: int) -> None:
        try:
            payload = {
                "action": "DELETE_MENTOR_PROFILE",
                "user_id": user_id,
            }
            await self.mq_adapter.publish_message(payload, group_id=str(user_id))
            log.info(f"[NotifyService] published DELETE_MENTOR_PROFILE, user_id={user_id}")
        except Exception as e:
            log.error(f"[NotifyService] failed to publish DELETE_MENTOR_PROFILE, user_id={user_id}: {e}")
            raise
