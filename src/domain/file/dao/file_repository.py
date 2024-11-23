# file_repository
import uuid
from datetime import timezone, datetime
from typing import List

from certifi import where
from sqlalchemy import insert, Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config.exception import NotFoundException
from src.domain.file.model.file_model import FileInfoDTO
from src.infra.db.orm.init.file_info_init import FileInfo
from src.infra.util.convert_util import get_all_template, get_first_template


class FileRepository:
    async def insert(self, session: AsyncSession, file_info_dto: FileInfoDTO) -> FileInfo:
        model = FileInfo(**file_info_dto.__dict__)
        model.file_id = uuid.uuid4()
        session.add(model)
        return model

    async def get_file_info_by_id(self, session: AsyncSession, file_id: str)-> FileInfo:
        stmt: Select = select(FileInfo).filter(FileInfo.file_id == file_id)
        res: FileInfo = await get_first_template(session, stmt)
        return res

    async def delete_file_info_by_id(self, session: AsyncSession, file_id: str) -> bool:
        stmt: Select = select(FileInfo).filter(FileInfo.file_id == file_id)
        res: FileInfo = await get_first_template(session, stmt)
        if res is None:
            return False
        res.is_deleted = True
        return True

    async def get_all_files_info(self, session: AsyncSession) -> List[FileInfo]:
        res = await get_all_template(session, select(FileInfo))
        return res
    async def get_by_filename(self, session: AsyncSession, file_name: str) -> FileInfo:
        stmt: Select = select(FileInfo).filter(FileInfo.file_name == file_name)
        res: FileInfo = await get_first_template(session, stmt)
        return res

    # update
    async def update(self, session: AsyncSession, file_info_dto: FileInfoDTO) -> FileInfo:
        stmt = select(FileInfo).where(FileInfo.file_id == file_info_dto.file_id)
        result = await session.execute(stmt)
        model: FileInfo = result.scalar_one_or_none()
        if model is not None:
            model.file_size = file_info_dto.file_size
            model.file_size = file_info_dto.file_size
            model.update_time = datetime.now(timezone.utc)
            model.is_deleted = file_info_dto.is_deleted
            model.content_type = file_info_dto.content_type
            return model
        else:
            raise NotFoundException(msg="File not found", code="40400", data=False)