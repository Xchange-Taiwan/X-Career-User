from datetime import datetime
from typing import Optional

from pydantic import HttpUrl

from src.infra.databse import Base
from src.infra.db.orm.init.file_info import FileInfo


class FileInfoServiceDTO(Base):
    file_id: str  # uuid
    filename: str
    size: int
    content_type: Optional[str] = None
    url: Optional[HttpUrl] = None  # Validates URL if provided
    create_time: datetime
    update_time: datetime
    is_deleted: bool = False

    @staticmethod
    def of(file_info: FileInfo):
        return FileInfoServiceDTO(
            file_id=str(file_info.info_id),
            filename=file_info.filename,
            size=file_info.size,
            content_type=file_info.content_type,
            url=file_info.url,
            create_time=file_info.create_time,
            update_time=file_info.update_time,
            is_deleted=file_info.is_deleted
        )
