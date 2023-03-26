import re
from datetime import datetime


class Extractor:
    _VALID_URL: str = ""

    def __init__(self, hostname: str, post_id: str) -> None:
        self.hostname = hostname
        self.temp_id = post_id

    async def _extract(self) -> None:
        self.post_id: str = ""
        self.user_id: str = ""
        self.name: str = ""
        self.username: str = ""
        self.timestamp: datetime | None = None
        self.text: str = ""
        self.media: dict[str, dict[str, str]] = {}
        self.url: str = ""
        self.user_url: str = ""
        raise NotImplementedError("This method should be implemented by subclasses.")

    @classmethod
    async def _match_url(cls, url: str) -> re.Match | None:
        if not cls._VALID_URL:
            return None
        if "_VALID_URL_REGEX" not in cls.__dict__:
            cls._VALID_URL_REGEX = re.compile(cls._VALID_URL)
        return cls._VALID_URL_REGEX.match(url)

    @classmethod
    async def extract(cls, url: str) -> dict[str, str | datetime | dict[str, str] | None] | None:
        if match := await cls._match_url(url):
            extractor = cls(match.group("hostname"), match.group("id"))
            await extractor._extract()
            return extractor.__dict__
