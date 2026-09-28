import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Добавляет заголовок X-Process-Time с временем обработки запроса"""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response
