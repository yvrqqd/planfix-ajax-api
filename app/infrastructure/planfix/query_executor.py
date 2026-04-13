import aiohttp
from loguru import logger

from app.infrastructure.browser.session import Session
from app.utils.types import JSONLikeValue


class QueryExecutor:
    __slots__ = (
        '_domain',
        '_session',
        '_url',
    )

    def __init__(
            self,
            domain: str,
            session: Session,
    ) -> None:
        self._domain = domain
        self._session = session
        self._url = f"https://{domain}/ajax/"

    async def execute(self, query: JSONLikeValue) -> JSONLikeValue:
        if self._session.token is None or self._session.session_id is None:
            raise RuntimeError("Session is not authenticated")

        logger.debug(f"Executing query against {self._url}")

        headers = {
            'Host': self._domain,
            'X-RToken': self._session.token,
            'X-Requested-With': 'XMLHttpRequest',
        }
        cookies = {
            'Lang': 'Ru',
            'PHPSESSID': self._session.session_id,
            'RememberMeSet': '0',
            'rtoken': self._session.token,
        }

        async with aiohttp.ClientSession() as http_session:
            http_session.cookie_jar.update_cookies(cookies)
            async with http_session.post(
                    self._url,
                    headers=headers,
                    data=query,
            ) as response:
                body = await response.json(content_type=None)

                if response.status != 200:
                    logger.error(f"Planfix API error {response.status}: {body}")
                    raise RuntimeError(f"Planfix API returned status {response.status}")

                logger.debug(f"Query successful ({response.status})")
                return body
