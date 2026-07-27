from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from app.config import settings
from app.handlers.chat import generate_reply_for_text
from app.handlers.common import get_active_conversation_id
from app.services.speech_service import transcribe_voice
from app.utils.logger import get_logger
from app.utils.telegram import reply_in_chunks

logger = get_logger(__name__)


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or message.voice is None:
        return
    if message.voice.file_size and message.voice.file_size > settings.max_upload_bytes:
        await message.reply_text("📦 Ovozli xabar juda katta. Iltimos, kichikroq fayl yuboring.")
        return
    conversation_id = await get_active_conversation_id(update)
    if conversation_id is None:
        return

    await context.bot.send_chat_action(message.chat_id, ChatAction.TYPING)
    voice_file = await context.bot.get_file(message.voice.file_id)
    try:
        transcript = await transcribe_voice(bytes(await voice_file.download_as_bytearray()))
    except Exception:
        logger.exception("Could not transcribe voice message")
        await message.reply_text("😔 Ovozni matnga o‘girishda xatolik yuz berdi.")
        return
    if not transcript:
        await message.reply_text("🤔 Ovozli xabardan matn ajratilmadi. Qayta yuborib ko‘ring.")
        return

    await message.reply_text(f"🎙 Eshitdim:\n{transcript}")
    try:
        answer = await generate_reply_for_text(conversation_id, transcript)
    except Exception:
        logger.exception("Could not generate voice reply")
        await message.reply_text("😔 Javob olishda xatolik yuz berdi. Keyinroq qayta urinib ko‘ring.")
        return
    await reply_in_chunks(message, answer)
