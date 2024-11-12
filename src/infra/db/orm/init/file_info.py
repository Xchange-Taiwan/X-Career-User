from datetime import datetime
from tokenize import String

from sqlalchemy import Column, Integer, DateTime, Boolean, UUID
from sqlalchemy.orm import declarative_base
import uuid

from src.domain.file.dto.file_info_dto import FileInfoServiceDTO

Base = declarative_base()


class FileInfo(Base):
    __tablename__ = 'file_info'

    info_id = Column(UUID, primary_key=True)
    filename = Column(String)
    size = Column(Integer)
    content_type = Column(String)
    url = Column(String)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    @staticmethod
    def of(dto: FileInfoServiceDTO):
        return FileInfo(info_id=uuid.UUID(dto.file_id),
                        filename=dto.filename,
                        size=dto.size,
                        content_type=dto.content_type,
                        url=dto.url,
                        create_time=dto.create_time,
                        update_time=dto.update_time,
                        is_deleted=dto.is_deleted)
