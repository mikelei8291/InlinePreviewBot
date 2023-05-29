from datetime import datetime

from aiohttp import ClientSession, ClientTimeout

from .base import Extractor, Metadata


class Misskey(Extractor):
    _VALID_URL = r"^https?:\/\/(?P<hostname>misskey\.(io|art))\/notes\/(?P<id>\w+)$"

    def __init__(self, metadata: Metadata) -> None:
        super().__init__(metadata)

    @classmethod
    async def _extract(cls, hostname: str, post_id: str) -> Metadata:
        async with ClientSession(timeout=ClientTimeout(total=10)) as s:
            async with s.post(
                f"https://{hostname}/api/notes/show", json={"noteId": post_id}
            ) as res:
                data = await res.json()
                return {
                    "hostname": hostname,
                    "post_id": data["id"],
                    "user_id": data["user"]["id"],
                    "name": data["user"]["name"] or data["user"]["username"],
                    "username": data["user"]["username"],
                    "timestamp": datetime.fromisoformat(data["createdAt"]),
                    "text": data["text"],
                    "media": {
                        file["id"]: {
                            "photo_url": file["url"],
                            "thumbnail_url": file["thumbnailUrl"],
                            "photo_width": file["properties"]["width"],
                            "photo_height": file["properties"]["height"]
                        } for file in data["files"]
                    },
                    "url": f"https://{hostname}/notes/{data['id']}",
                    "user_url": f"https://{hostname}/@{data['user']['username']}"
                }
