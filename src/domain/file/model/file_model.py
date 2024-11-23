#file_dto
from datetime import datetime, timezone
from typing import Optional

from pydantic import HttpUrl, BaseModel, UUID4
from sqlalchemy import String

from src.infra.db.orm.init.file_info_init import FileInfo


class FileInfoDTO(BaseModel):
    file_id: Optional[UUID4] # uuid
    file_name: str
    file_size: int
    content_type: Optional[str] = None
    url: Optional[HttpUrl] = "http://example.com"  # Validates URL if provided
    create_time: Optional[datetime] = datetime.now(timezone.utc)
    update_time: Optional[datetime] = datetime.now(timezone.utc)
    is_deleted: bool = False

    @staticmethod
    def of(model: FileInfo):
        return FileInfoDTO(
            file_id=model.file_id,
            file_name=model.file_name,
            file_size=model.file_size,
            content_type=model.content_type,
            url=model.url,
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
    is_deleted: bool = False
    @staticmethod
    def of(model: FileInfoDTO):
        return FileInfoVO(
            file_id=model.file_id,
            file_name=model.file_name,
            file_size=model.file_size,
            content_type=model.content_type,
            url=model.url,
            create_time=model.create_time,
            update_time=model.update_time,
            is_deleted=model.is_deleted
        )