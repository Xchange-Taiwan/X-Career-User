import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.file.dao.file_repository import FileRepository
from src.domain.mentor.dao.canned_message_repository import CannedMessageRepository
from src.domain.mentor.dao.schedule_repository import ScheduleRepository
from src.domain.mentor.service.notify_service import NotifyService
from src.domain.user.dao.mentor_experience_repository import MentorExperienceRepository
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.dao.reservation_repository import ReservationRepository
from src.domain.user.service.delete_account_service import DeleteAccountService

log = logging.getLogger(__name__)


class DeleteAccount:
    def __init__(
        self,
        delete_account_service: DeleteAccountService,
        experience_repository: MentorExperienceRepository,
        schedule_repository: ScheduleRepository,
        canned_message_repository: CannedMessageRepository,
        reservation_repository: ReservationRepository,
        profile_repository: ProfileRepository,
        file_repository: FileRepository,
        notify_service: NotifyService,
    ):
        self.__delete_account_service = delete_account_service
        self.__experience_repo = experience_repository
        self.__schedule_repo = schedule_repository
        self.__canned_message_repo = canned_message_repository
        self.__reservation_repo = reservation_repository
        self.__profile_repo = profile_repository
        self.__file_repo = file_repository
        self.__notify_service = notify_service

    async def execute(self, db: AsyncSession, user_id: int) -> None:
        profile = await self.__profile_repo.find_by_user_id(db, user_id)
        if profile is None:
            return

        is_mentor = profile.is_mentor

        await self.__schedule_repo.delete_all_by_user_id(db, user_id)
        await self.__experience_repo.delete_all_by_user_id(db, user_id)
        await self.__canned_message_repo.delete_all_by_user_id(db, user_id)
        await self.__reservation_repo.anonymize_by_my_user_id(db, user_id)
        await self.__reservation_repo.anonymize_by_user_id(db, user_id)
        await self.__file_repo.soft_delete_all_by_user_id(db, user_id)
        await self.__profile_repo.delete_profile(db, user_id)

        await db.commit()

        if is_mentor:
            try:
                await self.__notify_service.notify_delete_mentor_profile(user_id)
            except Exception as e:
                log.error(
                    f"[DeleteAccount] SQS DELETE_MENTOR_PROFILE failed, user_id={user_id}: {e}"
                )
