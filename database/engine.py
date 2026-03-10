import os
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .models import Base

# По умолчанию SQLite-файл в текущей рабочей директории (async через aiosqlite)

 

if DATABASE_URL.startswith("sqlite:///"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
elif DATABASE_URL.startswith("sqlite:////"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:////", "sqlite+aiosqlite:////")

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

session_factory = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


def get_engine():
    return engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return session_factory


async def init_db() -> None:
    """Создаёт все таблицы в БД."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
