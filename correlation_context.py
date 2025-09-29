# correlation_context.py

from contextvars import ContextVar

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="N/A")

def set_correlation_id(corr_id: str):
    correlation_id_ctx.set(corr_id)

def get_correlation_id() -> str:
    return correlation_id_ctx.get()