import asyncio
from os import getenv

from .bot import InlinePreviewBot

if __name__ == "__main__":
    print("Bot running")
    bot = InlinePreviewBot(getenv("BOT_TOKEN"))
    asyncio.run(bot.polling())
