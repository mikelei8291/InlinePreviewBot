import re
from datetime import datetime


class Extractor:
    _VALID_URL: str = ""

    def __init__(self, hostname: str, post_id: str) -> None:
        self.hostname = hostname
        self.temp_id = post_id
        self._extract()

    def _extract(self) -> None:
        self.url: str = ""
        self.name: str = ""
        self.user_id: str = ""
        self.username: str = ""
        self.user_url: str = ""
        self.post_id: str = ""
        self.timestamp: datetime | None = None
        self.text: str = ""
        self.media: dict[str, tuple[str, str]] = {}
        raise NotImplementedError("This method should be implemented by subclasses.")

    @classmethod
    def _match_url(cls, url: str) -> re.Match | None:
        if not cls._VALID_URL:
            return None
        if "_VALID_URL_REGEX" not in cls.__dict__:
            cls._VALID_URL_REGEX = re.compile(cls._VALID_URL)
        return cls._VALID_URL_REGEX.match(url)

    @classmethod
    def extract(cls, url: str) -> dict[str, str | datetime | dict[str, str] | None] | None:
        if match := cls._match_url(url):
            return cls(match.group("hostname"), match.group("id")).__dict__
