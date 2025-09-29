from cachetools import TTLCache

chat_logs_cache = TTLCache(maxsize=100, ttl=3600)

__all__ =["chat_logs_cache"]