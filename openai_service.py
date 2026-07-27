from openai import AsyncOpenAI

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())

SYSTEM_PROMPT = (
    "You are a helpful, friendly Telegram AI assistant. Reply in the same language as the user. "
    "Be accurate, concise, and say when you are uncertain."
)


async def get_chat_response(
    history: list[dict[str, str]], system_prompt: str = SYSTEM_PROMPT
) -> tuple[str, int]:
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "system", "content": system_prompt}, *history],
            temperature=0.7,
        )
    except Exception:
        logger.exception("OpenAI chat request failed")
        raise

    answer = response.choices[0].message.content or ""
    tokens_used = response.usage.total_tokens if response.usage else 0
    return answer.strip(), tokens_used

