from telegram import Bot, LabeledPrice

from app.config import settings

PREMIUM_PAYLOAD = "premium_subscription:v1"


async def send_premium_invoice(bot: Bot, chat_id: int) -> None:
    await bot.send_invoice(
        chat_id=chat_id,
        title="Premium subscription",
        description=(
            f"{settings.premium_duration_days}-day Premium subscription for the AI assistant."
        ),
        payload=PREMIUM_PAYLOAD,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice("Premium subscription", settings.premium_price_stars)],
    )

