from __future__ import annotations
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import Feedback, User


async def get_recent_feedbacks(session: AsyncSession, *, limit: int=10, offset: int=0):
    """
    Return recent feedbacks for a user
    """
    stmt= (
        select(Feedback, User)
        .join(User, Feedback.user_id==User.id )
        .order_by(desc(Feedback.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    rows = result.all()
    out=[]
    for fb, user in rows:
        out.append({
            'id': fb.id,
            "message": fb.message,

            "created_at": fb.created_at,
            "username": fb.user.username,
            "first_name": fb.user.first_name,

        })
    return out