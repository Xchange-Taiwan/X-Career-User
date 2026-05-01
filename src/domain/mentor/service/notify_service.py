from typing import Dict, List, Optional
from fastapi import BackgroundTasks
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.template.service_api import IServiceApi
from src.infra.mq.sqs_mq_adapter import SqsMqAdapter
from src.infra.databse import SessionLocal
from src.domain.user.dao.tag_repository import TagRepository
from src.domain.user.service.profile_service import ProfileService
from src.domain.user.model import user_model as user
from src.domain.mentor.service.mentor_service import MentorService
from src.domain.mentor.service.experience_service import ExperienceService
from src.domain.mentor.model import (
    experience_model as exp,
    mentor_model as mentor,
)
from src.config.constant import ExperienceCategory
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
        experience_service: ExperienceService,
        mq_adapter: SqsMqAdapter,
        tag_repository: TagRepository,
    ):
        self.mentor_service = mentor_service
        self.exp_service: ExperienceService = experience_service
        self.mq_adapter = mq_adapter
        self.tag_repository = tag_repository

    async def _serialize_user_tags(
        self, db: AsyncSession, user_id: int
    ) -> List[Dict]:
        # Hydrates current user_tags rows into the SQS-friendly shape the
        # Search service expects on `profiles_v2.user_tags`. Joins to Tag so
        # kind / subject_group / language / desc travel with the row.
        rows = await self.tag_repository.get_user_tags_with_tag(db, user_id)
        return [
            {
                "tag_id": ut.tag_id,
                "kind": tag.kind,
                "intent": ut.intent,
                "subject_group": tag.subject_group,
                "subject": tag.subject,
                "language": tag.language,
                "desc": tag.desc,
                "parent_subject_group": tag.parent_subject_group,
            }
            for ut, tag in rows
        ]

    async def updated_user_profile(self, user_id: int):
        """Triggered by PUT /users/profile — syncs the full mentor profile document."""
        try:
            async with SessionLocal() as db:
                mentor_profile: mentor.MentorProfileVO = (
                    await self.mentor_service.get_mentor_profile_by_id(
                        db, user_id, DEFAULT_LANGUAGE
                    )
                )
                user_tags = await self._serialize_user_tags(db, user_id)
            payload = {
                **mentor_profile.to_dto_json(user_tags=user_tags),
                "action": "UPSERT_MENTOR_PROFILE",
            }
            await self.mq_adapter.publish_message(payload, group_id=str(user_id))
            log.info(f"[NotifyService] published UPSERT_MENTOR_PROFILE, user_id={user_id}")

        except Exception as e:
            log.error(f"[NotifyService] failed to publish user profile update, user_id={user_id}: {e}")

    async def updated_mentor_profile(self, mentor_profile: mentor.MentorProfileVO):
        """Triggered by PUT /mentors/mentor_profile — updates mentor-specific fields."""
        try:
            user_id = mentor_profile.user_id
            async with SessionLocal() as db:
                user_tags = await self._serialize_user_tags(db, user_id)
            payload = {
                **mentor_profile.to_dto_json(user_tags=user_tags),
                "action": "PUT_MENTOR_PROFILE",
            }
            await self.mq_adapter.publish_message(payload, group_id=str(user_id))
            log.info(f"[NotifyService] published PUT_MENTOR_PROFILE, user_id={user_id}")
        except Exception as e:
            log.error(f"[NotifyService] failed to publish mentor profile update, user_id={user_id}: {e}")

    async def notify_updated_user_experiences(
        self, user_id: int, is_mentor: Optional[bool] = None
    ):
        """Triggered by PUT/DELETE /mentors/{id}/experiences — patches the experiences array."""
        try:
            if is_mentor is False:
                experiences = []
            else:
                async with SessionLocal() as db:
                    experiences: List[exp.ExperienceVO] = (
                        await self.exp_service.get_exp_list_by_user_id(db, user_id)
                    )

            # 若為 is_mentor 狀態且 experiences 有至少兩筆資料，則需通知 Search Service
            if is_mentor is True and ExperienceService.is_mentor(experiences):
                mentor_profile: mentor.MentorProfileVO = mentor.MentorProfileVO(
                    user_id=user_id, experiences=experiences
                )
                async with SessionLocal() as db:
                    user_tags = await self._serialize_user_tags(db, user_id)
                payload = {
                    **mentor_profile.to_dto_json(user_tags=user_tags),
                    "action": "PATCH_MENTOR_PROFILE",
                }
                await self.mq_adapter.publish_message(payload, group_id=str(user_id))
                log.info(f"[NotifyService] published PATCH_MENTOR_PROFILE, user_id={user_id}")

        except Exception as e:
            log.error(f"[NotifyService] failed to publish experience update, user_id={user_id}: {e}")

    async def notify_updated_user_tags(self, user_id: int):
        """Triggered by PUT /v1/users/{id}/tags — fires a fresh full UPSERT
        so Search re-syncs both v1 (legacy nested arrays, unchanged) and v2
        (`profiles_v2.user_tags`, populated from the freshly-written tags)."""
        try:
            async with SessionLocal() as db:
                mentor_profile: mentor.MentorProfileVO = (
                    await self.mentor_service.get_mentor_profile_by_id(
                        db, user_id, DEFAULT_LANGUAGE
                    )
                )
                user_tags = await self._serialize_user_tags(db, user_id)
            payload = {
                **mentor_profile.to_dto_json(user_tags=user_tags),
                "action": "UPSERT_MENTOR_PROFILE",
            }
            await self.mq_adapter.publish_message(payload, group_id=str(user_id))
            log.info(f"[NotifyService] published UPSERT_MENTOR_PROFILE (tags), user_id={user_id}")
        except Exception as e:
            log.error(f"[NotifyService] failed to publish user tags update, user_id={user_id}: {e}")

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
