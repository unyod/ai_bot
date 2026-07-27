import io

from app.config import settings
from app.services.openai_service import client
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def transcribe_voice(file_bytes: bytes, filename: str = "voice.ogg") -> str:
    audio_file = io.BytesIO(file_bytes)
    audio_file.name = filename
    try:
        response = await client.audio.transcriptions.create(
            model=settings.whisper_model, file=audio_file
        )
    except Exception:
        logger.exception("OpenAI transcription request failed")
        raise
    return response.text.strip()

