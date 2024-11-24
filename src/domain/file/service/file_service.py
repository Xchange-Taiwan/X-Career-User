from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert

from src.config.exception import NotFoundException
from src.domain.file.dao.file_repository import FileRepository
from src.domain.file.model.file_model import FileInfoDTO, FileInfoVO, FileInfoListVO


class FileService:
    def __init__(self, file_repository: FileRepository):
        self.file_repository = file_repository

    async def save_file_info(self, session: AsyncSession, file_info: FileInfoDTO) -> FileInfoVO:
        res: FileInfoDTO = await self.file_repository.insert(session, file_info)
        return FileInfoVO.of(res)

    async def get_file_info(self, session: AsyncSession, user_id: int, file_id: str) -> FileInfoVO:
        file_info = await self.file_repository.get_file_info_by_id(session, user_id, file_id)
        if not file_info:
            raise NotFoundException(msg="File not found", code="40400", data=False)
        return FileInfoVO.of(file_info)

    async def delete_file_info(self, session: AsyncSession, user_id: int, file_id: str) -> bool:
        return await self.file_repository.delete_file_info_by_id(session, user_id, file_id)

    # async def get_all_files(self, session: AsyncSession) -> List[FileInfoVO]:
    #     res: List[FileInfoDTO] = await self.file_repository.get_all_files_info(session)
    #     return [FileInfoVO.of(r) for r in res]

    async def get_file_info_by_user_id(self, session: AsyncSession, user_id: int) -> FileInfoListVO:
        file_info_list = await self.file_repository.get_by_user_id(session, user_id)
        if not file_info_list:
            raise NotFoundException(msg="File not found", code="40400", data=False)
        return FileInfoListVO.of(file_info_list)

    async def update_file_info(self, session: AsyncSession, user_id: int, file_info: FileInfoDTO) -> FileInfoVO:
        update_res = await self.file_repository.update(session, user_id, file_info)
        file_info = FileInfoDTO.of(update_res)

        return FileInfoVO.of(file_info)
