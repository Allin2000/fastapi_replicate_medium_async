import pytest
from starlette.requests import Request

from app.core.security import HTTPTokenHeader


@pytest.mark.asyncio
async def test_http_token_header_raises_when_missing_and_raise_error_true():
    header = HTTPTokenHeader(raise_error=True, name="Authorization")
    request = Request({"type": "http", "headers": []})

    with pytest.raises(Exception) as exc_info:
        await header(request)
    assert "Missing authorization credentials" in str(exc_info.value)


@pytest.mark.asyncio
async def test_http_token_header_returns_empty_when_missing_and_raise_error_false():
    header = HTTPTokenHeader(raise_error=False, name="Authorization")
    request = Request({"type": "http", "headers": []})

    token = await header(request)
    assert token == ""


@pytest.mark.asyncio
async def test_http_token_header_rejects_invalid_schema():
    header = HTTPTokenHeader(raise_error=True, name="Authorization")
    request = Request({
        "type": "http",
        "headers": [[b"authorization", b"invalidtoken"]],
    })

    with pytest.raises(Exception) as exc_info:
        await header(request)

    assert "Invalid token schema" in str(exc_info.value)


@pytest.mark.asyncio
async def test_http_token_header_rejects_wrong_prefix():
    header = HTTPTokenHeader(raise_error=True, name="Authorization")
    request = Request({
        "type": "http",
        "headers": [[b"authorization", b"Bearer abc.def"]],
    })

    with pytest.raises(Exception) as exc_info:
        await header(request)

    assert "Invalid token schema" in str(exc_info.value)


@pytest.mark.asyncio
async def test_http_token_header_parses_valid_token():
    header = HTTPTokenHeader(raise_error=True, name="Authorization")
    request = Request({
        "type": "http",
        "headers": [[b"authorization", b"Token abc.def"]],
    })

    token = await header(request)
    assert token == "abc.def"
