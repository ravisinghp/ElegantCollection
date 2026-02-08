from typing import AsyncGenerator, Callable, Type
from fastapi import Depends, Request
from app.db.repositories.base import BaseRepository
import aioodbc

# ------------- MSSQL Dependency for FastAPI -------------
def _get_mssql_pool(request: Request) -> aioodbc.Pool:
    pool = getattr(request.app.state, "mssql_pool", None)
    if not pool:
        raise RuntimeError("MSSQL pool not initialized")
    return pool


# ------------- Repository Dependency for MSSQL -------------
def get_mssql_repository(repo_type: Type[BaseRepository]) -> Callable:
    async def _get_repo(
        pool: aioodbc.Pool = Depends(_get_mssql_pool)
    ) -> AsyncGenerator[BaseRepository, None]:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                yield repo_type(cur)
    return _get_repo