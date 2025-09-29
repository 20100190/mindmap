from sqlalchemy import Text
from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from db.session import Base  # Make sure path is correct

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String)
    session_id = Column(String)
    chat_id = Column(Integer)
    query_text = Column(String)
    used_functions = Column(String)
    response_length = Column(Integer)
    mindmap_depth = Column(Integer)
    error_flag = Column(Boolean)
    chat_logs = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=False), server_default=func.now())