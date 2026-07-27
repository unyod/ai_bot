from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from app.config import settings
from app.database import crud
from app.database.db import get_session
from app.database.models import MessageRole
from app.handlers.common import get_active_conversation_id
from app.services.openai_service import get_chat_response
from app.services.pdf_service import extract_text
from app.utils.logger import get_logger
from app.utils.telegram import reply_in_chunks

logger = get_logger(__name__)
SUPPORTED_EXTENSIONS = (".pdf", ".docx")
DOCUMENT_SYSTEM_PROMPT = (
    "The user has sent a document. Answer their request from the document text. "
    "If no question was asked, provide a concise summary and the key points. "
    "Use the user's language."
)


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or message.document is None:
        return
    document = message.document
    filename = document.file_name or "document"
    if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
        await message.reply_text("📎 Hozircha faqat PDF va DOCX fayllarni qabul qilaman.")
        return
    if document.file_size and document.file_size > settings.max_upload_bytes:
        await message.reply_text("📦 Fayl juda katta. Iltimos, kichikroq PDF yoki DOCX yuboring.")
        return
    conversation_id = await get_active_conversation_id(update)
    if conversation_id is None:
        return

    await context.bot.send_chat_action(message.chat_id, ChatAction.TYPING)
    try:
        document_file = await context.bot.get_file(document.file_id)
        text = extract_text(bytes(await document_file.download_as_bytearray()), filename)
    except Exception:
        logger.exception("Could not extract document text: %s", filename)
        await message.reply_text("😔 Fayldan matn ajratib bo‘lmadi. U shikastlangan yoki himoyalangan bo‘lishi mumkin.")
        return
    if not text:
        await message.reply_text("🤔 Fayldan matn topilmadi. Skan qilingan fayllar uchun OCR kerak bo‘lishi mumkin.")
        return

    question = message.caption or "Hujjatning qisqacha xulosasi va asosiy fikrlarini bering."
    prompt = (
        f"Fayl nomi: {filename}\n\nHujjat matni:\n---\n"
        f"{text[:settings.max_document_chars]}\n---\n\nFoydalanuvchi so‘rovi: {question}"
    )
    try:
        answer, tokens_used = await get_chat_response(
            [{"role": "user", "content": prompt}], DOCUMENT_SYSTEM_PROMPT
        )
    except Exception:
        logger.exception("Could not generate document answer")
        await message.reply_text("😔 Hujjatni tahlil qilishda xatolik yuz berdi.")
        return

    async with get_session() as session:
        await crud.add_message(
            session, conversation_id, MessageRole.user, f"[Fayl: {filename}] {question}"
        )
        await crud.add_message(
            session, conversation_id, MessageRole.assistant, answer, tokens_used=tokens_used
        )
    await reply_in_chunks(message, answer)

