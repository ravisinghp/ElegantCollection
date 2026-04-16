from app.db.repositories.base import BaseRepository
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()

try:
    MSSQL_PO_FETCH_LIMIT = int(os.getenv("MSSQL_PO_FETCH_LIMIT"))
except ValueError:
    MSSQL_PO_FETCH_LIMIT = 500

class MSSQLRepo(BaseRepository):

    # ------------------- PO list from MSSQL ------------------- #
    @staticmethod
    async def get_po_list(app, start_date):

        try:
            async with app.state.mssql_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Client DB = Support.dbo.vPODetail
                    query = """
                    SELECT *
                    FROM Support.dbo.vPODetail
                    WHERE order_date BETWEEN ? AND GETDATE()
                    ORDER BY order_date ASC
                    """

                    await cur.execute(query, (start_date,))

                    columns = [col[0] for col in cur.description]
                    rows = await cur.fetchall()

                    logger.info(
                        f"Fetched {len(rows)} rows from MSSQL from {start_date} to current date"
                    )

                    return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logger.exception("Error fetching PO list from MSSQL")
            raise RuntimeError(f"MSSQL fetch failed: {e}") from e


    #-------------------po list from mssql-------------------#
    async def get_po_list_without_oldest_date(app):
        """
        Fetch POs from MSSQL using env-based limit.
        """
        try:
            # validate env limit once before query
            if not isinstance(MSSQL_PO_FETCH_LIMIT, int) or MSSQL_PO_FETCH_LIMIT <= 0:
                raise ValueError("MSSQL_PO_FETCH_LIMIT must be a positive integer")

            async with app.state.mssql_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Client DB = Support.dbo.vPODetail
                    query = f"""
                    SELECT TOP ({MSSQL_PO_FETCH_LIMIT}) *
                    FROM Support.dbo.vPODetail   
                    """

                    await cur.execute(query)

                    columns = [col[0] for col in cur.description]
                    rows = await cur.fetchall()

                    logger.info(
                        f"Fetched {len(rows)} rows from MSSQL (limit={MSSQL_PO_FETCH_LIMIT})"
                    )

                    return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logger.exception("Error fetching PO list from MSSQL")
            raise RuntimeError(f"MSSQL fetch failed: {e}") from e