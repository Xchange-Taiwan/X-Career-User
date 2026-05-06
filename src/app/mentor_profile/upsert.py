from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.user.service.profile_service import ProfileService
from src.domain.user.model import user_model as user
from src.domain.mentor.service.mentor_service import MentorService
from src.domain.mentor.service.notify_service import NotifyService
from src.domain.mentor.model import mentor_model as mentor
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
        notify_service: NotifyService,
    ):
        self.profile_service: ProfileService = profile_service
        self.mentor_service: MentorService = mentor_service
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


    async def upsert_mentor_profile(
        self,
        db: AsyncSession,
        profile_dto: mentor.MentorProfileDTO,
        background_tasks: BackgroundTasks,
    ):
        res: mentor.MentorProfileVO = await self.mentor_service.upsert_mentor_profile(
            db, profile_dto
        )
        # 若為 is_mentor 狀態，則需通知 Search Service. Experiences are part
        # of the same payload, so a single PUT_MENTOR_PROFILE message covers
        # both the mentor-specific fields and the experiences array.
        if res.is_mentor:
            background_tasks.add_task(
                self.notify_service.updated_mentor_profile, mentor_profile=res
            )
        return res
