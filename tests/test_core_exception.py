from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request

from app.core.exception import (
    ArticleNotFoundException,
    BaseInternalException,
    _build_conduit_errors_from_http_exception,
    _build_conduit_errors_from_validation,
    add_exception_handlers,
)


def test_base_internal_exception_defaults_and_fields():
    exc = BaseInternalException()
    assert exc.get_status_code() == 400
    assert exc.get_message() == "error"
    assert exc.get_field() == "body"


def test_custom_internal_exception_values():
    exc = ArticleNotFoundException()
    assert exc.get_status_code() == 404
    assert exc.get_message() == "not found"
    assert exc.get_field() == "article"


def test_build_conduit_errors_from_validation_msg_translation():
    class DummyValidationError:
        def errors(self):
            return [
                {"loc": ["body", "email"], "msg": "value is not a valid email address"},
                {"loc": ["query", "limit"], "msg": "ensure this value has at least 1 items"},
            ]

    errors = _build_conduit_errors_from_validation(DummyValidationError())
    assert errors == {"email": ["can't be blank"], "limit": ["can't be blank"]}


def test_build_conduit_errors_from_validation_empty_errors():
    class DummyValidationError:
        def errors(self):
            return []

    errors = _build_conduit_errors_from_validation(DummyValidationError())
    assert errors == {"body": ["invalid request"]}


def test_build_conduit_errors_from_http_exception_401_missing():
    http_exc = HTTPException(status_code=401, detail="Missing authorization credentials")
    errors = _build_conduit_errors_from_http_exception(http_exc)
    assert errors == {"token": ["is missing"]}


def test_build_conduit_errors_from_http_exception_404_article():
    http_exc = HTTPException(status_code=404, detail="Article not found")
    errors = _build_conduit_errors_from_http_exception(http_exc)
    assert errors == {"article": ["not found"]}


def test_add_exception_handlers_for_internal_exception_with_testclient():
    app = FastAPI()
    add_exception_handlers(app)

    @app.get("/article")
    async def _handler():
        raise ArticleNotFoundException()

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/article")
    assert response.status_code == 404
    assert response.json() == {"errors": {"article": ["not found"]}}
