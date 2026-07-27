from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from app.config import settings
from app.database import crud
from app.database.db import get_session
from app.database.models import MessageRole
from app.handlers.common import get_active_conversation_id
from app.services.vision_service import DEFAULT_IMAGE_PROMPT, analyze_image
from app.utils.logger import get_logger
from app.utils.telegram import reply_in_chunks

logger = get_logger(__name__)


async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.photo:
        return
    photo = message.photo[-1]
    if photo.file_size and photo.file_size > settings.max_upload_bytes:
        await message.reply_text("📦 Rasm juda katta. Kichikroq rasm yuboring.")
        return
    conversation_id = await get_active_conversation_id(update)
    if conversation_id is None:
        return

    await context.bot.send_chat_action(message.chat_id, ChatAction.UPLOAD_PHOTO)
    try:
        photo_file = await context.bot.get_file(photo.file_id)
        prompt = message.caption or DEFAULT_IMAGE_PROMPT
        answer, tokens_used = await analyze_image(
            bytes(await photo_file.download_as_bytearray()), prompt
        )
    except Exception:
        logger.exception("Could not analyse image")
        await message.reply_text("😔 Rasmni tahlil qilishda xatolik yuz berdi.")
        return

    async with get_session() as session:
        await crud.add_message(
            session, conversation_id, MessageRole.user, f"[Rasm] {prompt}"
        )
        await crud.add_message(
            session, conversation_id, MessageRole.assistant, answer, tokens_used=tokens_used
        )
    await reply_in_chunks(message, answer)

