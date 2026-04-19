import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.conf import AUTH_SERVICE_URL
from src.config.constant import ActivityStatus, RoleType
from src.domain.user.dao.activity_repository import ActivityRepository
from src.infra.client.async_service_api_adapter import _async_service_api_adapter
from src.infra.db.orm.init.user_init import Activity

log = logging.getLogger(__name__)

CALENDAR_EVENTS_PATH = '/v1/calendar/events'


class ActivityService:
    def __init__(self, activity_repository: ActivityRepository):
        self.activity_repo = activity_repository

    async def create_google_event_and_schedule_activity(
        self,
        db: AsyncSession,
        mentor_reservation_id: int,
        mentee_reservation_id: int,
        start_time: int,
        end_time: int,
        user_ids: List[int],
        summary: str = 'XChange X-Talent Appointment',
        description: str = '',
    ) -> Optional[Activity]:
        try:
            exists = await self.activity_repo.find_by_reservation_id_and_role(
                db,
                mentor_reservation_id,
                RoleType.MENTOR,
            )
            if exists:
                return exists

            payload = {
                'summary': summary,
                'description': description,
                'start_time': str(start_time),
                'end_time': str(end_time),
                'user_ids': user_ids,
            }
            url = f'{AUTH_SERVICE_URL}{CALENDAR_EVENTS_PATH}'
            data = await _async_service_api_adapter.simple_post(url=url, json=payload)
            if not data or not data.get('event_id'):
                log.error('create google event fail: invalid response data=%s', data)
                return None

            event_id = data.get('event_id')
            log.info(
                'create google event success: event_id=%s, mentor_reservation_id=%s, mentee_reservation_id=%s',
                event_id,
                mentor_reservation_id,
                mentee_reservation_id,
            )
            await self.activity_repo.create_scheduled(
                db,
                event_id=event_id,
                mentor_reservation_id=mentor_reservation_id,
                mentee_reservation_id=mentee_reservation_id,
            )
            return await self.activity_repo.find_by_reservation_id_and_role(
                db,
                mentor_reservation_id,
                RoleType.MENTOR,
            )
        except Exception as e:
            log.error('create google event and schedule activity fail: %s', str(e))
            return None

    async def cancel_google_event_and_cancel_activity(
        self,
        db: AsyncSession,
        reservation_id: int,
        role: RoleType,
    ) -> bool:
        try:
            activity = await self.activity_repo.find_by_reservation_id_and_role(
                db,
                reservation_id,
                role,
            )
            if not activity:
                return False

            if activity.status != ActivityStatus.SCHEDULED:
                return False

            url = f'{AUTH_SERVICE_URL}{CALENDAR_EVENTS_PATH}/{activity.id}'
            await _async_service_api_adapter.simple_delete(url=url)
            log.info(
                'cancel google event success: event_id=%s, reservation_id=%s, role=%s',
                activity.id,
                reservation_id,
                role,
            )
            await self.activity_repo.update_to_cancelled(db, event_id=activity.id)
            return True
        except Exception as e:
            log.error('cancel google event and cancel activity fail: %s', str(e))
            return False
