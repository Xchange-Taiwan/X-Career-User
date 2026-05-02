from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.mentor.model.mentor_model import MentorProfileDTO
from src.infra.db.orm.init.user_init import Profile, MentorExperience
from src.infra.util.convert_util import get_first_template


# Input-only fields on MentorProfileDTO — they're per-bucket replace inputs,
# not Profile columns. Service layer aggregates them into want_tags/have_tags
# (which ARE columns) before this repository runs the upsert.
_INPUT_BUCKET_FIELDS = {
    'want_position', 'want_skill', 'want_topic', 'have_skill', 'have_topic',
}


class MentorRepository:

    async def get_mentor_profile_by_id(self, db: AsyncSession, mentor_id: int) -> Optional[MentorProfileDTO]:
        stmt: Select = select(Profile).filter(Profile.user_id == mentor_id)
        mentor: Optional[Profile] = await get_first_template(db, stmt)
        if mentor is None:
            return None
        return MentorProfileDTO.model_validate(mentor)

    async def find_profile_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> Optional[MentorProfileDTO]:
        # Used by the upsert path to pull existing want_tags/have_tags before
        # the per-bucket merge; returns None on first-time mentors.
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)
        profile: Optional[Profile] = await get_first_template(db, stmt)
        if profile is None:
            return None
        return MentorProfileDTO.model_validate(profile)

    async def upsert_mentor(self, db: AsyncSession, mentor_profile_dto: MentorProfileDTO) -> MentorProfileDTO:
        # Load-or-create rather than db.merge: the input bucket fields aren't
        # Profile columns, and merge would clobber columns that the dto
        # doesn't carry (e.g. want_tags on a body whose service layer is
        # still warming up).
        payload = mentor_profile_dto.model_dump(exclude=_INPUT_BUCKET_FIELDS)
        existing: Optional[Profile] = await db.get(Profile, mentor_profile_dto.user_id)
        if existing is None:
            model = Profile(**payload)
            db.add(model)
            await db.commit()
            await db.refresh(model)
            return MentorProfileDTO.model_validate(model)

        for key, value in payload.items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return MentorProfileDTO.model_validate(existing)

    async def delete_mentor_profile_by_id_and_language(self, db: AsyncSession, user_id: int, language: str) -> None:
        stmt: Select = select(Profile).join(MentorExperience, MentorExperience.user_id == Profile.user_id)
        stmt: Select = stmt.filter(Profile.user_id == user_id and Profile.language == language)
        mentor: Profile = await get_first_template(db, stmt)

        if mentor:
            await db.delete(mentor)
            await db.commit()
