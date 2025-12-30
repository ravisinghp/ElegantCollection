from app.db.repositories.base import BaseRepository


class CategoryRepo(BaseRepository):
    
    # ------------------- check category already exists -------------------
    async def is_category_exists(self, category_name: str, user_id: int):
        query = """
        SELECT cat_id, cat_name
        FROM category_master
        WHERE LOWER(cat_name) = LOWER(%s) AND user_id = %s AND is_active = 1
        LIMIT 1
        """
        await self._cur.execute(query, (category_name, user_id))
        return await self._cur.fetchone()

    # ------------------- create category -------------------
    async def create_category(
        self, category_name: str, user_id: int, created_by: int
    ):
        query = """
        INSERT INTO category_master (cat_name, user_id, created_by)
        VALUES (%s, %s, %s)
        """
        await self._log_and_execute(query, (category_name, user_id, created_by))

    async def get_last_inserted_id(self):
        await self._cur.execute("SELECT LAST_INSERT_ID() AS cat_id")
        return await self._cur.fetchone()
    
    
    # ------------------- check keyword already exists -------------------
    async def is_keyword_exists(self, keyword_name: str, user_id: int, cat_id: int):
        query = """
        SELECT keyword_id, keyword_name
        FROM keyword_master
        WHERE LOWER(keyword_name) = LOWER(%s) AND user_id = %s AND cat_id = %s AND is_active = 1
        LIMIT 1
        """
        await self._cur.execute(query, (keyword_name, user_id, cat_id))
        return await self._cur.fetchone()    
        
    #-------------------Creating keyword------------------------
    async def create_keyword(self, keyword_name: str, user_id: int, created_by: int, cat_id: int):
        insert_query = """
            INSERT INTO keyword_master (keyword_name, is_active, created_on, user_id, created_by, cat_id)
            VALUES (%s, TRUE, NOW(), %s, %s, %s)
        """
        await self._log_and_execute(insert_query, (keyword_name, user_id, created_by, cat_id))

        # fetch inserted ID
        await self._cur.execute("SELECT LAST_INSERT_ID() AS keyword_id")
        row = await self._cur.fetchone()
        return row["keyword_id"]  
    
    # ------------------- fetch category + keyword list -------------------
    async def fetch_category_keyword_list(self, user_id: int):
        query = """
            SELECT 
                c.cat_id,
                c.cat_name AS category_name,
                k.keyword_id,
                k.keyword_name
            FROM category_master c
            LEFT JOIN keyword_master k
                ON c.cat_id = k.cat_id AND k.is_active = 1
            WHERE c.user_id = %s AND c.is_active = 1
            ORDER BY k.keyword_id DESC
        """
        await self._cur.execute(query, (user_id,))
        rows = await self._cur.fetchall()
        return rows
    
    # ------------------- delete category/keyword start -------------------
    # count keywords under category
    async def count_keywords_under_category(self, cat_id: int, user_id: int):
        query = "SELECT COUNT(*) AS total FROM keyword_master WHERE cat_id=%s AND user_id=%s AND is_active=1"
        await self._cur.execute(query, (cat_id, user_id))  # single tuple
        row = await self._cur.fetchone()
        return row["total"]

    # delete keyword only
    async def delete_keyword(self, keyword_id: int, user_id: int, cat_id: int):
        query = "DELETE FROM keyword_master WHERE keyword_id=%s AND user_id=%s AND cat_id=%s"
        await self._cur.execute(query, (keyword_id, user_id, cat_id)) 
        print("Deleted rows:", self._cur.rowcount)
        await self._cur.connection.commit()

    # delete category only
    async def delete_category(self, cat_id: int, user_id: int):
        query = "DELETE FROM category_master WHERE cat_id=%s AND user_id=%s"
        await self._cur.execute(query, (cat_id, user_id)) 
        await self._cur.connection.commit()
    # ------------------- delete category/keyword end -------------------