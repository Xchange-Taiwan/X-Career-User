from sqlalchemy import Column, BigInteger, String, Integer, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
from src.config.constant import OutboxStatus

# Assuming these are imported from your config
from .....config.constant import AggregateType, EventType

Base = declarative_base()


class OutboxMessage(Base):
    __tablename__ = "outbox_message"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    aggregate_id = Column(String(100), nullable=False)  # Virtual Foreign Key to other table (e.g. user_id -> profiles)
    # create_type=False -> doesn't create ENUM to the database
    aggregate_type = Column(ENUM(AggregateType, name="aggregate_type_enum", create_type=False),nullable=False)
    event_type = Column(ENUM(EventType, name="event_type_enum", values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    payload = Column(JSONB, nullable=False)

    # Delivery & Status Tracking 0: initial, 1: pending, 2: failed, 3: success
    status = Column(Integer, nullable=False, default=OutboxStatus.PENDING) 
    retry_count = Column(Integer, nullable=False, default=0)
    err_msg = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("TIMEZONE('utc', NOW())")

    )
    next_retry_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("TIMEZONE('utc', NOW())")

    )

    def __repr__(self):
        return f"<OutboxMessage(id={self.id}, status={self.status}, event={self.event_type})>"
