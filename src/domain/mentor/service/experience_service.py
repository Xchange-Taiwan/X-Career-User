from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotFoundException, ServerException
from src.domain.mentor.model.experience_model import ExperienceVO, ExperienceDTO, ExperienceListVO
from src.domain.user.dao.mentor_experience_repository import MentorExperienceRepository
from src.infra.db.orm.init.user_init import MentorExperience
import logging

log = logging.getLogger(__name__)


class ExperienceService:
    def __init__(self, exp_dao: MentorExperienceRepository):
        self.__exp_dao = exp_dao

    async def get_exp_list_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[List[ExperienceVO]]:
        try:
            mentor_exp: List[MentorExperience] = await self.__exp_dao.get_mentor_exp_list_by_user_id(db, user_id)
            if not mentor_exp:
                return []
            return [ExperienceVO.model_validate(exp) for exp in mentor_exp]
        except Exception as e:
            log.error(f'get_exp_list_by_user_id error: %s', str(e))
            raise ServerException(msg='get experience list response failed')

    # FIXME: 育志，為什麼透過u ser_id 去取得的經驗只會有一種？應該包含 學歷/經歷/LINK ... 多種經驗
    # 我用 get_exp_list_by_user_id 實現的函數你可以參考一下
    async def get_exp_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[ExperienceVO]:
        try:
            mentor_exp_list: List[MentorExperience] = \
                await self.__exp_dao.get_mentor_exp_list_by_user_id(db, user_id)
            if not mentor_exp_list:
                return []

            experiences = [ExperienceVO.model_validate(exp) for exp in mentor_exp_list]
            return ExperienceListVO(experiences=experiences)
        except Exception as e:
            log.error(f'get_exp_by_user_id error: %s', str(e))
            raise ServerException(msg='get experience response failed')

    async def upsert_exp(self, db: AsyncSession,
                         user_id: int,
                         experience_dto: ExperienceDTO) -> ExperienceVO:
        try:
            mentor_exp: MentorExperience = await self.__exp_dao.upsert_mentor_exp_by_user_id(db=db,
                                                                                            user_id=user_id,
                                                                                            mentor_exp_dto=experience_dto)
            res: ExperienceVO = ExperienceVO.model_validate(mentor_exp)

            return res
        except Exception as e:
            log.error(f'upsert_exp error: %s', str(e))
            raise ServerException(msg='upsert experience response failed')

    async def sync_experiences(
        self,
        db: AsyncSession,
        user_id: int,
        experiences: List[ExperienceDTO],
    ) -> List[ExperienceVO]:
        # Replace semantics: the provided list IS the new full set.
        # Items with id are upserted; items without id are inserted; any
        # existing experience whose id isn't in the kept set is deleted.
        # Single commit at the end so the batch is internally atomic — a
        # mid-batch failure rolls back to the pre-call state.
        try:
            current: List[MentorExperience] = (
                await self.__exp_dao.get_mentor_exp_list_by_user_id(db, user_id)
            )
            current_ids = {e.id for e in current if e.id is not None}

            # Reject ids that aren't owned by this user — db.merge would
            # otherwise reassign another user's row to user_id (cross-user
            # clobber). Treat foreign ids as new inserts.
            sanitized_ids: List[Optional[int]] = []
            for exp_dto in experiences:
                if exp_dto.id is not None and exp_dto.id not in current_ids:
                    log.warning(
                        'sync_experiences: dropping foreign exp id %s for user %s',
                        exp_dto.id, user_id,
                    )
                    sanitized_ids.append(None)
                else:
                    sanitized_ids.append(exp_dto.id)

            kept_ids = {sid for sid in sanitized_ids if sid is not None}
            ids_to_delete = current_ids - kept_ids

            if ids_to_delete:
                await self.__exp_dao.delete_by_user_id_in_ids(
                    db, user_id, ids_to_delete,
                )

            merged_rows: List[MentorExperience] = []
            for exp_dto, exp_id in zip(experiences, sanitized_ids):
                row = MentorExperience(
                    id=exp_id,
                    user_id=user_id,
                    category=exp_dto.category,
                    order=exp_dto.order,
                    mentor_experiences_metadata=exp_dto.mentor_experiences_metadata,
                )
                merged_rows.append(await db.merge(row))

            await db.commit()
            for row in merged_rows:
                await db.refresh(row)

            return [ExperienceVO.model_validate(row) for row in merged_rows]
        except Exception as e:
            await db.rollback()
            log.error(f'sync_experiences error: %s', str(e))
            raise ServerException(msg='sync experiences response failed')

    async def delete_exp_by_user_and_exp_id(self, db: AsyncSession,
                                            user_id: int,
                                            experience_dto: ExperienceDTO) -> bool:
        try:
            res: bool = await self.__exp_dao.delete_mentor_exp_by_id(db, user_id, experience_dto)
            if not res:
                exp_id = experience_dto.id
                log.info('user_id: %s No such experience with id: %s', user_id, exp_id)
            return res
        except Exception as e:
            log.error(f'delete_exp_by_user_and_exp_id error: %s', str(e))
            raise ServerException(msg=f'delete experience response failed: user_id: {user_id}, exp_id: {exp_id}')


    # Onboarding completion gate. Mentee onboarding writes profiles.want_tags;
    # have_tags is mentor-only and stays empty for plain mentees, so checking
    # want_tags alone is sufficient.
    @staticmethod
    def is_onboarded(want_tags: Optional[List[str]]) -> bool:
        return bool(want_tags)

    # 是否為 Mentor, 透過是否有填寫足夠的經驗類別判斷
    @staticmethod
    def is_mentor(experiences: List[ExperienceVO]) -> bool:
        exp_categories = set()
        for exp in experiences:
            if exp.category:
                exp_categories.add(exp.category)

        # 如果有填寫至少 2 種經驗類別, 則視為已完成 Mentor
        return (len(exp_categories) >= 2)
