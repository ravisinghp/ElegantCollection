from app.db.repositories.base import BaseRepository
from loguru import logger

class MSSQLRepo(BaseRepository):

    #-------------------po list from mssql-------------------#
    async def get_po_list(self, limit: int = None):
        """
        Fetch POs from MSSQL directly, no ORDER BY.
        - limit: maximum number of rows to fetch (None = all)
        """
        try:
            # Direct query
            if limit:
                query = f"SELECT TOP {limit} * FROM client_po_details_data"
            else:
                query = "SELECT * FROM client_po_details_data"

            await self._cur.execute(query)

            columns = [col[0] for col in self._cur.description]
            rows = await self._cur.fetchall()

            logger.info(f"Fetched {len(rows)} rows from MSSQL")
            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            logger.exception("Error fetching PO list from MSSQL")
            raise RuntimeError(f"MSSQL fetch failed: {e}") from e
