from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config.conf import (
    DB_USER, DB_PASSWORD, DB_PORT, DB_NAME, DB_HOST, DB_SCHEMA,
    DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, DB_POOL_RECYCLE,
    DB_POOL_PRE_PING, DB_COMMAND_TIMEOUT, DB_JIT_OFF, DB_SSL
)

#DB_URL: str = 'postgresql+asyncpg://user_connection:pg_user_password@localhost:5432/Xchange_local'
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
schema_translate_map = {"schema": DB_SCHEMA}

# 動態構建 server_settings
server_settings = {}

# 是否關閉 PostgreSQL JIT (提高穩定性)
if DB_JIT_OFF:
    server_settings["jit"] = "off"

# Without this, unqualified table names hit `public` regardless of DB_SCHEMA.
# No-op when DB_SCHEMA=public.
if DB_SCHEMA:
    server_settings["search_path"] = f'"{DB_SCHEMA}", public'

# asyncpg 特定設置
connect_args = {
    "command_timeout": DB_COMMAND_TIMEOUT,  # 命令超時時間（秒）
    "server_settings": server_settings      # 服務器設置
}

# SSL 設置：RDS 強制 SSL (rds.force_ssl=1) 時必須加密連線，否則 pg_hba 會拒絕 ("no encryption")
# DB_SSL 為空時不傳，維持本機非加密連線
if DB_SSL:
    connect_args["ssl"] = DB_SSL

# 資料庫引擎配置：使用配置參數設置連接池和超時
engine = create_async_engine(
    DATABASE_URL,
    execution_options={"schema_translate_map": schema_translate_map},
    # 連接池設置
    pool_size=DB_POOL_SIZE,                    # 連接池大小
    max_overflow=DB_MAX_OVERFLOW,              # 最大溢出連接數
    pool_timeout=DB_POOL_TIMEOUT,              # 獲取連接的超時時間（秒）
    pool_recycle=DB_POOL_RECYCLE,              # 連接回收時間（秒）
    pool_pre_ping=DB_POOL_PRE_PING,            # 連接前先 ping 檢查連接是否有效
    connect_args=connect_args
)
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
