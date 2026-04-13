import asyncio
from functools import partial

from loguru import logger
from playwright.async_api import BrowserContext, Response

from app.domain.credentials import Credentials
from app.infrastructure.browser.browser_session import BrowserSession


class Session:
    __slots__ = (
        '_domain',
        '_base_url',
        '_login_url',
        '_creds',
        '_token',
        '_session_id',
        '_browser_session',
        '_timeout',
    )

    def __init__(
            self,
            domain: str,
            credentials: Credentials,
            browser_session: BrowserSession,
            timeout: float = 30000.0,
    ) -> None:
        self._domain: str = domain
        self._base_url: str = f"https://{domain}"
        self._login_url: str = f"{self._base_url}/?action=login"

        self._creds: Credentials = credentials

        self._token: str | None = None
        self._session_id: str | None = None

        self._browser_session: BrowserSession = browser_session
        self._timeout: float = timeout

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def domain(self) -> str:
        return self._domain

    async def create(self) -> None:
        await self._capture_tokens()

    async def _capture_tokens(self) -> None:
        timeout: float = self._timeout
        logger.debug(f"Authenticating at {self._login_url}")

        assert self._browser_session.browser is not None, "Browser not connected"
        context = await self._browser_session.browser.new_context()
        page = await context.new_page()

        token_future: asyncio.Future[str] = self._browser_session.loop.create_future()
        session_id_future: asyncio.Future[str] = self._browser_session.loop.create_future()

        page.on(
            event="response",
            f=partial(
                self._intercept_response,
                context=context,
                token_future=token_future,
                session_id_future=session_id_future,
            )
        )

        await page.goto(self._login_url, timeout=timeout)
        await page.wait_for_selector(selector='input[name="tbUserName"]', timeout=timeout)

        username_field = await page.query_selector('input[name="tbUserName"]')
        password_field = await page.query_selector('input[name="tbUserPassword"]')
        assert username_field is not None, "Username field not found"
        assert password_field is not None, "Password field not found"

        await username_field.fill(self._creds.username)
        await password_field.fill(self._creds.password.get_secret_value())
        await password_field.press('Enter')
        logger.debug("Credentials submitted, waiting for tokens")

        token, session_id = await asyncio.wait_for(
            asyncio.gather(token_future, session_id_future),
            timeout=timeout,
        )
        self._token = token
        self._session_id = session_id
        logger.info(f"Session authenticated for {self._domain}")

        await page.close()
        await context.close()

    async def _intercept_response(
            self,
            response: Response,
            *,
            context: BrowserContext,
            token_future: asyncio.Future[str],
            session_id_future: asyncio.Future[str],
    ) -> None:
        if response.url == f"{self._base_url}/j/online/ping":
            cookies = await context.cookies(response.url)
            for cookie in cookies:
                if cookie['name'] == 'PHPSESSID':
                    session_id_future.set_result(cookie['value'])

                if cookie['name'] == 'rtoken':
                    token_future.set_result(cookie['value'])
