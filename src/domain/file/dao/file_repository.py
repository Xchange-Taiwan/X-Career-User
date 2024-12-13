# file_repository
import uuid
from datetime import timezone, datetime
from typing import List

from sqlalchemy import Select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config.exception import NotFoundException
from src.domain.file.model.file_model import FileInfoDTO
from src.infra.db.orm.init.file_info_init import FileInfo
from src.infra.util.convert_util import get_all_template, get_first_template


class FileRepository:
    async def upsert(self, session: AsyncSession, file_info_dto: FileInfoDTO) -> FileInfo:
        # query by user_id and file_name
        stmt: Select = select(FileInfo).where(
            and_(
                FileInfo.create_user_id == file_info_dto.create_user_id,
                FileInfo.file_name == file_info_dto.file_name,
                ~FileInfo.is_deleted
            )
        )
        res: FileInfo = await get_first_template(session, stmt)
        if res is not None:
            res.file_size = file_info_dto.file_size
            res.update_time = datetime.now(timezone.utc)
            res.content_type = file_info_dto.content_type
            res.url = file_info_dto.url
            res = await session.merge(res)
            return res
        else:
            model = FileInfo(**file_info_dto.__dict__)
            model.file_id = uuid.uuid4()
            session.add(model)
            return model

    async def get_file_info_by_id(self, session: AsyncSession, user_id: int, file_id: str) -> FileInfo:
        stmt: Select = select(FileInfo).where(
            and_(
                FileInfo.create_user_id == user_id,
                FileInfo.file_id == file_id,
                ~FileInfo.is_deleted
            )
        )
        res: FileInfo = await get_first_template(session, stmt)
        return res

    async def delete_file_info_by_name(self, session: AsyncSession, user_id: int, file_name: str) -> bool:
        stmt: Select = select(FileInfo).where(
            and_(
                FileInfo.create_user_id == user_id,
                FileInfo.file_name == file_name,
                ~FileInfo.is_deleted
            )
        )
        res: FileInfo = await get_first_template(session, stmt)
        if res is None:
            return False
        res.is_deleted = True
        return True

    async def get_by_user_id(self, session: AsyncSession, user_id: int) -> List[FileInfo]:
        stmt: Select = select(FileInfo).where(
            and_(
                FileInfo.create_user_id == user_id,
                ~FileInfo.is_deleted
            )
        )
        res: FileInfo = await get_all_template(session, stmt)
        return res

    # update
    async def update(self, session: AsyncSession, user_id: int, file_info_dto: FileInfoDTO) -> FileInfo:
        stmt = select(FileInfo).where(
            and_(
                FileInfo.create_user_id == user_id,
                FileInfo.file_id == file_info_dto.file_id,
                FileInfo.create_user_id == user_id,
                ~FileInfo.is_deleted
            )
        )
        result = await session.execute(stmt)
        model: FileInfo = result.scalar_one_or_none()
        if model is not None:
            model.file_size = file_info_dto.file_size
            model.file_name = file_info_dto.file_name
            model.update_time = datetime.now(timezone.utc)
            model.is_deleted = file_info_dto.is_deleted
            model.content_type = file_info_dto.content_type
            model.url = file_info_dto.url
            return model
        else:
            raise NotFoundException(msg="File not found", code="40400", data=False)
