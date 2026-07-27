import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from app.database import crud
from app.database.db import get_session
from app.utils.decorators import admin_only
from app.utils.logger import get_logger

logger = get_logger(__name__)

ADMIN_HELP = (
    "🛠 Admin panel\n\n"
    "/stats — umumiy statistika\n"
    "/block <telegram_id> — foydalanuvchini bloklash\n"
    "/unblock <telegram_id> — blokdan chiqarish\n"
    "/broadcast <matn> — barcha bloklanmagan foydalanuvchilarga xabar yuborish"
)


@admin_only
async def admin_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message is not None:
        await update.effective_message.reply_text(ADMIN_HELP)


@admin_only
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message is None:
        return
    async with get_session() as session:
        stats = await crud.get_bot_stats(session)
    await update.effective_message.reply_text(
        "📊 Bot statistikasi\n\n"
        f"👤 Foydalanuvchilar: {stats['total_users']}\n"
        f"⭐ Faol premium: {stats['premium_users']}\n"
        f"⛔ Bloklangan: {stats['blocked_users']}\n"
        f"💬 Suhbatlar: {stats['total_conversations']}\n"
        f"✉️ Xabarlar: {stats['total_messages']}\n"
        f"🔢 Ishlatilgan tokenlar: {stats['total_tokens']}\n"
        f"💳 Muvaffaqiyatli to‘lovlar: {stats['successful_payments']}\n"
        f"💰 Tushum: {stats['total_revenue_stars']} ⭐"
    )


@admin_only
async def block_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _set_block_status(update, context, True)


@admin_only
async def unblock_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _set_block_status(update, context, False)


async def _set_block_status(
    update: Update, context: ContextTypes.DEFAULT_TYPE, blocked: bool
) -> None:
    message = update.effective_message
    if message is None:
        return
    if not context.args:
        await message.reply_text("Foydalanish: /block <telegram_id> yoki /unblock <telegram_id>")
        return
    try:
        telegram_id = int(context.args[0])
    except ValueError:
        await message.reply_text("Telegram ID butun son bo‘lishi kerak.")
        return
    async with get_session() as session:
        user = await crud.set_user_blocked(session, telegram_id, blocked)
        if user is not None:
            await crud.add_log(
                session,
                "block_user" if blocked else "unblock_user",
                user.id,
                f"admin={update.effective_user.id if update.effective_user else 'unknown'}",
            )
    if user is None:
        await message.reply_text("Bunday foydalanuvchi topilmadi.")
        return
    await message.reply_text(
        f"Foydalanuvchi {telegram_id} {'bloklandi ⛔' if blocked else 'blokdan chiqarildi ✅'}"
    )


@admin_only
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return
    if not context.args:
        await message.reply_text("Foydalanish: /broadcast <matn>")
        return
    text = "📢 " + " ".join(context.args)
    async with get_session() as session:
        telegram_ids = await crud.get_all_active_user_telegram_ids(session)
    await message.reply_text(f"Yuborilmoqda: {len(telegram_ids)} foydalanuvchi.")
    sent = failed = 0
    for telegram_id in telegram_ids:
        try:
            await context.bot.send_message(telegram_id, text)
            sent += 1
        except Exception:
            failed += 1
            logger.warning("Broadcast send failed for Telegram user %s", telegram_id)
        await asyncio.sleep(0.05)
    async with get_session() as session:
        await crud.add_log(
            session,
            "broadcast",
            details=(
                f"admin={update.effective_user.id if update.effective_user else 'unknown'}, "
                f"sent={sent}, failed={failed}"
            ),
        )
    await message.reply_text(f"✅ Yuborildi: {sent}\n❌ Xato: {failed}")

