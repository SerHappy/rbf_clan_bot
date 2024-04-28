from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes, ExtBot

from app.core.config import settings
from app.db.engine import UnitOfWork
from app.services.applications.application_retrieve import ApplicationRetrieveService


async def new_user_joined_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик нового пользователя."""
    message = update.message
    if not message:
        return
    logger.debug("В обработчике нового пользователя")
    new_users = message.new_chat_members
    for new_user in new_users:
        uow = UnitOfWork()
        application_service = ApplicationRetrieveService(uow)
        user_id = new_user.id
        application = await application_service.execute(user_id)
        if not application:
            logger.warning(
                (
                    f"Пользователь {user_id} не имеет активной заявки. "
                    "Невозможно получить ссылку"
                ),
            )
            return
        user_link = application.invite_link
        if not user_link:
            logger.warning(
                (
                    f"Пользователь {user_id} не имеет ссылки в заявке. "
                    "Невозможно получить ссылку"
                ),
            )
            return
        await _revoke_invite_link(context.application.bot, user_link)
        logger.debug(f"Ссылка пользователя {user_id} отозвана")


async def _revoke_invite_link(bot: ExtBot, invite_link: str) -> None:
    """Отменяет ссылку на приглашение."""
    logger.debug("In revoke invite link handler.")
    chat_id = settings.CLAN_CHAT_ID
    await bot.revoke_chat_invite_link(chat_id, invite_link)
