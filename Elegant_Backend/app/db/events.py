from typing import Optional
#import asyncpg
#import asyncio
import asyncmy
from fastapi import FastAPI
from loguru import logger

from app.core.config import HOST, PORT, USER, PWD, DB, DATABASE_URL, MAX_CONNECTIONS_COUNT, MIN_CONNECTIONS_COUNT


#loop = asyncio.get_event_loop()
# async def connect_to_db(app: FastAPI) -> None:
#     logger.info("Connecting to {0}", repr(DATABASE_URL))

#     app.state.pool = await asyncmy.create_pool(
#         host=str(HOST),
#         port=int(PORT),
#         user=str(USER),
#         password=str(PWD),
#         db=str(DB),
#         autocommit=True,
#     )

#     '''
#     app.state.pool = await asyncpg.create_pool(
#         str(DATABASE_URL),
#         min_size=MIN_CONNECTIONS_COUNT,
#         max_size=MAX_CONNECTIONS_COUNT,
#     )
#     '''
#     logger.info("Connection established")
async def connect_to_db(app: FastAPI) -> None:

    logger.info("Connecting to {0}", repr(DATABASE_URL))

    try:

        app.state.pool = await asyncmy.create_pool(

            host=str(HOST),

            port=int(PORT),

            user=str(USER),

            password=str(PWD),

            db=str(DB),

            autocommit=True,

        )

        logger.info("✅ Connection established")

    except Exception as e:

        logger.error(f"⚠ Failed to connect to DB: {e}")

        app.state.pool = None  # allow server to start



async def close_db_connection(app: FastAPI) -> None:
    logger.info("Closing connection to database")

    # Close pool gracefully; asyncmy provides close() and wait_closed()
    pool = getattr(app.state, "pool", None)  # type: Optional[object]
    if pool is None:
        logger.info("No DB pool to close")
        return
    try:
        pool.close()
    except Exception:
        pass
    try:
        await pool.wait_closed()  # type: ignore[attr-defined]
    except Exception:
        pass

    logger.info("Connection closed")
