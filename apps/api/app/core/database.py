from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Backward-compatible alias for background workers and services.
async_session_maker = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def _sync_schema(sync_conn):
    Base.metadata.create_all(sync_conn)
    if "sqlite" in settings.DATABASE_URL:
        try:
            # Handle SQLite missing columns automatically
            raw_conn = sync_conn.connection.dbapi_connection
            if hasattr(raw_conn, "cursor"):
                cur = raw_conn.cursor()
                for table_name, table in Base.metadata.tables.items():
                    try:
                        cur.execute(f"PRAGMA table_info({table_name})")
                        existing_cols = {row[1]: row for row in cur.fetchall()}
                        if not existing_cols:
                            continue
                        for col in table.columns:
                            if col.name not in existing_cols:
                                col_type = "TEXT"
                                if "int" in str(col.type).lower():
                                    col_type = "INTEGER"
                                elif "bool" in str(col.type).lower():
                                    col_type = "BOOLEAN"
                                elif "float" in str(col.type).lower():
                                    col_type = "REAL"
                                
                                default_clause = ""
                                if col.default is not None and col.default.arg is not None:
                                    if isinstance(col.default.arg, (int, float, bool)):
                                        default_clause = f" DEFAULT {col.default.arg}"
                                    elif isinstance(col.default.arg, str):
                                        default_clause = f" DEFAULT '{col.default.arg}'"
                                
                                sql = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause}"
                                cur.execute(sql)
                    except Exception:
                        pass
        except Exception:
            pass


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(_sync_schema)
