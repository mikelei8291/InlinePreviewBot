import re
from datetime import datetime
from typing import Self, TypedDict


class Media(TypedDict):
    photo_url: str
    thumbnail_url: str
    photo_width: int
    photo_height: int


class Metadata(TypedDict):
    hostname: str
    post_id: str
    user_id: str
    name: str
    username: str
    timestamp: datetime | str
    text: str
    media: dict[str, Media]
    url: str
    user_url: str


class Extractor(dict):
    _VALID_URL: str = ""

    def __init__(self, metadata: Metadata) -> None:
        super().__init__({
            "hostname": "",
            "post_id": "",
            "user_id": "",
            "name": "",
            "username": "",
            "timestamp": "",
            "text": "",
            "media": {},
            "url": "",
            "user_url": ""
        })
        for k, v in metadata.items():
            if v is not None:
                self[k] = v

    @classmethod
    async def _extract(cls, hostname: str, post_id: str) -> Metadata:
        raise NotImplementedError("This method should be implemented by subclasses.")

    @classmethod
    async def _match_url(cls, url: str) -> re.Match | None:
        if not cls._VALID_URL:
            return None
        if "_VALID_URL_REGEX" not in cls.__dict__:
            cls._VALID_URL_REGEX = re.compile(cls._VALID_URL)
        return cls._VALID_URL_REGEX.match(url)

    @classmethod
    async def extract(cls, url: str) -> Self | None:
        if match := await cls._match_url(url):
            metadata = await cls._extract(match.group("hostname"), match.group("id"))
            return cls(metadata)
