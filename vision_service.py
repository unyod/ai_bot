import base64

from app.config import settings
from app.services.openai_service import client
from app.utils.logger import get_logger

logger = get_logger(__name__)
DEFAULT_IMAGE_PROMPT = "Describe what is in this image clearly and helpfully."


async def analyze_image(image_bytes: bytes, prompt: str = DEFAULT_IMAGE_PROMPT) -> tuple[str, int]:
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"},
                        },
                    ],
                }
            ],
            max_tokens=800,
        )
    except Exception:
        logger.exception("OpenAI image analysis request failed")
        raise
    answer = response.choices[0].message.content or ""
    tokens_used = response.usage.total_tokens if response.usage else 0
    return answer.strip(), tokens_used

