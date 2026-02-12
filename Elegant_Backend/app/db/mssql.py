import aioodbc
from fastapi import FastAPI
from loguru import logger
from app.core.config import (
    MSSQL_HOST,
    MSSQL_PORT,
    MSSQL_USER,
    MSSQL_PWD,
    MSSQL_DB,
)

# -------------------- CONNECT TO MSSQL -------------------- #
async def connect_to_mssql(app: FastAPI):
    app.state.mssql_connected = False
    app.state.mssql_message = "MSSQL not initialized"

    if not all([MSSQL_HOST, MSSQL_DB, MSSQL_USER, MSSQL_PWD]):
        message = "MSSQL config not provided — skipping MSSQL connection"
        logger.warning(message)

        app.state.mssql_message = message
        return

    try:
        logger.info(f"Connecting to MSSQL at {MSSQL_HOST}:{MSSQL_PORT}/{MSSQL_DB}")

        dsn = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={MSSQL_HOST},{MSSQL_PORT};"
            f"DATABASE={MSSQL_DB};"
            f"UID={MSSQL_USER};"
            f"PWD={MSSQL_PWD}"
        )

        app.state.mssql_pool = await aioodbc.create_pool(
            dsn=dsn,
            autocommit=True,
            minsize=1,
            maxsize=10,
        )

        app.state.mssql_connected = True
        message = "MSSQL database connected successfully"
        app.state.mssql_message = message

        logger.info(message)

    except Exception:
        message = "Failed to connect to MSSQL database"

        app.state.mssql_pool = None
        app.state.mssql_connected = False
        app.state.mssql_message = message

        logger.exception(message)


# -------------------- CLOSE MSSQL CONNECTION -------------------- #
async def close_mssql_connection(app: FastAPI):
    """Close MSSQL pool on shutdown."""
    pool = getattr(app.state, "mssql_pool", None)
    if pool:
        pool.close()
        await pool.wait_closed()
        logger.info("MSSQL connection closed")
