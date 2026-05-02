from typing import List, Optional, Tuple

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.mentor.model.mentor_model import MentorProfileDTO
from src.infra.db.orm.init.user_init import Profile, MentorExperience
from src.infra.util.convert_util import get_first_template


# Per-bucket replace inputs on MentorProfileDTO — they're not Profile columns,
# so they're stripped from the dump before the dto is mapped onto the ORM.
_INPUT_BUCKET_FIELDS = {
    'want_position', 'want_skill', 'want_topic', 'have_skill', 'have_topic',
}


# (dto, want_tags, have_tags) — the storage arrays travel alongside the dto
# rather than on it, so the API-facing dto stays free of plumbing fields.
ProfileWithTags = Tuple[MentorProfileDTO, List[str], List[str]]


class MentorRepository:

    async def get_mentor_profile_by_id(
        self, db: AsyncSession, mentor_id: int
    ) -> Optional[ProfileWithTags]:
        stmt: Select = select(Profile).filter(Profile.user_id == mentor_id)
        mentor: Optional[Profile] = await get_first_template(db, stmt)
        if mentor is None:
            return None
        return self._split(mentor)

    async def find_profile_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> Optional[ProfileWithTags]:
        # Used by the upsert path to pull existing want_tags/have_tags before
        # the per-bucket merge; returns None on first-time mentors.
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)
        profile: Optional[Profile] = await get_first_template(db, stmt)
        if profile is None:
            return None
        return self._split(profile)

    async def upsert_mentor(
        self,
        db: AsyncSession,
        mentor_profile_dto: MentorProfileDTO,
        *,
        want_tags: List[str],
        have_tags: List[str],
    ) -> ProfileWithTags:
        # Load-or-create rather than db.merge: the input bucket fields aren't
        # Profile columns, and merge would clobber want_tags/have_tags
        # columns the dto doesn't carry. The merged storage arrays come in
        # as kwargs because they're storage state, not API surface.
        payload = mentor_profile_dto.model_dump(exclude=_INPUT_BUCKET_FIELDS)
        payload['want_tags'] = want_tags
        payload['have_tags'] = have_tags

        existing: Optional[Profile] = await db.get(Profile, mentor_profile_dto.user_id)
        if existing is None:
            model = Profile(**payload)
            db.add(model)
            await db.commit()
            await db.refresh(model)
            return self._split(model)

        for key, value in payload.items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return self._split(existing)

    async def delete_mentor_profile_by_id_and_language(self, db: AsyncSession, user_id: int, language: str) -> None:
        stmt: Select = select(Profile).join(MentorExperience, MentorExperience.user_id == Profile.user_id)
        stmt: Select = stmt.filter(Profile.user_id == user_id and Profile.language == language)
        mentor: Profile = await get_first_template(db, stmt)

        if mentor:
            await db.delete(mentor)
            await db.commit()

    @staticmethod
    def _split(profile: Profile) -> ProfileWithTags:
        return (
            MentorProfileDTO.model_validate(profile),
            list(profile.want_tags or []),
            list(profile.have_tags or []),
        )
