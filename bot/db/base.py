# bot/db/base.py
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
Session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)

async def init_db() -> None:
    # import models so metadata knows them
    from . import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # sanity ping
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
