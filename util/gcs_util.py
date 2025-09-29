from datetime import datetime
from sqlalchemy import select, update
from google.cloud import storage
import os
import json
import asyncio
from typing import Dict
from db.models import QueryLog

import logging
logger = logging.getLogger(__name__)

def _upload_syc(bucket, blob_path, data):
    blob = bucket.blob(blob_path)
    blob.upload_from_string(data, content_type="application/json")

async def upload_result_to_gcs(result_dict: Dict, filename: str):
    try:
        logger.info(f"trying to log in GCB: {result_dict}")
        client = storage.Client()
        bucket = client.bucket(os.getenv("RESULTS_BUCKET", "mindmap-results"))
        blob = f"query_results/{filename}"
        data = json.dumps(result_dict, indent=2)
        await asyncio.to_thread(_upload_syc, bucket, blob, data)
    except json.JSONDecodeError as e:
        logger.error(f"Unable to store to GC bucket. Error: {e}")
    except Exception as e:
        logger.exception(f"Exception while uploading to GC bucket: {e}")


async def save_to_sql_db(log_entry, db):
    try:
        stmt = select(QueryLog).where(
            QueryLog.user_id == log_entry.user_id,
            QueryLog.chat_id == log_entry.chat_id,
            QueryLog.session_id == log_entry.session_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            await db.execute(
                update(QueryLog)
                .where (QueryLog.id == existing.id)
                .values(
                    chat_logs=log_entry.chat_logs,
                    updated_at=datetime.now()
                )
            )
        else:
            db.add(log_entry)
        
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Unable to save to SQL. Error: {e}")