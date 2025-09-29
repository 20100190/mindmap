import imp
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uuid

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/chat", response_class=HTMLResponse)
async def chat_ui(request: Request):
    # Simulate user_id, chat_id, session_id, and chat log (replace with your own logic)
    user_id = str(uuid.uuid4())
    chat_id = 1
    session_id = str(uuid.uuid4())

    chat_log = [
        {"role": "system", "content": "Welcome to the chatbot!"},
        {"role": "user", "content": "Who won the Hockey World Cup?"},
        {"role": "assistant", "content": "Germany won the 2023 Men's Hockey World Cup."}
    ]

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "user_id": user_id,
        "chat_id": chat_id,
        "session_id": session_id,
        "chat_log": chat_log
    })

__all__ = ["router"]