import logging as log

from fastapi import (
    APIRouter,
    Depends,
    Path, Query, Body
)
from sqlalchemy.ext.asyncio import AsyncSession

from ..res.response import *
from ...config.constant import *
from ...domain.user.model import (
    common_model as common,
    user_model as user,
    reservation_model as reservation,
)
from ...domain.user.service.interest_service import InterestService
from ...domain.user.service.profession_service import ProfessionService
from ...domain.user.service.profile_service import ProfileService
from ...infra.databse import get_db, db_session
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
        db: AsyncSession = Depends(db_session),
        body: user.ProfileDTO = Body(...),
        profile_service: ProfileService = Depends(get_profile_service)
):
    res: user.ProfileVO = await profile_service.upsert_profile(db, body)
    return res_success(data=res.dict())


@router.get('/{user_id}/{language}/profile',
            responses=idempotent_response('get_profile', user.ProfileVO))
async def get_profile(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        language: Language = Path(...),
        profile_service: ProfileService = Depends(get_profile_service)
):
    res: user.ProfileVO = await profile_service.get_by_user_id(db, user_id, language.value)
    return res_success(data=res.dict())


@router.get('/{language}/interests',
            responses=idempotent_response('get_interests', common.InterestListVO))
async def get_interests(
        language: Language = Path(...),
        interest: InterestCategory = Query(...),
        db: AsyncSession = Depends(db_session),
        interest_service: InterestService = Depends(get_interest_service)
):
    # 需確認是不是返回全部還是可以查詢特定
    res: common.InterestListVO = await interest_service.get_all_interest(db, interest, language)
    return res_success(data=res.to_json())


@router.get('/{language}/industries',
            responses=idempotent_response('get_industries', common.ProfessionListVO))
async def get_industries(
        language: Language = Path(...),
        # category = ProfessionCategory.INDUSTRY = Query(...),
        db: AsyncSession = Depends(db_session),
        profession_service: ProfessionService = Depends(get_profession_service)
):
    # 需確認是不是返回全部還是可以查詢特定
    res: common.ProfessionListVO = \
        await profession_service.get_all_profession_by_category_and_language(db,
                                                                             ProfessionCategory.INDUSTRY,
                                                                             language)
    return res_success(data=res.to_json())


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
