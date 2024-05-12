import os
import time
import json
from typing import List, Dict, Any
from fastapi import (
    APIRouter,
    Request, Depends,
    Header, Path, Query, Body, Form
)
from sqlalchemy.orm import Session

from ...domain.user.model import (
    common_model as common,
    user_model as user,
    reservation_model as reservation,
)
from ..res.response import *
from ...config.constant import *
from ...config.exception import *
import logging as log

from ...infra.databse import get_db
from ...infra.util.injection_util import get_interest_service, get_profession_service, get_profile_service

log.basicConfig(filemode='w', level=log.INFO)

router = APIRouter(
    prefix='/users',
    tags=['User'],
    responses={404: {'description': 'Not found'}},
)


@router.put('/{user_id}/profile',
            responses=idempotent_response('upsert_profile', user.ProfileVO))
async def upsert_profile(
        db: Session = Depends(get_db),
        body: user.ProfileDTO = Body(...),
        profile_service: ProfileService = Depends(get_profile_service)
):
    # TODO: implement
    res: user.ProfileVO = await profile_service.upsert_profile(db, body)
    return res_success(data=res.json())


@router.get('/{user_id}/profile',
            responses=idempotent_response('get_profile', user.ProfileVO))
async def get_profile(
        db: Session = Depends(get_db),
        user_id: int = Path(...),
        profile_service: ProfileService = Depends(get_profile_service)
):
    res: user.ProfileVO = await profile_service.get_by_user_id(db, user_id)
    return res_success(data=res.json())


@router.get('/interests',
            responses=idempotent_response('get_interests', common.InterestListVO))
async def get_interests(
        db: Session = Depends(get_db),
        interest_service: InterestService = Depends(get_interest_service)
        # ,interest: InterestCategory = Query(...)
):
    # 需確認是不是返回全部還是可以查詢特定
    res: common.InterestListVO = await interest_service.get_all_interest(db)
    return res_success(data=res.json())


@router.get('/industries',
            responses=idempotent_response('get_industries', common.ProfessionListVO))
async def get_industries(
        db: Session = Depends(get_db),
        profession_service: ProfessionService = Depends(get_profession_service)
        # category = ProfessionCategory.INDUSTRY = Query(...),
):
    # 需確認是不是返回全部還是可以查詢特定
    res: common.ProfessionListVO = await profession_service.get_all_profession(db)
    return res_success(data=res.json())


@router.get('/{user_id}/reservations',
            responses=idempotent_response('reservation_list', reservation.ReservationListVO))
async def reservation_list(
        user_id: int = Path(...),
        state: ReservationListState = Query(...),
        batch: int = Query(...),
        next_id: int = Query(None),
):
    # TODO: implement
    return res_success(data=None)


@router.post('/{user_id}/reservations',
             responses=post_response('new_booking', reservation.ReservationVO))
async def new_booking(
        user_id: int = Path(...),
        body: reservation.ReservationDTO = Body(...),
):
    # TODO: implement
    return res_success(data=None)


@router.put('/{user_id}/reservations/{reservation_id}',
            responses=idempotent_response('update_or_delete_booking', reservation.ReservationVO))
async def update_or_delete_booking(
        user_id: int = Path(...),
        reservation_id: int = Path(...),
        body: reservation.ReservationDTO = Body(...),
):
    # TODO: implement
    return res_success(data=None)
