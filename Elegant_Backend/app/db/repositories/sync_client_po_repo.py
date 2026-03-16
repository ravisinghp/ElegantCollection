from app.db.repositories.base import BaseRepository
from loguru import logger


class MSSQLRepo(BaseRepository):

    # ------------------- PO list from MSSQL ------------------- #
    @staticmethod
    async def get_po_list(app, start_date):

        try:
            async with app.state.mssql_pool.acquire() as conn:
                async with conn.cursor() as cur:

                    query = """
                    SELECT *
                    FROM ClientDB.dbo.PO_details_data
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