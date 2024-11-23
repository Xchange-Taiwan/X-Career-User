#injection util
# Dependency function to create DAO instance
from fastapi import Depends

from src.domain.file.dao.file_repository import FileRepository
from src.domain.file.service.file_service import FileService
from src.domain.mentor.dao.profession_repository import ProfessionRepository
from src.domain.mentor.dao.interest_repository import InterestRepository
from src.domain.mentor.dao.mentor_repository import MentorRepository
from src.domain.mentor.service.experience_service import ExperienceService
from src.domain.mentor.service.mentor_service import MentorService
from src.domain.user.dao.mentor_experience_repository import MentorExperienceRepository
from src.domain.user.dao.profile_repository import ProfileRepository
from src.domain.user.service.interest_service import InterestService
from src.domain.user.service.profession_service import ProfessionService
from src.domain.user.service.profile_service import ProfileService


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


def get_interest_service(interest_repo: InterestRepository = Depends(get_interest_dao)) -> InterestService:
    return InterestService(interest_repo)


def get_profession_service(
        profession_repository: ProfessionRepository = Depends(get_profession_dao)) -> ProfessionService:
    return ProfessionService(profession_repository)


def get_experience_service(
        experience_repository: MentorExperienceRepository = Depends(get_experience_dao)) -> ExperienceService:
    return ExperienceService(experience_repository)


# Dependency function to create Service instance with DAO dependency injected
def get_mentor_service(mentor_repository: MentorRepository = Depends(get_mentor_dao),
                       profile_repository: ProfileRepository = Depends(get_profile_dao),
                       interest_service: InterestService = Depends(get_interest_service),
                       profession_service: ProfessionService = Depends(get_profession_service)
                       ) -> MentorService:
    return MentorService(mentor_repository, profile_repository, interest_service, profession_service, )


def get_profile_service(interest_service: InterestService = Depends(get_interest_service),
                        profession_service: ProfessionService = Depends(get_profession_service),
                        profile_repository: ProfileRepository = Depends(get_profile_dao)) -> ProfileService:
    return ProfileService(interest_service=interest_service, profession_service=profession_service,
                          profile_repository=profile_repository)


def get_interest_service(interest_dao: InterestRepository = Depends(get_interest_dao)):
    return InterestService(interest_dao)


def get_profession_service(profession_repository: ProfessionRepository = Depends(get_profession_dao)):
    return ProfessionService(profession_repository)


def get_file_service(file_repository: FileRepository = Depends(get_file_dao)):
    return FileService(file_repository)
