import logging as log

from fastapi import (
    APIRouter,
    Depends,
    Path, Query, Body, BackgroundTasks
)
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from ..res.response import *
from ...config.constant import *
from ...domain.user.model import (
    common_model as common,
    user_model as user,
    reservation_model as reservation,
)
from ...app.reservation.booking import Booking
from ...domain.user.service.interest_service import InterestService
from ...domain.user.service.profession_service import ProfessionService
from ...domain.user.service.profile_service import ProfileService
from ...infra.databse import get_db, db_session

from ...app._di.injection import (
    get_interest_service, 
    get_profession_service, 
    get_profile_service,
    get_reservation_service,
    get_booking_service,
)
from ...app.mentor_profile.upsert import MentorProfile
from ...app._di.injection import (
    get_interest_service,
    get_profession_service,
    get_profile_service,
    get_mentor_profile_app,

)

log.basicConfig(filemode='w', level=log.INFO)

router = APIRouter(
    prefix='/users',
    tags=['User'],
    responses={404: {'description': 'Not found'}},
)


@router.put('/profile',
            responses=idempotent_response('upsert_profile', user.ProfileVO))
async def upsert_profile(
        background_tasks: BackgroundTasks, 
        db: AsyncSession = Depends(db_session),
        body: user.ProfileDTO = Body(...),
        mentor_profile_app: MentorProfile = Depends(get_mentor_profile_app),
):
    # TODO-EVENT: implement event
    res: user.ProfileVO = await mentor_profile_app.upsert_profile(
        db, body, background_tasks
    )
    return res_success(data=jsonable_encoder(res))


@router.get('/{user_id}/{language}/profile',
            responses=idempotent_response('get_profile', user.ProfileVO))
async def get_profile(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        language: Language = Path(...),
        profile_service: ProfileService = Depends(get_profile_service)
):
    res: user.ProfileVO = await profile_service.get_by_user_id(db, user_id, language.value)
    return res_success(data=jsonable_encoder(res))


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
    return res_success(data=jsonable_encoder(res))


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
    return res_success(data=jsonable_encoder(res))


@router.get('/{user_id}/reservations',
            responses=idempotent_response('reservation_list', reservation.ReservationInfoListVO))
async def reservation_list(
        user_id: int = Path(...),
        query: reservation.ReservationQueryDTO = Query(...),
        db: AsyncSession = Depends(db_session),
        booking_service: Booking = Depends(get_booking_service),
):
    res = await booking_service.list(db, user_id, query)
    return res_success(data=jsonable_encoder(res))


############################################################################################
# NOTE: 如何改預約時段? 重新建立後再 cancel 舊的。 (status_code: 201)
# 用戶可能有很多memtor/memtee預約；為方便檢查時間衝突，要重新建立後再 cancel 舊的。
# ReservationDTO.previous_reserve 可紀錄前一次的[reserve_id]，以便找到同樣的討論串/變更原因歷史。
# 如果 "previous_reserve" 不為空，則表示這是一次變更預約的操作 => 新增後，將舊的預約設為 cancel。
############################################################################################
@router.post('/{user_id}/reservations',
             responses=post_response('new_booking', reservation.ReservationVO))
async def new_booking(
        user_id: int = Path(...),
        body: reservation.ReservationDTO = Body(...),
        db: AsyncSession = Depends(db_session),
        booking_service: Booking = Depends(get_booking_service),
):
    body.my_user_id = user_id
    body.my_status = BookingStatus.ACCEPT
    res = await booking_service.create(db, body)
    return res_success(data=jsonable_encoder(res))


@router.put('/{user_id}/reservations/{reservation_id}',
            responses=idempotent_response('update_reservation_status', reservation.ReservationVO))
async def update_reservation_status(
        user_id: int = Path(...),
        reservation_id: int = Path(...),
        body: reservation.UpdateReservationDTO = Body(...),
        db: AsyncSession = Depends(db_session),
        booking_service: Booking = Depends(get_booking_service),
):
    body.my_user_id = user_id
    res = await booking_service.update_reservation_status(db, reservation_id, body)
    return res_success(data=jsonable_encoder(res))
