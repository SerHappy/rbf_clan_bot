from handlers.admins import register_admin_handlers
from handlers.chat import register_chat_handlers
from handlers.empty import unknown_handler
from telegram.ext import Application, MessageHandler, filters

from app.handlers.application import register_application_handlers


def add_all_handlers(application: Application) -> None:
    """Регистрация всех обработчиков."""
    register_chat_handlers(application)
    register_application_handlers(application)
    register_admin_handlers(application)
    application.add_handler(MessageHandler(filters.ALL, unknown_handler))
