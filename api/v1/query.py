from datetime import datetime
from chat_log_cache import chat_log
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from services import query_service
from fastapi import BackgroundTasks
from fastapi import Request, APIRouter

from db.models import QueryLog
from chat_log_cache.chat_log import chat_logs_cache
from util.gcs_util import upload_result_to_gcs, save_to_sql_db  # ← utility we’ll extract


import logging
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    user_query: str
    session_id: str
    user_id: str | None = None
    chat_id: int | None = None


router = APIRouter()

@router.post("/query")
async def query_endpoint(
        user_request:QueryRequest, 
        background_tasks: BackgroundTasks, 
        request: Request,
        db:AsyncSession=Depends(get_db)
    ):
    """Generate a mindmap / Simple text based answer for user query."""
    try: 
        correlation_id = request.headers.get("correlation_id")
        user_query, user_id, session_id, chat_id = user_request.user_query, user_request.user_id, user_request.session_id, user_request.chat_id
        response = await query_service.handle_query(user_request, correlation_id)

        logger.info(f"Response from Query Service: {response}")

        
        log_entry = QueryLog(
                    user_id=user_id,
                    session_id=session_id,
                    chat_id=chat_id,                    
                    query_text=user_query,
                    used_functions=str(response.get("function_calls")),
                    response_length=int(response.get("full_response").usage.total_tokens), # tokens
                    mindmap_depth=0,
                    error_flag=False,
                    chat_logs=str(response.get("chat_log"))
        )

        chat_logs_cache[(user_id, session_id, chat_id)] = response.get("chat_log")

        
        json_filename = f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        background_tasks.add_task(upload_result_to_gcs, response.get("chat_log", []), json_filename)
        background_tasks.add_task(save_to_sql_db, log_entry, db)

        return {
            "mindmap": response.get("mindmap", {}),
            "message": response.get("message", None),
            "chat_log": response.get("chat_log")
        }
    except Exception as e:
        logger.exception(f"Unable to create map. Error: {e}")