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
    """
    Connect to MSSQL and store pool in app state.
    If MSSQL config is missing, skip connection safely.
    """

    # SAFETY CHECK (VERY IMPORTANT)
    if not all([MSSQL_HOST, MSSQL_DB, MSSQL_USER, MSSQL_PWD]):
        logger.warning("MSSQL config not provided — skipping MSSQL connection")
        return

    try:
        logger.info(
            f"Connecting to MSSQL at {MSSQL_HOST}:{MSSQL_PORT}/{MSSQL_DB}"
        )

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

        logger.info("MSSQL connection established!")

    except Exception as e:
        logger.exception("Failed to connect to MSSQL")
        # App should still run even if MSSQL fails
        app.state.mssql_pool = None


# -------------------- CLOSE MSSQL CONNECTION -------------------- #
async def close_mssql_connection(app: FastAPI):
    """Close MSSQL pool on shutdown."""
    pool = getattr(app.state, "mssql_pool", None)
    if pool:
        pool.close()
        await pool.wait_closed()
        logger.info("MSSQL connection closed")
