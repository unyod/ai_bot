from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    ActivityLog,
    Admin,
    Conversation,
    Message,
    MessageRole,
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionPlan,
    User,
)


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    language_code: str | None = None,
) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )
        session.add(user)
        await session.flush()
    else:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.language_code = language_code
    return user


async def get_or_create_active_conversation(session: AsyncSession, user_id: int) -> Conversation:
    statement = (
        select(Conversation)
        .where(Conversation.user_id == user_id, Conversation.is_active.is_(True))
        .order_by(Conversation.id.desc())
    )
    conversation = (await session.scalars(statement)).first()
    if conversation is None:
        conversation = Conversation(user_id=user_id)
        session.add(conversation)
        await session.flush()
    return conversation


async def start_new_conversation(session: AsyncSession, user_id: int) -> Conversation:
    conversations = await session.scalars(
        select(Conversation).where(Conversation.user_id == user_id, Conversation.is_active.is_(True))
    )
    for conversation in conversations:
        conversation.is_active = False
    conversation = Conversation(user_id=user_id)
    session.add(conversation)
    await session.flush()
    return conversation


async def add_message(
    session: AsyncSession,
    conversation_id: int,
    role: MessageRole,
    content: str,
    tokens_used: int | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id, role=role, content=content, tokens_used=tokens_used
    )
    session.add(message)
    await session.flush()
    return message


async def get_recent_messages(
    session: AsyncSession, conversation_id: int, limit: int
) -> list[Message]:
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    messages = list(await session.scalars(statement))
    return list(reversed(messages))


async def seed_admins(session: AsyncSession, telegram_ids: list[int]) -> None:
    for telegram_id in telegram_ids:
        if await session.scalar(select(Admin).where(Admin.telegram_id == telegram_id)) is None:
            session.add(Admin(telegram_id=telegram_id))


async def is_admin(session: AsyncSession, telegram_id: int) -> bool:
    return await session.scalar(select(Admin.id).where(Admin.telegram_id == telegram_id)) is not None


async def set_user_blocked(session: AsyncSession, telegram_id: int, blocked: bool) -> User | None:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is not None:
        user.is_blocked = blocked
    return user


async def get_all_active_user_telegram_ids(session: AsyncSession) -> list[int]:
    ids = await session.scalars(select(User.telegram_id).where(User.is_blocked.is_(False)))
    return list(ids)


async def add_log(
    session: AsyncSession, action: str, user_id: int | None = None, details: str | None = None
) -> None:
    session.add(ActivityLog(action=action, user_id=user_id, details=details))


async def get_or_create_subscription(session: AsyncSession, user_id: int) -> Subscription:
    subscription = await session.scalar(select(Subscription).where(Subscription.user_id == user_id))
    if subscription is None:
        subscription = Subscription(user_id=user_id, plan=SubscriptionPlan.free)
        session.add(subscription)
        await session.flush()
    return subscription


def is_subscription_active(subscription: Subscription, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    return (
        subscription.plan is SubscriptionPlan.premium
        and subscription.expires_at is not None
        and subscription.expires_at > now
    )


async def activate_premium(session: AsyncSession, user_id: int, duration_days: int) -> Subscription:
    subscription = await get_or_create_subscription(session, user_id)
    now = datetime.now(timezone.utc)
    starts_from = subscription.expires_at if is_subscription_active(subscription, now) else now
    subscription.plan = SubscriptionPlan.premium
    subscription.started_at = subscription.started_at or now
    subscription.expires_at = starts_from + timedelta(days=duration_days)
    return subscription


async def payment_exists(session: AsyncSession, telegram_charge_id: str) -> bool:
    return await session.scalar(
        select(Payment.id).where(Payment.telegram_charge_id == telegram_charge_id)
    ) is not None


async def create_successful_payment(
    session: AsyncSession,
    user_id: int,
    amount: int,
    currency: str,
    telegram_charge_id: str,
) -> Payment:
    payment = Payment(
        user_id=user_id,
        amount=amount,
        currency=currency,
        status=PaymentStatus.success,
        telegram_charge_id=telegram_charge_id,
    )
    session.add(payment)
    await session.flush()
    return payment


async def get_bot_stats(session: AsyncSession) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    total_users = (await session.scalar(select(func.count(User.id)))) or 0
    blocked_users = (
        await session.scalar(select(func.count(User.id)).where(User.is_blocked.is_(True)))
    ) or 0
    premium_users = (
        await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.plan == SubscriptionPlan.premium, Subscription.expires_at > now
            )
        )
    ) or 0
    total_conversations = (await session.scalar(select(func.count(Conversation.id)))) or 0
    total_messages = (await session.scalar(select(func.count(Message.id)))) or 0
    total_tokens = (await session.scalar(select(func.coalesce(func.sum(Message.tokens_used), 0)))) or 0
    successful_payments = (
        await session.scalar(select(func.count(Payment.id)).where(Payment.status == PaymentStatus.success))
    ) or 0
    total_revenue_stars = (
        await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.success, Payment.currency == "XTR"
            )
        )
    ) or 0
    return {
        "total_users": total_users,
        "blocked_users": blocked_users,
        "premium_users": premium_users,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_tokens": total_tokens,
        "successful_payments": successful_payments,
        "total_revenue_stars": total_revenue_stars,
    }

