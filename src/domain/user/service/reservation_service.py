from datetime import datetime
from fastapi.encoders import jsonable_encoder
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.user.model.reservation_model import *
from src.domain.user.dao.reservation_repository import ReservationRepository
from src.domain.user.service.activity_service import ActivityService
from src.domain.mentor.dao.schedule_repository import ScheduleRepository
from src.config.conf import BATCH, DATETIME_FORMAT
from src.config.constant import ScheduleType
from src.config.exception import *
from src.infra.db.orm.init.user_init import MentorSchedule
from src.infra.util.time_util import (
    create_calendar_with_rrule,
    rrule_events,
)
import logging

log = logging.getLogger(__name__)


def _is_legal_sub_slot(
    schedule: MentorSchedule,
    dtstart: int,
    dtend: int,
) -> bool:
    # Decide whether a (dtstart, dtend) pair lines up with one of the schedule's
    # real sub-slots. Two formats coexist:
    #   - New format: meeting_duration_minutes is set; (schedule.dtstart,
    #     schedule.dtend) is the whole block, sub-slots = block divided by
    #     meeting_duration_minutes. Pre-Phase 5 there's no rrule on these rows;
    #     when weekly recurrence ships, this branch needs to also iterate
    #     rrule occurrences.
    #   - Legacy: rrule encodes FREQ=MINUTELY sub-slot iteration; each
    #     occurrence IS one sub-slot of length (schedule.dtend-schedule.dtstart).
    if dtend <= dtstart or dtstart < int(schedule.dtstart):
        return False

    # exdate currently means "sub-slot starts the mentor excluded". Phase 5
    # weekly recurrence will repurpose it for block-start exclusions; that
    # branch will need its own handling here.
    exdate = [int(x) for x in (schedule.exdate or []) if x is not None]
    if dtstart in exdate:
        return False

    mdm = schedule.meeting_duration_minutes
    if mdm and mdm > 0:
        slot_sec = mdm * 60
        if (dtend - dtstart) != slot_sec:
            return False
        if schedule.rrule:
            # Phase 5 (weekly) hasn't shipped yet — refuse to validate
            # something we don't know how to expand. Better to reject a real
            # booking than silently let an invalid one through.
            log.warning(
                'reservation slot validation refused: schedule %s has rrule '
                'in new format which is not yet supported',
                getattr(schedule, 'id', '?'),
            )
            return False
        if dtend > int(schedule.dtend):
            return False
        return (dtstart - int(schedule.dtstart)) % slot_sec == 0

    # Legacy path: each rrule occurrence is one sub-slot.
    first_slot_sec = int(schedule.dtend) - int(schedule.dtstart)
    if (dtend - dtstart) != first_slot_sec:
        return False
    if not schedule.rrule:
        return dtstart == int(schedule.dtstart)
    try:
        calendar = create_calendar_with_rrule(
            event_title='SCHEDULE',
            start_date=datetime.fromtimestamp(int(schedule.dtstart)),
            end_date=datetime.fromtimestamp(int(schedule.dtend)),
            dt_format=DATETIME_FORMAT,
            rrule=schedule.rrule,
        )
        events = rrule_events(
            calendar,
            datetime.fromtimestamp(dtstart - 1),
            datetime.fromtimestamp(dtend + 1),
        )
        return any(
            int(event.get('DTSTART').dt.timestamp()) == dtstart
            for event in events
        )
    except Exception as expand_err:
        log.warning(
            'reservation slot validation: rrule expansion failed for schedule '
            '%s: %s',
            getattr(schedule, 'id', '?'), expand_err,
        )
        return False


def _has_forbidden_overlap(
    forbidden_rows: List[MentorSchedule],
    dtstart: int,
    dtend: int,
) -> bool:
    # FORBIDDEN rows shadow ALLOW sub-slots: any time-overlap means the slot
    # is closed. Most FORBIDDEN rows are simple one-offs, but we honour rrule
    # too in case a mentor sets a recurring "lunch break" or similar.
    for f in forbidden_rows:
        f_start = int(f.dtstart)
        f_end = int(f.dtend)
        if not f.rrule:
            if f_start < dtend and f_end > dtstart:
                return True
            continue
        try:
            cal = create_calendar_with_rrule(
                event_title='FORBIDDEN',
                start_date=datetime.fromtimestamp(f_start),
                end_date=datetime.fromtimestamp(f_end),
                dt_format=DATETIME_FORMAT,
                rrule=f.rrule,
            )
            events = rrule_events(
                cal,
                datetime.fromtimestamp(dtstart),
                datetime.fromtimestamp(dtend),
            )
            for event in events:
                fs = int(event.get('DTSTART').dt.timestamp())
                fe = int(event.get('DTEND').dt.timestamp())
                if fs < dtend and fe > dtstart:
                    return True
        except Exception as expand_err:
            log.warning(
                'forbidden row %s rrule expansion failed: %s',
                getattr(f, 'id', '?'), expand_err,
            )
            # Fail-open here would let a booking slip past a misconfigured
            # FORBIDDEN; fail-closed would block valid bookings. We choose
            # fail-closed because the alternative is data loss for the mentor.
            return True
    return False


class ReservationService:
    def __init__(self,
                 reservation_repository: ReservationRepository,
                 activity_service: ActivityService,
                 schedule_repository: ScheduleRepository,
                 ):
        self.reservation_repo = reservation_repository
        self.activity_service = activity_service
        self.schedule_repo = schedule_repository
        self.user_repo = None

    async def get_reservations(self, db: AsyncSession,
                               user_id: int,
                               query_dto: ReservationQueryDTO) -> Optional[ReservationInfoListVO]:
        try:
            res: ReservationInfoListVO = ReservationInfoListVO()
            query_dto.batch += 1
            reservations: List[ReservationInfoVO] = \
                await self.reservation_repo.get_user_reservations(db,
                                                                  user_id,
                                                                  query_dto)
            if len(reservations) < query_dto.batch:
                res.reservations = reservations
            else:
                res.reservations = reservations[:-1]
                res.next_dtend = reservations[-1].dtend
            return res
        except Exception as e:
            log.error('get reservations failed: %s', str(e))
            raise_http_exception(e=e, msg='get reservations failed')

    '''
    - reservation_dto 包含兩資訊: sender, participant
    - 對 sender 來說 accept 可能是新建(沒id) 也可以是更新狀態(有id)
    - 若 sender 為新建(沒id)，則檢查時間衝突；若 sender 為更新狀態(有id)，則不需檢查時間衝突
    - 對 participant 來說 accept 可能是新建(沒id) 也可以是更新狀態(有id)
    - 若 participant 為新建(沒id)，不需檢查時間衝突，因為預設狀態為 'PENDING'；
      若 participant 為更新狀態(有id)，也不需檢查時間衝突
    1. sender 沒id? 檢查時間衝突，若有衝突，則拋出異常
    2. 新建/更新 sender 狀態
    3. 新建/更新 participant 狀態
    '''
    async def create(self,
                     db: AsyncSession,
                     reservation_dto: ReservationDTO
                     ) -> Optional[ReservationVO]:
        try:
            # Verify the (schedule_id, dtstart, dtend) the client sent really
            # corresponds to a bookable sub-slot. Without this, frontend cache
            # staleness, race conditions, or hand-crafted requests can book a
            # slot that the mentor never opened (or already closed).
            await self.validate_slot_available(db, reservation_dto)

            # NOTE: check date conflict with sender's reservations;
            # checking participant's reservations is not necessary,
            # the default status is 'PENDING'
            await self.check_my_accepted_bookings(db, reservation_dto)

            # 检查是否已存在相同的预订
            await self.check_duplicate_reservation(db, reservation_dto)

            # sender 這次的新預約
            sender: Reservation = \
                reservation_dto.sender_model(BookingStatus.ACCEPT)
            # sender.id = None

            # participant 這次的新預約
            participant: Reservation = \
                reservation_dto.participant_model(BookingStatus.ACCEPT)
            # participant.id = None

            await self.reservation_repo.save_all(db, [
                sender,
                participant,
            ])

            return ReservationVO.from_model(sender)

        except Exception as e:
            log.error('create reservation failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'create reservation failed')
            raise_http_exception(e=e, msg=err_msg)


    '''
    - 和 accept 一樣，但多了一步: 拒絕前一次的預約
    - 前一次的預約是根據 reservation_dto 的 previous_reserve 來找到的
    - sender 的 previous_reserve 是前一次的 reserve_id, user_id,...等資訊
    - 根據 previous_reserve 找到 sender 的前一次的預約，並將其狀態設為 'REJECT'
    - participant 那邊的資訊得間接靠 sender 找到:
        - 先透過 previous_reserve 找到對應的 sender 上一次的預約
        - 再透過 sender 上一次的預約找到對應的 participant 上一次的預約
    '''
    async def create_new_and_reject_previous(self,
                                             db: AsyncSession,
                                             reservation_dto: ReservationDTO
                                             ) -> Optional[ReservationVO]:
        try:
            # Same slot validation as `create` — reschedule still needs to land
            # on a real, currently-open sub-slot.
            await self.validate_slot_available(db, reservation_dto)

            # NOTE: check date conflict with sender's reservations;
            # checking participant's reservations is not necessary,
            # the default status is 'PENDING'
            await self.check_my_accepted_bookings(db, reservation_dto)

            # 检查是否已存在相同的预订
            await self.check_duplicate_reservation(db, reservation_dto)

            # sender 這次的新預約
            sender: Reservation = \
                reservation_dto.sender_model(BookingStatus.ACCEPT)
            # sender.id = None

            # participant 這次的新預約
            participant: Reservation = \
                reservation_dto.participant_model(BookingStatus.ACCEPT)
            # participant.id = None

            # sender 的上一次預約
            PREV_SENDER_VO: ReservationVO = \
                await self.get_prev_sender_vo(db, reservation_dto)
            prev_sender: Reservation = \
                PREV_SENDER_VO.sender_model(BookingStatus.REJECT,
                                             PREV_SENDER_VO.id)

            # participant 的上一次預約
            prev_participant_vo: ReservationVO = \
                await self.get_prev_participant_vo(db, PREV_SENDER_VO)
            prev_participant: Reservation = \
                PREV_SENDER_VO.participant_model(BookingStatus.REJECT,
                                                  prev_participant_vo.id)

            # NOTE: 紀錄 participant 的上一次預約!!!!!!!!
            participant.previous_reserve = {
                'reserve_id': prev_participant.id,
            }

            await self.reservation_repo.save_all(db, [
                sender,
                prev_sender,
                participant,
                prev_participant,
            ])

            try:
                await self.activity_service.cancel_google_event_and_cancel_activity(
                    db,
                    reservation_id=PREV_SENDER_VO.id,
                    role=PREV_SENDER_VO.my_role,
                )
            except Exception as side_effect_error:
                log.error('cancel google event for previous reservation fail: %s', str(side_effect_error))

            return ReservationVO.from_model(sender)

        except Exception as e:
            log.error('create_and_cancel reservation failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'create_and_cancel reservation failed')
            raise_http_exception(e=e, msg=err_msg)

    '''
    - reject 表示已有資料，只需更新狀態即可；若無資料，則拋出異常
    - 因為 reject 是更新狀態，所以不需要檢查時間衝突
    - reservation_dto 包含兩資訊: sender, participant
    1. 確認 sender 是否存在? 若否，則拋出異常
    2. 確認 participant 是否存在? 若否，則拋出異常
    3. 若 sender 存在，則更新狀態
    4. 若 participant 存在，則更新狀態
    '''

    # FIXME: function 改為 update_reservation_status, 有 id
    async def update_reservation_status(self,
                                        db: AsyncSession,
                                        reserve_id: int,
                                        update_dto: UpdateReservationDTO
                                        ) -> Optional[ReservationVO]:
        try:
            # 當 ACCEPT 時，檢查時間衝突
            MY_STATUS = update_dto.my_status
            if MY_STATUS == BookingStatus.ACCEPT:
                await self.check_my_accepted_bookings(db, update_dto)

            SENDER_VO: ReservationVO = \
                await self.get_sender_vo_by_id(db, reserve_id, update_dto)
            participant_vo: ReservationVO = \
                await self.get_participant_vo(db, update_dto)

            sender: Reservation = \
                SENDER_VO.sender_model(MY_STATUS, SENDER_VO.id)
            participant: Reservation = \
                SENDER_VO.participant_model(MY_STATUS, participant_vo.id)

            # SENDER_VO 已經取得歷史訊息，可以直接 insert 新訊息，更新狀態
            self.append_new_message(update_dto, sender)
            await self.reservation_repo.save_all(db, [
                sender,
                participant,
            ])

            try:
                # 雙方皆 ACCEPT 時建立 Google event
                if sender.my_status == BookingStatus.ACCEPT and sender.status == BookingStatus.ACCEPT:
                    mentor_reservation_id, mentee_reservation_id = self.get_activity_pair_ids(sender, participant)
                    await self.activity_service.create_google_event_and_schedule_activity(
                        db=db,
                        mentor_reservation_id=mentor_reservation_id,
                        mentee_reservation_id=mentee_reservation_id,
                        start_time=sender.dtstart,
                        end_time=sender.dtend,
                        user_ids=[sender.my_user_id, sender.user_id],
                    )
            except Exception as side_effect_error:
                log.error('create google event fail: %s', str(side_effect_error))

            try:
                # 本次狀態為 REJECT 時，若活動存在且為 SCHEDULED，則取消
                if MY_STATUS == BookingStatus.REJECT:
                    await self.activity_service.cancel_google_event_and_cancel_activity(
                        db,
                        reservation_id=reserve_id,
                        role=SENDER_VO.my_role,
                    )
            except Exception as side_effect_error:
                log.error('cancel google event fail: %s', str(side_effect_error))
                
            return ReservationVO.from_model(sender)

        except Exception as e:
            log.error('update reservation status failed: %s', str(e))
            err_msg = getattr(e, 'msg', 'update reservation status failed')
            raise_http_exception(e=e, msg=err_msg)

    def append_new_message(self,
                           update_dto: UpdateReservationDTO,
                           sender: Reservation,
                           ):
        NEW_MESSAGES = update_dto.messages
        if len(NEW_MESSAGES) and \
            isinstance(NEW_MESSAGES[0], Dict) and \
            isinstance(sender.messages, List):
            sender.messages.insert(0, NEW_MESSAGES[0])

    def get_activity_pair_ids(self,
                              sender: Reservation,
                              participant: Reservation,
                              ) -> Tuple[int, int]:
        if sender.my_role == RoleType.MENTOR:
            return sender.id, participant.id
        return participant.id, sender.id

    async def validate_slot_available(
        self,
        db: AsyncSession,
        reservation_dto: ReservationDTO,
    ):
        # Authoritative server-side check that (schedule_id, dtstart, dtend)
        # is a real bookable sub-slot for this mentor at this moment. The
        # frontend already filters by exdate / FORBIDDEN / BOOKED before
        # rendering chips, but never re-verifies on submit; without this,
        # a stale cache or a hand-crafted POST can book a slot that the
        # mentor never opened (or already closed). Race-safe overbooking
        # is also enforced at the DB layer via the partial unique index on
        # (my_user_id, schedule_id, dtstart, dtend) WHERE my_role='MENTOR'.
        schedule = await self.schedule_repo.get_by_id(
            db, reservation_dto.schedule_id,
        )
        if not schedule:
            raise ClientException(msg='schedule not found')

        mentor_id = (
            reservation_dto.user_id
            if reservation_dto.my_role == RoleType.MENTEE
            else reservation_dto.my_user_id
        )
        if int(schedule.user_id) != int(mentor_id):
            raise ClientException(msg='schedule does not belong to this mentor')
        if schedule.dt_type != ScheduleType.ALLOW.value:
            raise ClientException(msg='schedule is not bookable')

        if not _is_legal_sub_slot(
            schedule, int(reservation_dto.dtstart), int(reservation_dto.dtend),
        ):
            raise ClientException(
                msg='requested slot does not match the mentor schedule',
            )

        forbidden_rows = await self.schedule_repo.get_forbidden_for_user(
            db, int(mentor_id),
        )
        if _has_forbidden_overlap(
            forbidden_rows,
            int(reservation_dto.dtstart),
            int(reservation_dto.dtend),
        ):
            raise ClientException(msg='requested slot is unavailable')

        existing = await self.reservation_repo.find_active_for_mentor_slot(
            db,
            mentor_user_id=int(mentor_id),
            schedule_id=int(reservation_dto.schedule_id),
            dtstart=int(reservation_dto.dtstart),
            dtend=int(reservation_dto.dtend),
        )
        if existing:
            raise ClientException(msg='requested slot is already booked')


    '''
    Check my bookings with a status: "ACCEPT"
    '''

    async def check_my_accepted_bookings(self, db: AsyncSession, reservation_dto: ReservationDTO):
        dtstart = reservation_dto.dtstart
        dtend = reservation_dto.dtend
        query: Dict = {
            'my_user_id': reservation_dto.my_user_id,
            'my_status': BookingStatus.ACCEPT,
        }

        # check sender's reservations
        sender_reserve_list: Optional[List[ReservationDTO]] = \
            await self.reservation_repo.find_all(db, query, dtstart, dtend)

        if len(sender_reserve_list) > 0:
            sender_reserve_dict = {idx+1: jsonable_encoder(r) for idx, r in enumerate(sender_reserve_list)}
            raise ClientException(msg='reservation conflict',
                                  data=sender_reserve_dict)

        # checking participant's reservations is not necessary,
        # the default status is 'PENDING'

    async def check_duplicate_reservation(self, db: AsyncSession, reservation_dto: ReservationDTO):
        # 检查是否已存在完全相同的预订记录
        # 取消後 row 仍保留並標記為 REJECT，需排除掉才能讓使用者重訂同一時段
        try:
            existing_reservation = await self.reservation_repo.find_active_duplicate(
                db,
                schedule_id=reservation_dto.schedule_id,
                dtstart=reservation_dto.dtstart,
                dtend=reservation_dto.dtend,
                my_user_id=reservation_dto.my_user_id,
                user_id=reservation_dto.user_id,
            )

            if existing_reservation:
                raise ClientException(msg='Duplicate reservation already exists')

        except Exception as e:
            if isinstance(e, ClientException):
                raise e
            log.error('check duplicate reservation failed: %s', str(e))
            raise ClientException(msg='check duplicate reservation failed')

    async def get_sender_vo_by_id(self, db: AsyncSession,
                                  reserve_id: int,
                                  update_dto: UpdateReservationDTO) -> Optional[ReservationVO]:
        my_user_id = update_dto.my_user_id
        SENDER_VO: ReservationVO = \
            await self.reservation_repo.find_by_id(db, reserve_id, my_user_id)
        if not SENDER_VO:
            log.error('sender reservation not found, reserve_id: %s', reserve_id)
            raise ClientException(msg='sender reservation not found')

        return SENDER_VO

    async def get_participant_vo(self, db: AsyncSession,
                                 update_dto: UpdateReservationDTO) -> Optional[ReservationVO]:
        p_query = update_dto.participant_query()
        participant_vo: ReservationVO = \
            await self.reservation_repo.find_one(db, p_query)
        if not participant_vo:
            log.error('participant reservation not found, query: %s', p_query)
            raise ClientException(msg='participant reservation not found')

        return participant_vo

    async def get_prev_sender_vo(self, db: AsyncSession,
                                 reservation_dto: ReservationDTO) -> Optional[ReservationVO]:
        # sender reserve_id 在 reservation_dto.previous_reserve 中
        (reserve_id, my_user_id) = reservation_dto.previous_sender_query_by_id()
        prev_sender_vo: ReservationVO = \
            await self.reservation_repo.find_by_id(db, reserve_id, my_user_id)

        if not prev_sender_vo:
            log.error('previous sender reservation not found, \
                reserve_id: %s', reserve_id)
            raise ClientException(msg=f'previous sender reservation not found: {reserve_id}')

        return prev_sender_vo

    async def get_prev_participant_vo(self, db: AsyncSession,
                                      prev_sender_vo: ReservationVO) -> Optional[ReservationVO]:
        p_query = prev_sender_vo.participant_query()
        prev_participant_vo: ReservationVO = \
            await self.reservation_repo.find_one(db, p_query)

        if not prev_participant_vo:
            log.error('previous participant reservation not found, \
                    query: %s', p_query)
            raise ClientException(msg='previous participant reservation not found')

        return prev_participant_vo


class ScaleOutReservationService:
    pass


class CrossRegionReservationService:
    pass
