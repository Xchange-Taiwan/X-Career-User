import logging
from typing import List

from fastapi import (
    APIRouter,
    Header,
    Path,
    Query,
    Body,
    Depends,
    BackgroundTasks,
)
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.mentor.service.mentor_service import MentorService
from src.domain.mentor.service.schedule_service import ScheduleService
from ..res.response import *
from ..req.mentor_validation import *
from ...config.constant import *
from ...domain.mentor.model import (
    mentor_model as mentor,
    experience_model as experience,
)
from ...domain.mentor.model.mentor_model import MentorProfileVO
from ...domain.mentor.service.experience_service import ExperienceService
from ...infra.databse import get_db, db_session
from ...app.mentor_profile.upsert import MentorProfile
from ...app._di.injection import (
    get_mentor_service,
    get_experience_service,
    get_schedule_service,
    get_mentor_profile_app,
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix='/mentors',
    tags=['Mentor'],
    responses={404: {'description': 'Not found'}},
)


@router.put('/mentor_profile',
            responses=idempotent_response('upsert_mentor_profile', mentor.MentorProfileVO))
async def upsert_mentor_profile(
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        body: mentor.MentorProfileDTO = Body(...),
        mentor_profile_app: MentorProfile = Depends(get_mentor_profile_app),
):
    # TODO-EVENT: implement event
    res: mentor.MentorProfileVO = \
        await mentor_profile_app.upsert_mentor_profile(db=db, 
                                                       profile_dto=body, 
                                                       background_tasks=background_tasks)
    return res_success(data=jsonable_encoder(res))


@router.get('/{user_id}/{language}/mentor_profile',
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
    return res_success(data=jsonable_encoder(mentor_profile))


@router.get('/{user_id}/experiences',
            responses=idempotent_response('get_exp_by_user_id', experience.ExperienceListVO))
async def get_exp_by_user_id(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        exp_service: ExperienceService = Depends(get_experience_service)
):
    res: experience.ExperienceListVO = await exp_service.get_exp_by_user_id(db, user_id)
    return res_success(data=jsonable_encoder(res))


@router.put('/{user_id}/experiences/{experience_type}',
            responses=idempotent_response('upsert_exp', experience.ExperienceVO))
async def upsert_experience(
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        is_mentor: bool = Header(None),
        user_id: int = Path(...),
        experience_type: ExperienceCategory = Path(...),
        body: experience.ExperienceDTO = Body(...),
        mentor_profile_app: MentorProfile = Depends(get_mentor_profile_app),
):
    # TODO-EVENT: implement event
    body.category = experience_type
    res: experience.ExperienceVO = \
        await mentor_profile_app.upsert_exp(db=db,
                                            user_id=user_id,
                                            experience_dto=body,
                                            background_tasks=background_tasks,
                                            is_mentor=is_mentor,)
    return res_success(data=jsonable_encoder(res))


@router.delete('/{user_id}/experiences/{experience_type}/{experience_id}',
               responses=idempotent_response('delete_experience', bool))
async def delete_experience(
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        is_mentor: bool = Header(None),
        user_id: int = Path(...),
        data: experience.ExperienceDTO = Depends(delete_experience_check),
        mentor_profile_app: MentorProfile = Depends(get_mentor_profile_app),
):
    # TODO-EVENT: implement event
    res: bool = await mentor_profile_app.delete_experience(db,
                                                           user_id=user_id,
                                                           experience_dto=data,
                                                           background_tasks=background_tasks,
                                                           is_mentor=is_mentor,)
    return res_success(data=res)


@router.get(
    '/{user_id}/schedule/y/{dt_year}/m/{dt_month}',
    responses=idempotent_response('get_mentor_schedule_list', mentor.MentorScheduleQueryVO),
    summary='Get mentor schedule segments (UTC)',
    description=(
        'All schedule timestamps use Unix seconds in UTC (GMT+0). '
        'The backend returns raw schedule rules (ALLOW/FORBIDDEN with rrule/exdate) '
        'and BOOKED/PENDING segments (mentor reservations by my_status). '
        'Rrule expansion and calendar rendering are handled by the frontend. '
        'New-format ALLOW rows carry meeting_duration_minutes; (dtstart, dtend) '
        'is then the block bounds and the frontend divides locally. Legacy rows '
        'leave that field NULL and still encode division in a FREQ=MINUTELY rrule.'
    ),
)
async def get_mentor_schedule_list(
        db: AsyncSession = Depends(db_session),
        user_id: int = Path(...),
        dt_year: int = Path(..., ge=2000, le=2100),
        dt_month: int = Path(..., ge=1, le=12),
        limit: int = Query(None, ge=1),
        next_dtstart: int = Query(None),
        schedule_service: ScheduleService = Depends(get_schedule_service),
):
    res: mentor.MentorScheduleQueryVO = await schedule_service.get_schedule_list(
        db,
        user_id=user_id,
        dt_year=dt_year,
        dt_month=dt_month,
        limit=limit,
        next_dtstart=next_dtstart,
    )
    return res_success(data=res.to_json())


@router.put('/{user_id}/schedule',
            responses=idempotent_response('upsert_mentor_schedule', mentor.MentorScheduleVO))
async def upsert_mentor_schedule(
        db: AsyncSession = Depends(db_session),
        user_id: int = Path(...),
        body: mentor.MentorScheduleDTO = Depends(upsert_mentor_schedule_check),
        schedule_service: ScheduleService = Depends(get_schedule_service),
):
    res: mentor.MentorScheduleVO = await schedule_service.save_schedules(db, user_id, body)
    return res_success(data=res.to_json())


@router.delete('/{user_id}/schedule/{schedule_id}',
               responses=idempotent_response('delete_mentor_schedule', int))
async def delete_mentor_schedule(
        db: AsyncSession = Depends(db_session),
        user_id: int = Path(...),
        schedule_id: int = Path(...),
        schedule_service: ScheduleService = Depends(get_schedule_service),
):
    msg: str = await schedule_service.delete_schedule(db, user_id, schedule_id)
    return res_success(data=schedule_id, msg=msg)
