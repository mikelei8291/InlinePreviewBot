import string
from datetime import datetime
from typing import Any, TypeVar

from telebot.formatting import escape_markdown
from telebot.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle,
    InlineQueryResultPhoto, InputTextMessageContent
)

T = TypeVar("T", bound=Any)


class Formatter(string.Formatter):
    def __init__(self, template: dict[str, dict[str, str | list[list[dict[str, str]]]]]) -> None:
        self.urls_template = template["urls"]

    def convert_field(self, value: T, conversion: str) -> str | T:
        if conversion == "m":
            return escape_markdown(str(value))
        return super().convert_field(value, conversion)

    async def _format_message(
        self,
        data: dict[str, str | datetime | dict[str, tuple[str, str]] | None]
    ) -> str:
        return self.format(self.urls_template["message"], **data)

    async def _format_inline_keyboard(
        self,
        data: dict[str, str | datetime | dict[str, tuple[str, str]] | None]
    ) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(**{k: v.format_map(data) for k, v in col.items()}) for col in row]
            for row in self.urls_template["inline_keyboard"]
        ])

    async def get_inline_query_results(
        self,
        data: dict[str, str | datetime | dict[str, tuple[str, str]] | None]
    ) -> list[InlineQueryResultPhoto]:
        _id = self.urls_template["id"].format_map(data)
        title = self.urls_template["title"].format_map(data)
        description = self.urls_template["description"].format_map(data)
        message = await self._format_message(data)
        reply_markup = await self._format_inline_keyboard(data)
        if data["media"]:
            return [
                InlineQueryResultPhoto(
                    f"{_id}-{media_key}",
                    *media,
                    title=title,
                    description=description,
                    caption=message,
                    parse_mode="MarkdownV2",
                    reply_markup=reply_markup
                ) for media_key, media in data["media"].items()
            ]
        return [
            InlineQueryResultArticle(
                _id,
                title,
                InputTextMessageContent(message, parse_mode="MarkdownV2"),
                reply_markup=reply_markup,
                url=data["url"],
                description=description
            )
        ]
