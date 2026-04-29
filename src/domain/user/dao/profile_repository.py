from typing import Optional, Tuple

from sqlalchemy import select, Select, delete as sa_delete, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotFoundException
from src.domain.user.model.user_model import ProfileDTO
from src.infra.db.orm.init.user_init import Profile
from src.infra.util.convert_util import convert_dto_to_model, get_first_template
from src.infra.util.time_util import current_seconds


async def assign_avatar_updated_at(db: AsyncSession, dto: ProfileDTO) -> None:
    """Set ``dto.avatar_updated_at`` ahead of an upsert.

    Bumps to ``current_seconds()`` only when the avatar URL actually changes
    so unrelated profile edits don't invalidate the avatar's cache buster.
    Preserves the previous timestamp otherwise.
    """
    if dto is None or dto.user_id is None:
        return

    stmt: Select = select(Profile).filter(Profile.user_id == dto.user_id)
    existing: Optional[Profile] = await get_first_template(db, stmt)

    new_avatar = (dto.avatar or '').strip()
    prev_avatar = (getattr(existing, 'avatar', None) or '') if existing else ''
    if new_avatar and new_avatar != prev_avatar:
        dto.avatar_updated_at = current_seconds()
    elif existing is not None:
        dto.avatar_updated_at = getattr(existing, 'avatar_updated_at', None)


class ProfileRepository:

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> ProfileDTO:
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)

        query: Optional[Profile] = await get_first_template(db, stmt)
        if query is None:
            raise NotFoundException(msg=f"No such user with id: {user_id}")
        return ProfileDTO.model_validate(query)

    async def find_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[ProfileDTO]:
        stmt: Select = select(Profile).filter(Profile.user_id == user_id)
        query: Optional[Profile] = await get_first_template(db, stmt)
        if query is None:
            return None
        return ProfileDTO.model_validate(query)

    async def upsert_profile(self, db: AsyncSession, dto: ProfileDTO) -> ProfileDTO:
        if (dto is None) or (dto.user_id is None):
            raise NotFoundException(msg="not a valid user")
        # directly upsert since the user_id should be pre dedined in auth service

        await assign_avatar_updated_at(db, dto)
        model: Profile = convert_dto_to_model(dto, Profile)
        model = await db.merge(model)

        await db.commit()
        await db.refresh(model)
        return ProfileDTO.model_validate(model)

    async def delete_profile(self, db: AsyncSession, user_id: int) -> None:
        stmt = sa_delete(Profile).where(Profile.user_id == user_id)
        await db.execute(stmt)

    async def bump_avatar_updated_at(
        self, db: AsyncSession, user_id: int
    ) -> Tuple[int, bool]:
        """Set ``avatar_updated_at`` to ``current_seconds()`` and return the
        value plus ``is_mentor``.

        The S3 avatar key is per-user and stable, so a re-upload doesn't change
        ``profile.avatar``. The BFF calls this after a successful upload (POST
        to presigned URL or server-side upload) to refresh the cache buster
        without going through the full profile upsert path. Returns
        ``is_mentor`` so the caller can decide whether to re-publish to Search.
        """
        now = current_seconds()
        stmt = (
            sa_update(Profile)
            .where(Profile.user_id == user_id)
            .values(avatar_updated_at=now)
            .returning(Profile.avatar_updated_at, Profile.is_mentor)
        )
        result = await db.execute(stmt)
        row = result.first()
        if row is None:
            raise NotFoundException(msg=f"No such user with id: {user_id}")
        await db.commit()
        return row.avatar_updated_at, bool(row.is_mentor)

