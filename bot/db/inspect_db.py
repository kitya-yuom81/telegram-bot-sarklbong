import asyncio
from sqlalchemy import select
from bot.db.base import Session, init_db
from bot.db.models import User, Feedback

async def main():
    await init_db()
    async with Session() as s:
        users = (await s.execute(select(User))).scalars().all()
        feedbacks = (await s.execute(select(Feedback))).scalars().all()

        print("Users:")
        for u in users:
            print(u.id, u.tg_id, u.username, u.first_name, u.language)

        print("\nFeedbacks:")
        for f in feedbacks:
            print(f.id, f.user_id, f.message, f.created_at)

if __name__ == "__main__":
    asyncio.run(main())
