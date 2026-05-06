# injection util
# Dependency function to create DAO instance
from fastapi import Depends

from src.domain.file.dao.file_repository import FileRepository
from src.domain.file.service.file_service import FileService
from src.domain.mentor.dao.canned_message_repository import CannedMessageRepository
from src.domain.mentor.dao.mentor_repository import MentorRepository
from src.domain.mentor.service.mentor_service import MentorService
from src.domain.mentor.service.schedule_service import ScheduleService
from src.domain.mentor.dao.schedule_repository import ScheduleRepository
from src.domain.mentor.service.notify_service import NotifyService
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.dao.reservation_repository import ReservationRepository
from src.domain.user.dao.tag_repository import TagRepository
from src.domain.user.service.delete_account_service import DeleteAccountService
from src.domain.user.dao.activity_repository import ActivityRepository
from src.domain.user.service.reservation_service import ReservationService
from src.domain.user.service.activity_service import ActivityService
from src.domain.user.service.profile_service import ProfileService
from src.domain.user.service.tag_service import TagService
from src.app.account.delete import DeleteAccount
from src.app.reservation.booking import Booking
from src.app.mentor_profile.upsert import MentorProfile
from src.infra.cache.local_cache import _local_cache
from src.infra.resource.manager import resource_manager
from src.infra.mq.sqs_mq_adapter import SqsMqAdapter
from src.infra.template.service_api import IServiceApi
from src.infra.client.async_service_api_adapter import AsyncServiceApiAdapter


def get_mentor_dao() -> MentorRepository:
    return MentorRepository()


def get_profile_dao() -> ProfileRepository:
    return ProfileRepository()


def get_file_dao() -> FileRepository:
    return FileRepository()


def get_schedule_dao() -> ScheduleRepository:
    return ScheduleRepository()


def get_reservation_dao() -> ReservationRepository:
    return ReservationRepository()


def get_activity_dao() -> ActivityRepository:
    return ActivityRepository()


def get_tag_dao() -> TagRepository:
    return TagRepository()


def get_tag_service(
    tag_repository: TagRepository = Depends(get_tag_dao),
) -> TagService:
    return TagService(tag_repository)


def get_service_api() -> IServiceApi:
    return AsyncServiceApiAdapter()

def get_sqs_mq_adapter() -> SqsMqAdapter:
    sqs_rsc = resource_manager.get("sqs_rsc")
    return SqsMqAdapter(sqs_rsc=sqs_rsc)


# Dependency function to create Service instance with DAO dependency injected


def get_profile_service(
    tag_service: TagService = Depends(get_tag_service),
    profile_repository: ProfileRepository = Depends(get_profile_dao),
) -> ProfileService:
    return ProfileService(
        tag_service=tag_service,
        profile_repository=profile_repository,
    )


def get_mentor_service(
    mentor_repository: MentorRepository = Depends(get_mentor_dao),
    profile_repository: ProfileRepository = Depends(get_profile_dao),
    profile_service: ProfileService = Depends(get_profile_service),
    tag_service: TagService = Depends(get_tag_service),
) -> MentorService:
    return MentorService(
        mentor_repository,
        profile_repository,
        profile_service,
        tag_service,
    )


def get_file_service(file_repository: FileRepository = Depends(get_file_dao)):
    return FileService(file_repository)


def get_schedule_service(
    schedule_repository: ScheduleRepository = Depends(get_schedule_dao),
):
    return ScheduleService(schedule_repository)


def get_activity_service(
    activity_repository: ActivityRepository = Depends(get_activity_dao),
    service_api: IServiceApi = Depends(get_service_api),
) -> ActivityService:
    return ActivityService(activity_repository, service_api)


def get_reservation_service(
    reservation_repository: ReservationRepository = Depends(get_reservation_dao),
    activity_service: ActivityService = Depends(get_activity_service),
):
    return ReservationService(reservation_repository, activity_service)


def get_booking_service(
    reservation_service: ReservationService = Depends(get_reservation_service),
):
    return Booking(reservation_service)


def get_notify_service(
    mentor_service: MentorService = Depends(get_mentor_service),
    mq_adapter: SqsMqAdapter = Depends(get_sqs_mq_adapter),
):
    return NotifyService(mentor_service, mq_adapter)


def get_mentor_profile_app(
    profile_service: ProfileService = Depends(get_profile_service),
    mentor_service: MentorService = Depends(get_mentor_service),
    notify_service: NotifyService = Depends(get_notify_service),
):
    return MentorProfile(profile_service, mentor_service, notify_service)


def get_canned_message_dao() -> CannedMessageRepository:
    return CannedMessageRepository()


def get_delete_account_service(
    reservation_repository: ReservationRepository = Depends(get_reservation_dao),
) -> DeleteAccountService:
    return DeleteAccountService(reservation_repository)


def get_delete_account_app(
    delete_account_service: DeleteAccountService = Depends(get_delete_account_service),
    schedule_repository: ScheduleRepository = Depends(get_schedule_dao),
    canned_message_repository: CannedMessageRepository = Depends(get_canned_message_dao),
    reservation_repository: ReservationRepository = Depends(get_reservation_dao),
    profile_repository: ProfileRepository = Depends(get_profile_dao),
    file_repository: FileRepository = Depends(get_file_dao),
    notify_service: NotifyService = Depends(get_notify_service),
) -> DeleteAccount:
    return DeleteAccount(
        delete_account_service,
        schedule_repository,
        canned_message_repository,
        reservation_repository,
        profile_repository,
        file_repository,
        notify_service,
    )
