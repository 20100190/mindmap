import json
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from llm import orchestrator as llm_orchestrator
from util import process_json_mindmap
import logging
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str

router = APIRouter()

@router.post("/query")
async def query_endpoint(request:QueryRequest):

    try:
        llm_orchestrator_instance = llm_orchestrator.LLMOrchestrator()

        if not isinstance(request, QueryRequest):
            return {"error": "Invalid request format"}

        query = request.query.strip()
        user_query_message = ""
        for try_count in range(3):

            user_query = query + user_query_message
            logger.info(f"Running loop No. {try_count} with user query = {user_query}")
            result = await llm_orchestrator_instance.generate_mindmap(user_query)
            tree_depth = process_json_mindmap.count_depth(result.get('data', {}))

            logger.info(f"Tree depth {tree_depth} for try_count: {try_count}")

            if tree_depth > 1:
                processed_result = process_json_mindmap.process_mindmap(result)
                json_result_print = json.dumps(processed_result, indent=2)
                json_filename = f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    f.write(json_result_print)

                # Return response
                return processed_result

            else:
                user_query_message = " Please provide a more detailed and structured mindmap with deeper hierarchy."
        else:
            processed_result = process_json_mindmap.process_mindmap(result)
            return processed_result

    except Exception as e:
        return {
            "status": "error",
            "data": {"error": str(e)},
            "function_calls": [],
            "message": f"Server error: {str(e)}"
        }
