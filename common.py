from telegram import Update

from app.database import crud
from app.database.db import get_session


async def get_active_conversation_id(update: Update) -> int | None:
    """Persist Telegram profile and return the active conversation unless the user is blocked."""
    user = update.effective_user
    message = update.effective_message
    if user is None or message is None:
        return None

    async with get_session() as session:
        db_user = await crud.get_or_create_user(
            session,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
        )
        if db_user.is_blocked:
            await message.reply_text("⛔ Botdan foydalanishingiz cheklangan.")
            return None
        conversation = await crud.get_or_create_active_conversation(session, db_user.id)
        return conversation.id

