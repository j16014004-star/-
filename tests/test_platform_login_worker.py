import pytest

from app.workers.platform_login_worker import is_logged_in


class FakePage:
    def __init__(self, url: str, *, closed: bool = False) -> None:
        self.url = url
        self._closed = closed

    def is_closed(self) -> bool:
        return self._closed


class FakeContext:
    def __init__(self, pages: list[FakePage], cookies: list[dict]) -> None:
        self.pages = pages
        self._cookies = cookies

    async def cookies(self) -> list[dict]:
        return self._cookies


@pytest.mark.asyncio
async def test_login_detects_authenticated_58_page_across_multiple_pages() -> None:
    context = FakeContext(
        pages=[
            FakePage("about:blank"),
            FakePage("https://passport.58.com/login"),
            FakePage("https://my.58.com/"),
        ],
        cookies=[{"name": "id58", "domain": ".58.com"}],
    )

    assert await is_logged_in(context) is True


@pytest.mark.asyncio
async def test_login_rejects_cookie_when_only_login_pages_are_open() -> None:
    context = FakeContext(
        pages=[FakePage("https://passport.58.com/login")],
        cookies=[{"name": "id58", "domain": ".58.com"}],
    )

    assert await is_logged_in(context) is False


@pytest.mark.asyncio
async def test_login_rejects_58_page_without_auth_cookie() -> None:
    context = FakeContext(
        pages=[FakePage("https://my.58.com/")],
        cookies=[],
    )

    assert await is_logged_in(context) is False
