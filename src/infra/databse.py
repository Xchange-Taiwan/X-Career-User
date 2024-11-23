from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL: str = 'postgresql+asyncpg://user_connection:pg_user_password@localhost:5432/Xchange_local'
engine = create_async_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()


async def get_db(auto_commit: bool = True):
    async with SessionLocal() as db:
        try:
            yield db
            if auto_commit:
                await db.commit()  # Automatically commit changes if `auto_commit` is True
        except Exception:
            await db.rollback()  # Roll back on exception
            raise
        finally:
            await db.close()  # Ensure session is closed