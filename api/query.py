from fastapi import APIRouter
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from services import query_service


import logging
logger = logging.getLogger(__name__)




class QueryRequest(BaseModel):
    query: str

router = APIRouter()

@router.post("/query")
async def query_endpoint(request:QueryRequest, db:AsyncSession=Depends(get_db)):
    return await query_service.handle_query(request.query, db)