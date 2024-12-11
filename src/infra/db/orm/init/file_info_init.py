from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, Boolean, UUID, String, text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class FileInfo(Base):
    __tablename__ = 'file_info'

    file_id = Column(UUID(as_uuid=True), primary_key=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(255))
    url = Column(String)
    create_user_id = Column(Integer, nullable=False)
    create_time = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    update_time = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    is_deleted = Column(
        Boolean,
        nullable=False,
        server_default=text('FALSE')
    )
