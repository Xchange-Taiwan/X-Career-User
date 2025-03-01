from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config.conf import DB_USER, DB_PASSWORD, DB_PORT, DB_NAME, DB_HOST, DB_SCHEMA

#DB_URL: str = 'postgresql+asyncpg://user_connection:pg_user_password@localhost:5432/Xchange_local'
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
schema_translate_map = {"schema": DB_SCHEMA}
engine = create_async_engine(DATABASE_URL, execution_options={"schema_translate_map": schema_translate_map})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()


# TODO: 建議都用手動 commit 就可以了.
async def get_db():
    async with SessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()  # Roll back on exception
            raise
        finally:
            await db.close()  # Ensure session is closed


async def db_session():
    async with SessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()  # Roll back on exception
            raise
        finally:
            await db.close()  # Ensure session is closed
