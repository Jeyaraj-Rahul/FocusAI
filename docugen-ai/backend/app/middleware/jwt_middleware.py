from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request.state.user_id = None
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")

        if scheme.lower() == "bearer" and token:
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                request.state.user_id = payload.get("sub")
            except JWTError:
                request.state.user_id = None

        return await call_next(request)
