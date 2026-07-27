from telegram import Update
from telegram.ext import ContextTypes

from app.config import settings
from app.database import crud
from app.database.db import get_session
from app.handlers.common import get_active_conversation_id
from app.services.payment_service import PREMIUM_PAYLOAD, send_premium_invoice
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def premium_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None or await get_active_conversation_id(update) is None:
        return
    async with get_session() as session:
        db_user = await crud.get_or_create_user(session, user.id, user.username, user.first_name)
        subscription = await crud.get_or_create_subscription(session, db_user.id)
        active = crud.is_subscription_active(subscription)
    if active:
        await message.reply_text(
            f"⭐ Premium faol. Tugash vaqti: {subscription.expires_at:%Y-%m-%d %H:%M UTC}"
        )
        return
    await message.reply_text(
        f"⭐ Premium obuna\n\nNarxi: {settings.premium_price_stars} Telegram Stars\n"
        f"Muddati: {settings.premium_duration_days} kun\n\nTo‘lov uchun invoys yuborildi."
    )
    await send_premium_invoice(context.bot, message.chat_id)


async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    if query is None:
        return
    valid = (
        query.invoice_payload == PREMIUM_PAYLOAD
        and query.currency == "XTR"
        and query.total_amount == settings.premium_price_stars
    )
    if not valid:
        await query.answer(ok=False, error_message="Noto‘g‘ri to‘lov ma’lumotlari.")
        return
    await query.answer(ok=True)


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None or message.successful_payment is None:
        return
    payment = message.successful_payment
    if (
        payment.invoice_payload != PREMIUM_PAYLOAD
        or payment.currency != "XTR"
        or payment.total_amount != settings.premium_price_stars
    ):
        logger.warning("Rejected unexpected successful payment from %s", user.id)
        return
    async with get_session() as session:
        if await crud.payment_exists(session, payment.telegram_payment_charge_id):
            await message.reply_text("ℹ️ Bu to‘lov avval qayta ishlangan.")
            return
        db_user = await crud.get_or_create_user(
            session, user.id, user.username, user.first_name, user.last_name, user.language_code
        )
        await crud.create_successful_payment(
            session,
            db_user.id,
            payment.total_amount,
            payment.currency,
            payment.telegram_payment_charge_id,
        )
        subscription = await crud.activate_premium(
            session, db_user.id, settings.premium_duration_days
        )
        await crud.add_log(
            session,
            "premium_activated",
            db_user.id,
            f"amount={payment.total_amount} {payment.currency}",
        )
    await message.reply_text(
        f"✅ To‘lov qabul qilindi. Premium {subscription.expires_at:%Y-%m-%d %H:%M UTC} gacha faol."
    )

