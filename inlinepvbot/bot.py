from pydantic import HttpUrl, ValidationError
from pydantic.tools import parse_obj_as
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
)

from . import extractor
from .config import ConfigLoader
from .extractor.base import Extractor
from .format import Formatter

_EXTRACTORS: list[Extractor] = [getattr(extractor, _class) for _class in extractor.__all__]


class InlinePreviewBot(AsyncTeleBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = ConfigLoader().load()
        self.formatter = Formatter(self.config["template"])
        self.register_message_handler(self.messages)
        self.register_inline_handler(self.inline_url, self.inline_url_filter)
        self.register_inline_handler(self.inline_query_default, None)

    def inline_url_filter(self, query: InlineQuery) -> bool:
        try:
            return parse_obj_as(HttpUrl, query.query).tld is not None
        except ValidationError:
            return False

    async def messages(self, message: Message) -> None:
        await self.send_message(message.chat.id, "This bot can only be used in inline mode")

    async def inline_url(self, query: InlineQuery) -> None:
        for url_extractor in _EXTRACTORS:
            if data := url_extractor.extract(query.query):
                await self.answer_inline_query(
                    query.id, await self.formatter.get_inline_query_results(data), cache_time=1
                )
                return
        await self.answer_inline_query(query.id, [
            InlineQueryResultArticle(
                "unsupported",
                self.config["template"]["unsupported"]["title"],
                InputTextMessageContent(self.config["template"]["unsupported"]["message"], parse_mode="MarkdownV2"),
                url=query.query,
                description=self.config["template"]["unsupported"]["description"]
            )
        ], cache_time=1)

    async def inline_query_default(self, query: InlineQuery) -> None:
        response_text = "Invalid URL" if query.query else "No URL found"
        await self.answer_inline_query(query.id, [
            InlineQueryResultArticle(
                "invalid-url" if query.query else "no-url",
                response_text,
                InputTextMessageContent(response_text),
                description=query.query
            )
        ])
