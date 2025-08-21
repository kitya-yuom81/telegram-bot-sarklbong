from idlelib.configdialog import changes

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import User, Feedback

async def get_or_create_user(session: AsyncSession, *, tg_id: int, username: str | None, first: str | None, lang: str | None) -> User:
    res = await session.execute(select(User).where(User.tg_id == tg_id))
    user = res.scalar_one_or_none()
    if user is None:
        user = User(tg_id=tg_id, username=username, first_name=first, language=lang)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        changed = False
        if user.username != username:
            user.username = username; changed = True
        if user.first_name != first:
            user.first_name = first; changed = True
        if user.language != lang:
            user.language = lang; changed = True
        if changed:
            await session.commit()
    return user

async def create_feedback(session: AsyncSession, *, user_id: int, message: str) -> Feedback:
    fb = Feedback(user_id=user_id, message=message)
    session.add(fb)
    await session.commit()
    await session.refresh(fb)
    return fb

async def counts(session: AsyncSession) -> tuple[int, int]:
    users = await session.scalar(select(func.count(User.id)))
    fbs = await session.scalar(select(func.count(Feedback.id)))
    return (users or 0, fbs or 0)


