from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.headers = headers


class ConflictError(AppError):
    status_code: int = 409
    code: str = "conflict"


class UnauthorizedError(AppError):
    status_code: int = 401
    code: str = "unauthorized"

    def __init__(self, message: str, headers: dict[str, str] | None = None) -> None:
        super().__init__(message, headers=headers or {"WWW-Authenticate": "Bearer"})


class ForbiddenError(AppError):
    status_code: int = 403
    code: str = "forbidden"


class NotFoundError(AppError):
    status_code: int = 404
    code: str = "not_found"


class BadRequestError(AppError):
    status_code: int = 400
    code: str = "bad_request"


class InternalServerError(AppError):
    status_code: int = 500
    code: str = "internal_server_error"


def register_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers=exc.headers,
        )
