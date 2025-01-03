# injection util
# Dependency function to create DAO instance
from fastapi import Depends

from src.domain.file.dao.file_repository import FileRepository
from src.domain.file.service.file_service import FileService
from src.domain.mentor.dao.profession_repository import ProfessionRepository
from src.domain.mentor.dao.interest_repository import InterestRepository
from src.domain.mentor.dao.mentor_repository import MentorRepository
from src.domain.mentor.service.experience_service import ExperienceService
from src.domain.mentor.service.mentor_service import MentorService
from src.domain.mentor.service.schedule_service import ScheduleService
from src.domain.mentor.dao.schedule_repository import ScheduleRepository
from src.domain.mentor.service.notify_service import NotifyService
from src.domain.user.dao.mentor_experience_repository import MentorExperienceRepository
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.dao.reservation_repository import ReservationRepository
from src.domain.user.service.reservation_service import ReservationService
from src.domain.user.service.interest_service import InterestService
from src.domain.user.service.profession_service import ProfessionService
from src.domain.user.service.profile_service import ProfileService
from src.app.reservation.booking import Booking
from src.app.mentor_profile.upsert import MentorProfile
from src.infra.cache.local_cache import _local_cache
from src.infra.resource.manager import resource_manager
from src.infra.mq.sqs_mq_adapter import SqsMqAdapter


def get_experience_dao() -> MentorExperienceRepository:
    return MentorExperienceRepository()


def get_mentor_dao() -> MentorRepository:
    return MentorRepository()


def get_interest_dao() -> InterestRepository:
    return InterestRepository()


def get_profile_dao() -> ProfileRepository:
    return ProfileRepository()


def get_profession_dao() -> ProfessionRepository:
    return ProfessionRepository()


def get_file_dao() -> FileRepository:
    return FileRepository()


def get_schedule_dao() -> ScheduleRepository:
    return ScheduleRepository()


def get_resevation_dao() -> ReservationRepository:
    return ReservationRepository()


def get_sqs_mq_adapter() -> SqsMqAdapter:
    sqs_rsc = resource_manager.get("sqs_rsc")
    return SqsMqAdapter(sqs_rsc=sqs_rsc)


def get_interest_service(
    interest_repo: InterestRepository = Depends(get_interest_dao),
) -> InterestService:
    return InterestService(interest_repo, _local_cache)


def get_profession_service(
    profession_repository: ProfessionRepository = Depends(get_profession_dao),
) -> ProfessionService:
    return ProfessionService(profession_repository, _local_cache)


def get_experience_service(
    experience_repository: MentorExperienceRepository = Depends(get_experience_dao),
) -> ExperienceService:
    return ExperienceService(experience_repository)


# Dependency function to create Service instance with DAO dependency injected


def get_profile_service(
    interest_service: InterestService = Depends(get_interest_service),
    profession_service: ProfessionService = Depends(get_profession_service),
    experience_service: ExperienceService = Depends(get_experience_service),
    profile_repository: ProfileRepository = Depends(get_profile_dao),
) -> ProfileService:
    return ProfileService(
        interest_service=interest_service,
        profession_service=profession_service,
        experience_service=experience_service,
        profile_repository=profile_repository,
    )


def get_mentor_service(
    mentor_repository: MentorRepository = Depends(get_mentor_dao),
    profile_repository: ProfileRepository = Depends(get_profile_dao),
    interest_service: InterestService = Depends(get_interest_service),
    profession_service: ProfessionService = Depends(get_profession_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> MentorService:
    return MentorService(
        mentor_repository,
        profile_repository,
        interest_service,
        profession_service,
        profile_service,
    )


def get_file_service(file_repository: FileRepository = Depends(get_file_dao)):
    return FileService(file_repository)


def get_schedule_service(
    schedule_repository: ScheduleRepository = Depends(get_schedule_dao),
):
    return ScheduleService(schedule_repository)


def get_reservation_service(
    reservation_repository: ReservationRepository = Depends(get_resevation_dao),
):
    return ReservationService(reservation_repository)


def get_booking_service(
    reservation_service: ReservationService = Depends(get_reservation_service),
):
    return Booking(reservation_service)


def get_notify_service(
    mentor_service: MentorService = Depends(get_mentor_service),
    experience_service: ExperienceService = Depends(get_experience_service),
    mq_adapter: SqsMqAdapter = Depends(get_sqs_mq_adapter),
):
    return NotifyService(mentor_service, experience_service, mq_adapter)


def get_mentor_profile_app(
    profile_service: ProfileService = Depends(get_profile_service),
    mentor_service: MentorService = Depends(get_mentor_service),
    experience_service: ExperienceService = Depends(get_experience_service),
    notify_service: NotifyService = Depends(get_notify_service),
):
    return MentorProfile(
        profile_service, mentor_service, experience_service, notify_service
    )
