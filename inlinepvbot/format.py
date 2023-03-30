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
        self.unsupported_template = template["unsupported"]

    def convert_field(self, value: T, conversion: str) -> str | T:
        if conversion == "m":
            return escape_markdown(str(value))
        return super().convert_field(value, conversion)

    async def _format_message(
        self,
        data: dict[str, str | datetime | dict[str, dict[str, str]] | None],
        template: dict[str, str]
    ) -> str:
        return self.format(template["message"], **data)

    async def _format_inline_keyboard(
        self,
        data: dict[str, str | datetime | dict[str, dict[str, str]] | None],
        template: dict[str, list[list[dict[str, str]]]]
    ) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(**{k: v.format_map(data) for k, v in col.items()}) for col in row]
            for row in template.get("inline_keyboard", [])
        ])

    async def get_inline_query_results(
        self,
        data: dict[str, str | datetime | dict[str, dict[str, str]] | None]
    ) -> list[InlineQueryResultPhoto | InlineQueryResultArticle]:
        supported = data.get("post_id") is not None
        template = self.urls_template if supported else self.unsupported_template
        _id = template["id"].format_map(data)
        title = template.get("title", "").format_map(data)
        description = template.get("description", "").format_map(data)
        message = await self._format_message(data, template)
        reply_markup = await self._format_inline_keyboard(data, template)
        if data.get("media"):
            return [
                InlineQueryResultPhoto(
                    f"{_id}-{media_key}",
                    **media,
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
                InputTextMessageContent(message, parse_mode="MarkdownV2", disable_web_page_preview=not supported),
                reply_markup=reply_markup,
                url=data["url"],
                description=description
            )
        ]
