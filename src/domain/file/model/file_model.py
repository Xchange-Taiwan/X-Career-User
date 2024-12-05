#file_dto
from datetime import datetime, timezone
from typing import Optional, List, Union

from pydantic import HttpUrl, BaseModel, UUID4

from src.infra.db.orm.init.file_info_init import FileInfo


class FileInfoDTO(BaseModel):
    file_id: Optional[UUID4]  # uuid
    file_name: str
    file_size: int
    content_type: Optional[str] = None
    url: Optional[Union[str, HttpUrl]] = "http://example.com"  # Validates URL if provided
    create_time: Optional[datetime] = datetime.now(timezone.utc)
    update_time: Optional[datetime] = datetime.now(timezone.utc)
    create_user_id: int
    is_deleted: bool = False

    @staticmethod
    def of(model: FileInfo):
        return FileInfoDTO(
            file_id=model.file_id,
            file_name=model.file_name,
            file_size=model.file_size,
            content_type=model.content_type,
            url=model.url,
            create_user_id=model.create_user_id,
            create_time=model.create_time,
            update_time=model.update_time,
            is_deleted=model.is_deleted
        )


class FileInfoVO(BaseModel):
    file_id: Optional[UUID4]  # uuid
    file_name: str
    file_size: int
    content_type: Optional[str] = None
    url: Optional[HttpUrl] = None  # Validates URL if provided
    create_time: datetime
    update_time: datetime
    create_user_id: int
    is_deleted: bool = False

    @staticmethod
    def of(model: FileInfoDTO):
        return FileInfoVO(
            file_id=model.file_id,
            file_name=model.file_name,
            file_size=model.file_size,
            content_type=model.content_type,
            url=model.url,
            create_user_id=model.create_user_id,
            create_time=model.create_time,
            update_time=model.update_time,
            is_deleted=model.is_deleted
        )


class FileInfoListVO(BaseModel):
    file_info_vo_list: List[FileInfoVO]

    @staticmethod
    def of(model_list: List[FileInfo]):
        return FileInfoListVO(file_info_vo_list=[FileInfoVO.of(file_info_dto) for file_info_dto in model_list])
