from collections.abc import Iterable

from telegram import Message


def split_text(text: str, limit: int = 4096) -> Iterable[str]:
    """Split long output at sensible boundaries for Telegram's message limit."""
    remaining = text.strip() or "I could not generate a text response."
    while len(remaining) > limit:
        break_at = max(remaining.rfind("\n", 0, limit), remaining.rfind(" ", 0, limit))
        if break_at < limit // 2:
            break_at = limit
        yield remaining[:break_at].rstrip()
        remaining = remaining[break_at:].lstrip()
    yield remaining


async def reply_in_chunks(message: Message, text: str) -> None:
    for chunk in split_text(text):
        await message.reply_text(chunk)

