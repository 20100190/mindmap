from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from llm.orchestrator import LLMOrchestrator
from util import process_json_mindmap
from db.models import QueryLog
from util.gcs_util import upload_result_to_gcs  # ← utility we’ll extract

async def handle_query(user_query: str, db: AsyncSession) -> dict:

    orchestrator = LLMOrchestrator()
    message = ""
    result = None

    for try_count in range(3):
        query = user_query + message
        result = await orchestrator.generate_mindmap(query)
        depth = process_json_mindmap.count_depth(result.get("data", {}))

        if depth > 1:
            processed = process_json_mindmap.process_mindmap(result)

            # Save JSON to GCS
            json_filename = f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            upload_result_to_gcs(processed, json_filename)

            # Log to DB
            log_entry = QueryLog(
                user_id=None,
                query_text=user_query,
                used_functions=str(result['function_calls']),
                response_length=len(str(result)),
                mindmap_depth=depth,
                error_flag=False,
            )
            db.add(log_entry)
            await db.commit()

            return processed

        message = " Please provide a more detailed and structured mindmap with deeper hierarchy."

    # Last fallback
    return process_json_mindmap.process_mindmap(result)