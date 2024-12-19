import logging as log
from typing import List

from fastapi import (
    APIRouter,
    Path, Body, Depends
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.mentor.service.mentor_service import MentorService
from ..res.response import *
from ...config.constant import *
from ...domain.mentor.model import (
    mentor_model as mentor,
    experience_model as experience,
)
from ...domain.mentor.model.mentor_model import MentorProfileVO
from ...domain.mentor.service.experience_service import ExperienceService
from ...domain.user.model import (
    common_model as common,
)
from ...domain.user.model.common_model import ProfessionListVO
from ...domain.user.service.profession_service import ProfessionService
from ...infra.databse import get_db, db_session
from ...infra.util.injection_util import get_mentor_service, get_experience_service, get_profession_service

log.basicConfig(filemode='w', level=log.INFO)

router = APIRouter(
    prefix='/mentors',
    tags=['Mentor'],
    responses={404: {'description': 'Not found'}},
)


@router.put('/mentor_profile/create',
            responses=idempotent_response('upsert_mentor_profile', mentor.MentorProfileVO))
async def upsert_mentor_profile(
        db: AsyncSession = Depends(get_db),
        body: mentor.MentorProfileDTO = Body(...),
        mentor_service: MentorService = Depends(get_mentor_service)

):
    # TODO: implement
    res: mentor.MentorProfileVO = await mentor_service.upsert_mentor_profile(db, body)
    return res_success(data=res.model_dump_json())


@router.get('/{user_id}/{language}/profile',
            responses=idempotent_response('get_mentor_profile', MentorProfileVO))
async def get_mentor_profile(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        language: Language = Path(...),
        mentor_service: MentorService = Depends(get_mentor_service)
):
    # TODO: implement
    mentor_profile: MentorProfileVO = \
        await mentor_service.get_mentor_profile_by_id(db, user_id, language.value)

    return res_success(data=mentor_profile.model_dump_json())

@router.get('/{user_id}/experiences',
            responses=idempotent_response('get_exp_by_user_id', experience.ExperienceListVO))
async def get_exp_by_user_id(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        exp_service: ExperienceService = Depends(get_experience_service)
):
    res: experience.ExperienceListVO = await exp_service.get_exp_by_user_id(db, user_id)
    return res_success(data=res.model_dump_json())



@router.put('/{user_id}/experiences/{experience_type}',
            responses=idempotent_response('upsert_exp', experience.ExperienceVO))
async def upsert_experience(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        experience_type: ExperienceCategory = Path(...),
        body: experience.ExperienceDTO = Body(...),
        exp_service: ExperienceService = Depends(get_experience_service)
):
    res: experience.ExperienceVO = await exp_service.upsert_exp(db=db,
                                                                experience_dto=body,
                                                                user_id=user_id,
                                                                exp_cate=experience_type)
    return res_success(data=res.model_dump_json())


@router.delete('/{user_id}/experiences/{experience_type}/{experience_id}',
               responses=idempotent_response('delete_experience', bool))
async def delete_experience(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        experience_id: int = Path(...),
        experience_type: ExperienceCategory = Path(...),
        exp_service: ExperienceService = Depends(get_experience_service)
):
    res: bool = await exp_service.delete_exp_by_user_and_exp_id(db, user_id, experience_id, experience_type)

    return res_success(data=res)


@router.get('/{language}/expertises',
            responses=idempotent_response('get_expertises', common.ProfessionListVO))
async def get_expertises(
        language: Language = Path(...),
        # category = ProfessionCategory.EXPERTISE = Query(...),
        db: AsyncSession = Depends(db_session),
        profession_service: ProfessionService = Depends(get_profession_service)
):
    res: ProfessionListVO = \
        await profession_service.get_all_profession_by_category_and_language(db,
                                                                             ProfessionCategory.EXPERTISE,
                                                                             language)
    return res_success(data=res.to_json())


@router.put('/{user_id}/schedule',
            responses=idempotent_response('upsert_mentor_schedule', mentor.MentorScheduleVO))
async def upsert_mentor_schedule(
        user_id: int = Path(...),
        body: List[mentor.TimeSlotDTO] = Body(...),
):
    # TODO: implement
    return res_success(data=None)


@router.delete('/{user_id}/schedule/{schedule_id}',
               responses=idempotent_response('delete_mentor_schedule', mentor.MentorScheduleVO))
async def delete_mentor_schedule(
        user_id: int = Path(...),
        schedule_id: int = Path(...),
):
    # TODO: implement
    return res_success(data=None)
