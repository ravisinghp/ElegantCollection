from app.db.repositories.base import BaseRepository


class CategoryRepo(BaseRepository):

    # ------------------- create category -------------------
    async def insert_category(
        self, category_name: str, org_id: int, user_id: int, created_by: int
    ):
        query = """
        INSERT INTO category_master (cat_name, org_id, user_id, created_by)
        VALUES (%s, %s, %s, %s)
        """
        await self._log_and_execute(query, (category_name, org_id, user_id, created_by))

    async def get_last_inserted_id(self):
        await self._cur.execute("SELECT LAST_INSERT_ID() AS cat_id")
        return await self._cur.fetchone()

    # ------------------- update category -------------------
    async def update_category_record(
        self, category_id: int, category_name: str, updated_by: int
    ):
        query = """
        UPDATE category_master
        SET cat_name = %s, updated_by = %s
        WHERE cat_id = %s AND is_active = 1
        """
        await self._log_and_execute(query, (category_name, updated_by, category_id))

    # ------------------- fetch categories -------------------
    async def fetch_categories(self, org_id: int, user_id: int,page: int, limit: int):
        offset = (page - 1) * limit
        
        #For Fetching the category with corresponding keywords 
        query = """
                SELECT 
                c.cat_id AS category_id,
                c.cat_name AS category_name,
                c.is_active,
                GROUP_CONCAT(k.keyword_name ORDER BY k.keyword_name SEPARATOR ', ') AS keywords

            FROM category_master AS c
            LEFT JOIN keyword_master AS k 
                ON c.cat_id = k.cat_id
            WHERE 
                c.org_id = %s 
            GROUP BY 
                c.cat_id, c.cat_name, c.is_active
            ORDER BY 
                c.cat_id DESC
            LIMIT %s OFFSET %s;

        """
        
        query_count = """
        SELECT COUNT(*) AS total_count
        FROM category_master
        WHERE org_id = %s 
    """
        
        await self._cur.execute(query, (org_id,limit, offset))
        rows = await self._cur.fetchall()
        
    
        await self._cur.execute(query_count, (org_id))
        total_count_row = await self._cur.fetchone()
        total_count = total_count_row["total_count"] if total_count_row else 0

        return {
    "categories": rows,
    "totalCount": total_count
}
    # ------------------- check category already exists -------------------
    async def find_by_name(self, category_name: str, org_id: int):
        query = """
        SELECT cat_id, cat_name
        FROM category_master
        WHERE LOWER(cat_name) = LOWER(%s) AND org_id = %s AND is_active = 1
        LIMIT 1
        """
        await self._cur.execute(query, (category_name, org_id))
        return await self._cur.fetchone()

    # -------------------Category Status Update-----------------
    async def update_category_status(request, cat_id: int, is_active: int):
        try:
            async with request.app.state.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Check if category exists
                    check_query = (
                        "SELECT COUNT(*) FROM category_master WHERE cat_id = %s"
                    )
                    await cursor.execute(check_query, (cat_id,))
                    row = await cursor.fetchone()

                    if row[0] == 0:
                        return {"success": False, "message": "Category not found"}

                    # Update status
                    update_query = """
                        UPDATE category_master
                        SET is_active = %s
                        WHERE cat_id = %s
                    """
                    await cursor.execute(update_query, (is_active, cat_id))
                    await conn.commit()

                    return {"success": True, "message": "Status updated successfully"}
        except Exception as e:
            return {"success": False, "message": f"Database error: {str(e)}"}
