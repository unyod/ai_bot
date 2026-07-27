from collections.abc import Awaitable, Callable
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from app.database import crud
from app.database.db import get_session

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]


def admin_only(handler: Handler) -> Handler:
    @wraps(handler)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user is None or update.effective_message is None:
            return
        async with get_session() as session:
            allowed = await crud.is_admin(session, update.effective_user.id)
        if not allowed:
            await update.effective_message.reply_text("⛔ This command is for administrators only.")
            return
        await handler(update, context)

    return wrapped

