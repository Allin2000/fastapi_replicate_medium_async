from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse


class BaseInternalException(Exception):
    """
    Base error class for internal domain errors.
    """

    _status_code = 400
    _field = "body"
    _message = "error"

    def __init__(self, status_code: int | None = None, message: str | None = None):
        self.status_code = status_code or self._status_code
        self.message = message or self._message

    def get_status_code(self) -> int:
        return self.status_code

    def get_message(self) -> str:
        return self.message

    def get_field(self) -> str:
        return self._field


class UserNotFoundException(BaseInternalException):
    _status_code = 404
    _field = "user"
    _message = "not found"


class ArticleNotFoundException(BaseInternalException):
    _status_code = 404
    _field = "article"
    _message = "not found"


class ArticleAlreadyFavoritedException(BaseInternalException):
    _status_code = 400
    _field = "article"
    _message = "already favorited"


class ArticleNotFavoritedException(BaseInternalException):
    _status_code = 400
    _field = "article"
    _message = "not favorited"


class ArticlePermissionException(BaseInternalException):
    _status_code = 403
    _field = "article"
    _message = "forbidden"


class CommentNotFoundException(BaseInternalException):
    _status_code = 404
    _field = "comment"
    _message = "not found"


class CommentPermissionException(BaseInternalException):
    _status_code = 403
    _field = "comment"
    _message = "forbidden"


class EmailAlreadyTakenException(BaseInternalException):
    _status_code = 409
    _field = "email"
    _message = "has already been taken"


class UserNameAlreadyTakenException(BaseInternalException):
    _status_code = 409
    _field = "username"
    _message = "has already been taken"


class IncorrectLoginInputException(BaseInternalException):
    _status_code = 401
    _field = "credentials"
    _message = "invalid"


class IncorrectJWTTokenException(BaseInternalException):
    _status_code = 401
    _field = "token"
    _message = "is invalid"


class ProfileNotFoundException(BaseInternalException):
    _status_code = 404
    _field = "profile"
    _message = "not found"


class OwnProfileFollowingException(BaseInternalException):
    _status_code = 400
    _field = "profile"
    _message = "cannot follow yourself"


class ProfileAlreadyFollowedException(BaseInternalException):
    _status_code = 400
    _field = "profile"
    _message = "already followed"


class ProfileNotFollowedFollowedException(BaseInternalException):
    _status_code = 400
    _field = "profile"
    _message = "not followed"


class RateLimitExceededException(BaseInternalException):
    _status_code = 429
    _field = "rate"
    _message = "rate limit exceeded. Please try again later."

    @classmethod
    def get_response(cls) -> JSONResponse:
        return JSONResponse(
            status_code=cls._status_code,
            content={
                "errors": {
                    cls._field: [cls._message],
                }
            },
        )


# Exception serializer helpers

def _build_conduit_errors_from_validation(exc: RequestValidationError) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for error in exc.errors():
        loc = error.get("loc", [])
        if len(loc) > 0 and loc[0] in {"body", "query", "path", "header", "json"}:
            field = loc[-1]
            if isinstance(field, int):
                field = "body"
        elif len(loc) > 0:
            field = loc[-1]
        else:
            field = "body"

        msg = error.get("msg", "invalid")
        if "at least" in msg or "greater than" in msg or "not be blank" in msg or "ensure this value has at least" in msg:
            msg_formatted = "can't be blank"
        elif msg == "value is not a valid email address" or msg == "str type expected":
            msg_formatted = "can't be blank"
        else:
            msg_formatted = msg

        errors.setdefault(str(field), []).append(msg_formatted)
    if not errors:
        errors["body"] = ["invalid request"]
    return errors


def _build_conduit_errors_from_http_exception(exc: HTTPException) -> dict[str, list[str]]:
    detail = exc.detail
    if isinstance(detail, dict) and "errors" in detail:
        return detail["errors"]

    # Parse known messages
    if exc.status_code == 401:
        if "Missing" in str(detail) or "missing" in str(detail):
            return {"token": ["is missing"]}
        return {"token": ["is invalid"]}

    if exc.status_code == 403:
        if "article" in str(detail).lower():
            return {"article": ["forbidden"]}
        if "comment" in str(detail).lower():
            return {"comment": ["forbidden"]}
        if "profile" in str(detail).lower():
            return {"profile": ["forbidden"]}
        return {"body": ["forbidden"]}

    if exc.status_code == 404:
        if "profile" in str(detail).lower():
            return {"profile": ["not found"]}
        if "article" in str(detail).lower():
            return {"article": ["not found"]}
        if "comment" in str(detail).lower():
            return {"comment": ["not found"]}
        if "user" in str(detail).lower():
            return {"user": ["not found"]}
        return {"body": ["not found"]}

    return {"body": [str(detail)]}


def add_internal_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(BaseInternalException)
    async def _exception_handler(_: Request, exc: BaseInternalException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.get_status_code(),
            content={
                "errors": {
                    exc.get_field(): [exc.get_message()],
                }
            },
        )


def add_request_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "errors": _build_conduit_errors_from_validation(exc),
            },
        )


def add_http_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "errors": _build_conduit_errors_from_http_exception(exc),
            },
        )


def add_exception_handlers(app: FastAPI) -> None:
    add_internal_exception_handler(app=app)
    add_request_exception_handler(app=app)
    add_http_exception_handler(app=app)
