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
from src.domain.mentor.service.notify_service import NotifyService
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

"""
以 mentor profile 為中心的服務，跨越 user, mentor 兩個 domains, 
所以放在 app/mentor_profile 下
"""


class MentorProfile:
    def __init__(
        self,
        profile_service: ProfileService,
        mentor_service: MentorService,
        experience_service: ExperienceService,
        notify_service: NotifyService,
    ):
        self.profile_service: ProfileService = profile_service
        self.mentor_service: MentorService = mentor_service
        self.exp_service: ExperienceService = experience_service
        self.notify_service: NotifyService = notify_service

    async def upsert_profile(
        self, db: AsyncSession, dto: user.ProfileDTO, background_tasks: BackgroundTasks
    ):
        res: user.ProfileVO = await self.profile_service.upsert_profile(db, dto)
        # 若為 is_mentor 狀態，則需通知 Search Service
        if res.is_mentor:
            background_tasks.add_task(
                self.notify_service.updated_user_profile, user_id=res.user_id
            )
        return res

    async def touch_avatar(
        self,
        db: AsyncSession,
        user_id: int,
        background_tasks: BackgroundTasks,
    ) -> int:
        """Bump ``avatar_updated_at`` after a successful avatar upload.

        Stable per-user S3 keys mean ``profile.avatar`` doesn't change on
        re-upload, so the standard upsert path can't detect the bytes have
        changed. The BFF calls this directly after the upload to refresh the
        cache buster, then re-publishes to Search for mentor users so the
        index stays in sync within the existing 60s SLA.
        """
        new_value, is_mentor = await self.profile_service.touch_avatar(
            db, user_id
        )
        if is_mentor:
            background_tasks.add_task(
                self.notify_service.updated_user_profile, user_id=user_id
            )
        return new_value


    async def upsert_mentor_profile(
        self,
        db: AsyncSession,
        profile_dto: mentor.MentorProfileDTO,
        background_tasks: BackgroundTasks,
    ):
        res: mentor.MentorProfileVO = await self.mentor_service.upsert_mentor_profile(
            db, profile_dto
        )
        # 若為 is_mentor 狀態，則需通知 Search Service
        if res.is_mentor:
            background_tasks.add_task(
                self.notify_service.updated_mentor_profile, mentor_profile=res
            )
        return res

    async def upsert_exp(
        self,
        db,
        user_id: int,
        experience_dto: exp.ExperienceDTO,
        background_tasks: BackgroundTasks,
        is_mentor: Optional[bool] = None,
    ):
        res: exp.ExperienceVO = await self.exp_service.upsert_exp(
            db=db,
            user_id=user_id,
            experience_dto=experience_dto,
        )
        background_tasks.add_task(
            self.notify_service.notify_updated_user_experiences,
            user_id=user_id,
            is_mentor=is_mentor,
        )
        return res

    async def delete_experience(
        self,
        db,
        user_id: int,
        experience_dto: exp.ExperienceDTO,
        background_tasks: BackgroundTasks,
        is_mentor: Optional[bool] = None,
    ):
        res: bool = await self.exp_service.delete_exp_by_user_and_exp_id(
            db=db, user_id=user_id, experience_dto=experience_dto,
        )
        background_tasks.add_task(
            self.notify_service.notify_updated_user_experiences,
            user_id=user_id,
            is_mentor=is_mentor,
        )
        return res
