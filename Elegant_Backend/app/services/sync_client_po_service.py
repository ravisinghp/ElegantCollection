from loguru import logger

class SyncClientPOService:

    def __init__(self, mssql_repo, mysql_repo):
        self.mssql_repo = mssql_repo
        self.mysql_repo = mysql_repo

    async def sync_po(self):
        try:
            #-------------Read from MSSQL-------------
            rows = await self.mssql_repo.get_po_list()

            if not rows:
                logger.info("No rows found in MSSQL to sync.")
                return {
                    "read_from_mssql": 0,
                    "inserted_into_mysql": 0
                }

            #------------Insert into MySQL-------------
            try:
                inserted = await self.mysql_repo.insert_bulk(rows)
            except Exception as insert_err:
                logger.exception("Error inserting rows into MySQL")
                raise RuntimeError(f"MySQL insert failed: {insert_err}") from insert_err

            if inserted == 0:
                logger.warning("All records already exist in MySQL. No new rows inserted.")
                return {
                    "read_from_mssql": len(rows),
                    "inserted_into_mysql": 0
                }

            logger.info(f"Successfully inserted {inserted} rows into MySQL.")
            return {
                "read_from_mssql": len(rows),
                "inserted_into_mysql": inserted
            }

        except Exception as e:
            # Catch any other unexpected errors (MSSQL connection, fetch issues, etc.)
            logger.exception("Unexpected error during PO sync")
            raise RuntimeError(f"PO sync failed: {e}") from e
