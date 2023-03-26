from datetime import datetime

from aiohttp import ClientSession, ClientTimeout

from .base import Extractor


class Misskey(Extractor):
    _VALID_URL = r"^https?:\/\/(?P<hostname>misskey\.(io|art))\/notes\/(?P<id>\w+)$"

    def __init__(self, hostname: str, post_id: str):
        super().__init__(hostname, post_id)

    async def _extract(self) -> None:
        async with ClientSession(timeout=ClientTimeout(total=10)) as s:
            async with s.post(
                f"https://{self.hostname}/api/notes/show", json={"noteId": self.temp_id}
            ) as res:
                data = await res.json()
                self.post_id = data["id"]
                self.user_id = data["user"]["id"]
                self.name = data["user"]["name"]
                self.username = data["user"]["username"]
                self.timestamp = datetime.fromisoformat(data["createdAt"])
                self.text = data["text"]
                self.media = {file["id"]: (file["url"], file["thumbnailUrl"]) for file in data["files"]}
                self.url = f"https://{self.hostname}/notes/{self.post_id}"
                self.user_url = f"https://{self.hostname}/@{self.username}"
