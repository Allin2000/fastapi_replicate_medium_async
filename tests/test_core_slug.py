from unittest.mock import patch

from app.core.slug import make_slug_from_title, make_slug_from_title_and_code, get_slug_unique_part


def test_make_slug_from_title_uses_slugify_and_token():
    with patch("app.core.slug.token_urlsafe", return_value="ABC123"):
        slug = make_slug_from_title("Hello World")

    assert slug.startswith("hello-world-")
    assert slug.endswith("abc123")
    assert get_slug_unique_part(slug) == "abc123"


def test_make_slug_from_title_and_code():
    slug = make_slug_from_title_and_code("FastAPI Rocks", "987654")
    assert slug == "fastapi-rocks-987654"


def test_get_slug_unique_part_extracts_last_segment():
    assert get_slug_unique_part("some-title-foobar-123") == "123"
