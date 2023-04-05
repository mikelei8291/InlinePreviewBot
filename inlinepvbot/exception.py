import telebot
from telebot import logger
from telebot.asyncio_helper import ApiException


class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        if isinstance(exception, ApiException):
            if 400 <= exception.error_code < 500:
                raise RuntimeError(exception.description) from exception
        logger.error(exception)
