from typing import List, Optional
from fastapi import BackgroundTasks
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.template.service_api import IServiceApi
from src.infra.mq.sqs_mq_adapter import SqsMqAdapter
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
import logging as log

log.basicConfig(filemode="w", level=log.INFO)


POST_MENTOR_URL = SEARCH_SERVICE_URL + "/v1/internal/mentor"


class NotifyService:
    def __init__(
        self,
        mentor_service: MentorService,
        experience_service: ExperienceService,
        mq_adapter: SqsMqAdapter,
    ):
        self.mentor_service = mentor_service
        self.exp_service: ExperienceService = experience_service
        self.mq_adapter = mq_adapter

    async def updated_user_profile(self, db: AsyncSession, user_id: str):
        try:
            mentor_profile: mentor.MentorProfileVO = (
                await self.mentor_service.get_mentor_profile_by_id(
                    db, user_id, DEFAULT_LANGUAGE
                )
            )
            await self.mq_adapter.publish_message(mentor_profile.to_dto_json())

        except Exception as e:
            log.error(f"Failed to notify search service: {str(e)}")

    # 更新 user 的 profile
    async def updated_mentor_profile(self, mentor_profile: mentor.MentorProfileVO):
        try:
            await self.mq_adapter.publish_message(mentor_profile.to_dto_json())
        except Exception as e:
            log.error(f"Failed to notify search service: {str(e)}")

    # 更新 user 的 experience
    async def notify_updated_user_experiences(
        self, db: AsyncSession, user_id: str, is_mentor: Optional[bool] = None
    ):
        try:
            if is_mentor is False:
                experiences = []
            else:
                experiences: List[exp.ExperienceVO] = (
                    await self.exp_service.get_exp_list_by_user_id(db, user_id)
                )

            # 若為 is_mentor 狀態，則需通知 Search Service
            if ExperienceService.is_mentor(experiences):
                mentor_profile: mentor.MentorProfileVO = mentor.MentorProfileVO(
                    user_id=user_id, experiences=experiences
                )
                await self.mq_adapter.publish_message(mentor_profile.to_dto_json())

        except Exception as e:
            log.error(f"Failed to notify search service: {str(e)}")
