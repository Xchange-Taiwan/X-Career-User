from typing import List
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
from src.config.conf import SEARCH_SERVICE_URL
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


POST_MENTOR_URL = SEARCH_SERVICE_URL + '/v1/internal/mentor'

'''
以 mentor profile 為中心的服務，跨越 user, mentor 兩個 domains, 
所以放在 app/mentor_profile 下
'''
class MentorProfile:
    def __init__(self,
                 service_api: IServiceApi,
                 profile_service: ProfileService,
                 mentor_service: MentorService,
                 experience_service: ExperienceService,
                 mq_adapter: SqsMqAdapter,
                 ):
        self.service_api: IServiceApi = service_api
        self.profile_service: ProfileService = profile_service
        self.mentor_service: MentorService = mentor_service
        self.exp_service: ExperienceService = experience_service
        self.mq_adapter: SqsMqAdapter = mq_adapter

    async def upsert_profile(self, db: AsyncSession, dto: user.ProfileDTO):
        res: user.ProfileVO = \
            await self.profile_service.upsert_profile(db, dto)
        # 若為 onboarding 狀態，則需通知 Search Service
        # if res.on_boarding:
        #     await self.service_api.post(POST_MENTOR_URL, res.to_dto_json())
            # await self.mq_adapter.publish_message(res.to_dto_json())
        return res

    async def upsert_mentor_profile(self, db: AsyncSession,
                                    profile_dto: mentor.MentorProfileDTO):
        res: mentor.MentorProfileVO = \
            await self.mentor_service.upsert_mentor_profile(db, profile_dto)
        # 若為 onboarding 狀態，則需通知 Search Service
        # if res.on_boarding:
            # await self.service_api.post(POST_MENTOR_URL, res.to_dto_json())
            # await self.mq_adapter.publish_message(res.to_dto_json())
        return res

    async def upsert_exp(self, db,
                         experience_dto: exp.ExperienceDTO,
                         user_id: int,
                         experience_type: ExperienceCategory):
        res: exp.ExperienceVO = \
            await self.exp_service.upsert_exp(db=db,
                                              experience_dto=experience_dto,
                                              user_id=user_id,
                                              exp_cate=experience_type)
        experiences: List[exp.ExperienceVO] = \
                await self.exp_service.get_exp_list_by_user_id(db, user_id)
        # 若為 onboarding 狀態，則需通知 Search Service
        if ExperienceService.is_onboarding(experiences):
            mentor_profile: mentor.MentorProfileVO = mentor.MentorProfileVO(
                user_id=user_id,
                experiences=experiences
            )
            # await self.service_api.post(POST_MENTOR_URL, mentor_profile.to_dto_json())
            # await self.mq_adapter.publish_message(mentor_profile.to_dto_json())
        return res

    async def delete_experience(self, db,
                                user_id: int,
                                experience_id: int,
                                experience_type: ExperienceCategory
                                ):
        res: bool = \
            await self.exp_service.delete_exp_by_user_and_exp_id(db=db,
                                                                 user_id=user_id,
                                                                 exp_id=experience_id,
                                                                 exp_cate=experience_type)
        experiences: List[exp.ExperienceVO] = \
                await self.exp_service.get_exp_list_by_user_id(db, user_id)
        # 若為 onboarding 狀態，則需通知 Search Service
        if ExperienceService.is_onboarding(experiences):
            mentor_profile: mentor.MentorProfileVO = mentor.MentorProfileVO(
                user_id=user_id,
                experiences=experiences
            )
            # await self.service_api.post(POST_MENTOR_URL, mentor_profile.to_dto_json())
            # await self.mq_adapter.publish_message(mentor_profile.to_dto_json())
        return res
