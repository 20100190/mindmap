from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from .session import Base


class QueryLog(Base):
    """Model for storing query execution logs."""
    
    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=True)
    query_text = Column(String, nullable=False)
    used_functions = Column(String, nullable=True)
    response_length = Column(Integer, nullable=True)
    mindmap_depth = Column(Integer, nullable=True)
    error_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())