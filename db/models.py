from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from db.session import Base  # Make sure path is correct

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String)
    query_text = Column(String)
    used_functions = Column(String)
    response_length = Column(Integer)
    mindmap_depth = Column(Integer)
    error_flag = Column(Boolean)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())