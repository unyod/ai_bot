from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import crud


async def build_context(session: AsyncSession, conversation_id: int) -> list[dict[str, str]]:
    messages = await crud.get_recent_messages(session, conversation_id, settings.max_context_messages)
    return [{"role": message.role.value, "content": message.content} for message in messages]

