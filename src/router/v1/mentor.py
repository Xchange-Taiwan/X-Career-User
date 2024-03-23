import os
import time
import json
from typing import List, Dict, Any
from fastapi import (
    APIRouter,
    Request, Depends,
    Header, Path, Query, Body, Form
)
from ...domain.mentor.model import (
    mentor_model as mentor,
    experience_model as experience,
)
from ...domain.user.model import (
    common_model as common,
)
from ..res.response import *
from ...config.conf import *
from ...config.constant import *
from ...config.exception import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


router = APIRouter(
    prefix='/users',
    tags=['Mentor'],
    responses={404: {'description': 'Not found'}},
)


@router.put('/{user_id}/mentor-profile',
            responses=idempotent_response('upsert_mentor_profile', mentor.MentorProfileVO))
async def upsert_mentor_profile(
    user_id: int = Path(...),
    body: mentor.MentorProfileDTO = Body(...),
):
    # TODO: implement
    return res_success(data=None)


@router.get('/{user_id}/mentor-profile',
            responses=idempotent_response('get_mentor_profile', mentor.MentorProfileVO))
async def get_mentor_profile(
    user_id: int = Path(...),
):
    # TODO: implement
    return res_success(data=None)


@router.put('/{user_id}/experiences/{experience_type}',
            responses=idempotent_response('upsert_experience', experience.ExperienceVO))
async def upsert_experience(
    user_id: int = Path(...),
    experience_type: ExperienceCategory = Path(...),
    body: experience.ExperienceDTO = Body(...),
):
    # TODO: implement
    return res_success(data=None)


@router.delete('/{user_id}/experiences/{experience_type}/{experience_id}',
               responses=idempotent_response('delete_experience', experience.ExperienceVO))
async def delete_experience(
    user_id: int = Path(...),
    experience_id: int = Path(...),
    experience_type: ExperienceCategory = Path(...),
):
    # TODO: implement
    return res_success(data=None)


@router.get('/expertises',
            responses=idempotent_response('get_expertises', common.ProfessionListVO))
async def get_expertises(
    # category = ProfessionCategory.EXPERTISE = Query(...),
):
    # TODO: implement
    return res_success(data=None)


@router.put('/{user_id}/mentor-schedule',
            responses=idempotent_response('upsert_mentor_schedule', mentor.MentorScheduleVO))
async def upsert_mentor_schedule(
    user_id: int = Path(...),
    body: List[mentor.TimeSlotDTO] = Body(...),
):
    # TODO: implement
    return res_success(data=None)


@router.delete('/{user_id}/mentor-schedule/{schedule_id}',
               responses=idempotent_response('delete_mentor_schedule', mentor.MentorScheduleVO))
async def delete_mentor_schedule(
    user_id: int = Path(...),
    schedule_id: int = Path(...),
):
    # TODO: implement
    return res_success(data=None)
