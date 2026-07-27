from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from app.config import settings
from app.handlers.admin import (
    admin_help_handler,
    block_handler,
    broadcast_handler,
    stats_handler,
    unblock_handler,
)
from app.handlers.chat import chat_handler, new_conversation_handler
from app.handlers.documents import document_handler
from app.handlers.image import image_handler
from app.handlers.start import start_handler
from app.handlers.subscription import (
    precheckout_handler,
    premium_handler,
    successful_payment_handler,
)
from app.handlers.voice import voice_handler
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def error_handler(update: object, context: object) -> None:
    logger.error("Unhandled Telegram update error", exc_info=getattr(context, "error", None))


def build_application() -> Application:
    application = Application.builder().token(settings.bot_token.get_secret_value()).build()
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("new", new_conversation_handler))
    application.add_handler(CommandHandler("premium", premium_handler))
    application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))

    application.add_handler(CommandHandler("admin", admin_help_handler))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(CommandHandler("block", block_handler))
    application.add_handler(CommandHandler("unblock", unblock_handler))
    application.add_handler(CommandHandler("broadcast", broadcast_handler))

    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    application.add_handler(MessageHandler(filters.PHOTO, image_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    application.add_error_handler(error_handler)
    return application
