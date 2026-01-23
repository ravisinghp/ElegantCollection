from typing import List, Optional
from app.db.repositories.base import BaseRepository
from sqlalchemy import insert, select

class SharepointRepo(BaseRepository):

    #---------------- FETCH KEYWORDS ---------------- # 
    async def fetch_keywords(self) -> List[str]:
        """
        Fetch active keywords for a given user_id from keyword_master table.
        """
        query = """
            SELECT keyword_name 
            FROM keyword_master 
            WHERE is_active = 1
        """
        
        await self._log_and_execute(query, )
        result = await self._cur.fetchall()
        return [row['keyword_name'].lower() for row in result] if result else []
    
    # ---------------- CHECK MAIL EXISTS ---------------- #
    async def file_exists(self, user_id: int, file_hash: str) -> bool:
        query = """
            SELECT 1 
            FROM sharepoint_files 
            WHERE file_hash = %s 
            AND user_id = %s 
            AND is_active = 1 
            LIMIT 1
        """
        await self._log_and_execute(query, (file_hash, user_id))
        result = await self._cur.fetchone()
        return result is not None


    # -------------------Save Sharepoint files------------------- #
    async def save_sharepoint_file(
        self,
        user_id: int,
        file_name: str,
        file_type: str,
        file_path: str,
        file_size: int,
        folder_name: str,
        uploaded_on: Optional[str],
        created_by: int,
        file_hash: str,
        updated_by: Optional[int] = None,
    ):
        query = """
            INSERT INTO sharepoint_files (
                user_id,
                file_name,
                file_type,
                file_path,
                file_size,
                folder_name,
                uploaded_on,
                created_by,
                created_on,
                updated_by,
                updated_on,
                is_active,
                file_hash
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, NOW(),
                %s, NOW(),
                1,
                %s
            )
        """

        params = (
            user_id,
            file_name,
            file_type,
            file_path,
            file_size,
            folder_name,
            uploaded_on,
            created_by,
            updated_by or created_by,
            file_hash,
        )

        await self._log_and_execute(query, params)
        return self._cur.lastrowid
