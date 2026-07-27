from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from app.database import crud
from app.database.db import get_session
from app.database.models import MessageRole
from app.handlers.common import get_active_conversation_id
from app.services.memory_service import build_context
from app.services.openai_service import get_chat_response
from app.utils.logger import get_logger
from app.utils.telegram import reply_in_chunks

logger = get_logger(__name__)


async def generate_reply_for_text(conversation_id: int, user_text: str) -> str:
    """Store the user message, send the recent context to the model, then store its reply."""
    async with get_session() as session:
        await crud.add_message(session, conversation_id, MessageRole.user, user_text)
        history = await build_context(session, conversation_id)

    answer, tokens_used = await get_chat_response(history)

    async with get_session() as session:
        await crud.add_message(
            session, conversation_id, MessageRole.assistant, answer, tokens_used=tokens_used
        )
    return answer


async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return
    conversation_id = await get_active_conversation_id(update)
    if conversation_id is None:
        return

    await context.bot.send_chat_action(message.chat_id, ChatAction.TYPING)
    try:
        answer = await generate_reply_for_text(conversation_id, message.text)
    except Exception:
        logger.exception("Could not generate text reply")
        await message.reply_text("😔 Javob olishda xatolik yuz berdi. Keyinroq qayta urinib ko‘ring.")
        return
    await reply_in_chunks(message, answer)


async def new_conversation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    if user is None or message is None:
        return
    async with get_session() as session:
        db_user = await crud.get_or_create_user(
            session, user.id, user.username, user.first_name, user.last_name, user.language_code
        )
        if db_user.is_blocked:
            await message.reply_text("⛔ Botdan foydalanishingiz cheklangan.")
            return
        await crud.start_new_conversation(session, db_user.id)
    await message.reply_text("🆕 Yangi suhbat boshlandi. Oldingi kontekst endi ishlatilmaydi.")

