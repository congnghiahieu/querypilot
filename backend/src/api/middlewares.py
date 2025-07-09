from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.deps import get_current_user
from src.core.settings import PRIVATE_PATHS


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not any(request.url.path.startswith(path) for path in PRIVATE_PATHS):
            return await call_next(request)

        try:
            _ = get_current_user(request)
            return await call_next(request)
        except Exception as e:
            return JSONResponse(status_code=401, content={"detail": str(e)})
