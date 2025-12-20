from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import *
from src.domain.file.dao.file_repository import FileRepository
from src.domain.file.model.file_model import FileInfoDTO, FileInfoVO, FileInfoListVO
import logging

log = logging.getLogger(__name__)

class FileService:
    def __init__(self, file_repository: FileRepository):
        self.file_repository = file_repository

    async def save_file_info(self, session: AsyncSession, file_info: FileInfoDTO) -> FileInfoVO:
        try:
            res: FileInfoDTO = await self.file_repository.upsert(session, file_info)
            return FileInfoVO.of(res)
        except Exception as e:
            # github codepilot 可以自動生成，多善用
            log.error(f'save_file_info error: %s', str(e)) # 給內部看的 log 訊息 (可能有隱私資訊，exL: SQL語法)
            raise ServerException(msg='File save failed') # 給外部看的錯誤訊息 (response body: {'msg': 'File save failed', 'code':..., 'data':...})

    async def get_file_info(self, session: AsyncSession, user_id: int, file_id: str) -> FileInfoVO:
        try:
            file_info = await self.file_repository.get_file_info_by_id(session, user_id, file_id)
            if not file_info:
                raise NotFoundException(msg='File not found', code='40400', data=False)
            return FileInfoVO.of(file_info)
        except Exception as e:
            log.error(f'get_file_info error: %s', str(e)) # 給內部看的 log 訊息 (可能有隱私資訊，exL: SQL語法)
            # 有兩種以上的錯誤類型: 1) NotFoundException, 2) 其他格式/系統錯誤等，就透過 getattr 取得 NotFoundException.msg (其他自定義的 exception 都有 msg 屬性)
            err_msg = getattr(e, 'msg', 'File read error')
            raise_http_exception(e, msg=err_msg) # 可以取得 1) 'NotFoundException', 2) 其他格式/系統錯誤等 多種錯誤類型

    async def delete_file_info(self, session: AsyncSession, user_id: int, file_name: str) -> bool:
        try:
            return await self.file_repository.delete_file_info_by_name(session, user_id, file_name)
        except Exception as e:
            log.error(f'delete_file_info error: %s', str(e)) # 給內部看的 log 訊息 (可能有隱私資訊，exL: SQL語法)
            raise ServerException(e, msg='File delete failed') # 給外部看的錯誤訊息 (response body: {'msg': 'File delete failed', 'code':..., 'data':...})

    # async def get_all_files(self, session: AsyncSession) -> List[FileInfoVO]:
    #     res: List[FileInfoDTO] = await self.file_repository.get_all_files_info(session)
    #     return [FileInfoVO.of(r) for r in res]

    async def get_file_info_by_user_id(self, session: AsyncSession, user_id: int) -> FileInfoListVO:
        try:
            file_info_list = await self.file_repository.get_by_user_id(session, user_id)
            if not file_info_list:
                raise NotFoundException(msg='File not found', code='40400', data=False)
            return FileInfoListVO.of(file_info_list)
        except Exception as e:
            log.error(f'get_file_info_by_user_id error: %s', str(e))
            err_msg = getattr(e, 'msg', str(e)) # 取得 e.msg 的值，若無則取得 str(e)
            raise_http_exception(e, msg=err_msg) # 可以取得 1) 'NotFoundException', 2) 其他格式/系統錯誤等 多種錯誤類型

    async def update_file_info(self, session: AsyncSession, user_id: int, file_info: FileInfoDTO) -> FileInfoVO:
        try:
            update_res = await self.file_repository.update(session, user_id, file_info)
            file_info = FileInfoDTO.of(update_res)

            return FileInfoVO.of(file_info)
        except Exception as e:
            log.error(f'update_file_info error: %s', str(e))
            raise ServerException(msg='File update failed')
