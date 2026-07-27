from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.common import get_active_conversation_id

WELCOME_TEXT = (
    "👋 Assalomu alaykum, {name}!\n\n"
    "Men AI yordamchiman. Menga matn, ovozli xabar, rasm yoki PDF/DOCX yuboring. "
    "Suhbat kontekstini eslab qolaman.\n\n"
    "Yangi suhbat boshlash: /new\nPremium: /premium"
)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await get_active_conversation_id(update) is None:
        return
    if update.effective_message is not None and update.effective_user is not None:
        await update.effective_message.reply_text(
            WELCOME_TEXT.format(name=update.effective_user.first_name or "do‘stim")
        )

