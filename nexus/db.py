# /sd/nexus/db.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Синхронная сессия (Flask)
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/nexus_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Асинхронная сессия (Aiogram)
ASYNC_DATABASE_URL = "postgresql+asyncpg://user:password@localhost/nexus_db"
async_engine = create_async_engine(ASYNC_DATABASE_URL)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession)

# Пример использования в Flask
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Пример использования в Aiogram
async def get_async_db():
    async with AsyncSessionLocal() as db:
        yield db