import argparse
import asyncio
import logging
import sys
import traceback
from importlib.metadata import distribution
from os import getenv
from pathlib import Path

from pydantic import HttpUrl, ValidationError
from pydantic.tools import parse_obj_as
from telebot import logger
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
)

from . import extractor
from .config import ConfigLoader
from .exception import ExceptionHandler
from .extractor.base import Extractor
from .format import Formatter

_EXTRACTORS: list[Extractor] = [getattr(extractor, _class) for _class in extractor.__all__]


class InlinePreviewBot(AsyncTeleBot):
    """The main class of the bot."""

    def __init__(self, *args, cache_time: int | None = None, config_path: Path | None = None, **kwargs):
        """Initialize the bot with arguments.

        `args` and `kwargs` are positional and keyword arguments of the `AsyncTeleBot` class, respectively.
        Optionally, a `cache_time` can be specified and will be used in all `AsyncTeleBot.answer_inline_query()`
        calls to set the cache time of the result on the API server. Also, the path to the configuration
        file of the bot can be specified with the `config_path` argument, and the specified file will be
        loaded as the configuration, instead of using paths pre-defined in the `ConfigLoader` class.

        - args: Positional arguments to the `AsyncTeleBot`.
        - cache_time: The time in seconds that the result of the inline query may be cached
          on the API server. Default value of the Telegram official API server is 300 seconds.
        - config_path: The path to the configuration file of the bot. If not specified, a set of
          platform-specific paths will be used.
        - kwargs: Keyword arguments to the `AsyncTeleBot`.
        """
        super().__init__(*args, **kwargs)
        self.cache_time = cache_time
        self.config = ConfigLoader(config_path).load()
        self.formatter = Formatter(self.config["template"])
        self.register_message_handler(self.messages)
        self.register_inline_handler(self.inline_url, self.inline_url_filter)
        self.register_inline_handler(self.inline_query_default, None)

    def inline_url_filter(self, query: InlineQuery) -> bool:
        """Test if inputs from inline queries are valid URLs.

        - query: The `InlineQuery` object to be tested.
        - return: `True` if the query string is a valid URL, `False` otherwise.
        """
        try:
            return parse_obj_as(HttpUrl, query.query).tld is not None
        except ValidationError:
            return False

    async def messages(self, message: Message) -> None:
        """Handler for text messages.

        Currently, this bot will reply to any text messages with a prompt indicating that the bot can
        only be used in inline mode.

        - message: The message to be handled.
        """
        await self.send_message(message.chat.id, "This bot can only be used in inline mode")

    async def inline_url(self, query: InlineQuery) -> None:
        """Handler for inline queries that are valid URLs.

        The query string will be tested by extractors in the `_EXTRACTORS` list.
        If any one of the extractors in the list successfully extracted data from the URL, the result would
        be generated from the "url" message template specified in the configuration file.
        If no extractor was able to extract data from the URL, the user would be prompted that the URL is
        unsupported, and the result would be generated from the "unsupported" message template specified in
        the configuration file.

        - query: The inline query to be handled.
        """
        data = {"url": query.query}
        for url_extractor in _EXTRACTORS:
            if result := await url_extractor.extract(query.query):
                data = result
                break
        await self.answer_inline_query(
            query.id, await self.formatter.get_inline_query_results(data), cache_time=self.cache_time
        )

    async def inline_query_default(self, query: InlineQuery) -> None:
        """Handler for inline queries that are empty strings or invalid URLs.

        A default response will be generated based on whether the query string is empty or not.
        If the query string is empty, the result will be "No URL found". Otherwise, the result will be
        "Invalid URL".

        - query: The inline query to be handled.
        """
        response_text = "Invalid URL" if query.query else "No URL found"
        await self.answer_inline_query(query.id, [
            InlineQueryResultArticle(
                "invalid-url" if query.query else "no-url",
                response_text,
                InputTextMessageContent(response_text),
                description=query.query
            )
        ], cache_time=self.cache_time)


def main() -> int | None:
    dist = distribution(__package__)
    parser = argparse.ArgumentParser(description=dist.metadata["Summary"])
    parser.add_argument("-V", "--version", action="version", version=f"{dist.name} {dist.version}")
    runtime_options = parser.add_argument_group("runtime options")
    runtime_options.add_argument("-c", "--config", type=Path, help="specify the path of the configuration file")
    runtime_options.add_argument("-q", "--quiet", action="store_true", help="disable all logging")
    runtime_options.add_argument("-v", "--verbose", action="store_true", help="enable verbose logging")
    args = parser.parse_args()
    cache_time = None
    if args.quiet:
        logging.disable()
    elif args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug(f"Command line arguments: {sys.argv[1:]}")
        cache_time = 1
    else:
        logger.setLevel(logging.INFO)
    logging.Formatter.default_msec_format = "%s.%03d"
    try:
        if not (token := getenv("BOT_TOKEN")):
            raise RuntimeError("The BOT_TOKEN environment variable was not set")
        bot = InlinePreviewBot(
            token, cache_time=cache_time, config_path=args.config, exception_handler=ExceptionHandler()
        )
        asyncio.run(bot.polling(non_stop=True))
    except Exception as e:
        logger.critical(e)
        logger.debug(traceback.format_exc())
        return 1
