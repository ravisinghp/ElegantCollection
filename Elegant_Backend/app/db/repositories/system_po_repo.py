import hashlib
from app.db.repositories.base import BaseRepository
from loguru import logger

class SystemPORepo(BaseRepository):

    # -------------------insert po list into mysql-------------------#
    async def insert_bulk(self, rows: list[dict]):
        """
        Insert rows into system_po_details, skipping duplicates silently.
        Returns the number of rows actually inserted.
        """
        if not rows:
            return 0

        # Step 1: Calculate hash for each row (exclude row_hash itself, sort keys for consistency)
        for row in rows:
            hash_input = "||".join(str(row[col]) for col in sorted(row.keys()) if col != "row_hash")
            row["row_hash"] = hashlib.md5(hash_input.encode()).hexdigest()

        # Step 2: Fetch existing hashes in chunks to skip duplicates
        hashes = [row["row_hash"] for row in rows]
        chunk_size = 1000
        existing_hashes = set()
        for i in range(0, len(hashes), chunk_size):
            chunk = hashes[i:i + chunk_size]
            placeholders = ", ".join(["%s"] * len(chunk))
            query = f"SELECT row_hash FROM system_po_details WHERE row_hash IN ({placeholders})"
            await self._cur.execute(query, tuple(chunk))
            existing_hashes.update(row[0] for row in await self._cur.fetchall())

        # Step 3: Keep only new rows
        filtered_rows = [row for row in rows if row["row_hash"] not in existing_hashes]
        if not filtered_rows:
            logger.info("All rows are duplicates. Nothing to insert.")
            return 0  # all rows are duplicates, nothing to insert

        # Step 4: Bulk insert (silently skip duplicates)
        columns = filtered_rows[0].keys()
        col_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT IGNORE INTO system_po_details ({col_str}) VALUES ({placeholders})"
        values = [tuple(row[col] for col in columns) for row in filtered_rows]

        try:
            await self._cur.executemany(query, values)
            await self._conn.commit()
        except Exception as e:
            # Do NOT rollback for duplicates or minor insert issues
            logger.warning(f"Minor insert issue, continuing: {e}")
            try:
                await self._conn.commit()  # commit whatever was inserted
            except Exception as commit_err:
                logger.error(f"Commit failed: {commit_err}")

        logger.info(f"Inserted {len(filtered_rows)} rows successfully (duplicates skipped).")
        return len(filtered_rows)
