from typing import List, Optional
from app.db.repositories.base import BaseRepository
from sqlalchemy import insert, select
from fastapi import APIRouter, HTTPException,Query,Request
from typing import List, Tuple
from typing import Any,Dict


insert_sharepoint_po_details = """
INSERT INTO sharepoint_po_details (
    sharepoint_file_id,
    user_id,
    po_number,
    customer_name,
    vendor_number,
    po_date,
    delivery_date,
    cancel_date,
    gold_karat,
    ec_style_number,
    customer_style_number,
    color,
    quantity,
    description,
    created_by,
    gold_lock
) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
"""


GET_ALL_SHAREPOINT_PO_DETAILS = """
SELECT * FROM sharepoint_po_details WHERE active = 1
"""

GET_ALL_SYSTEM_PO_DETAILS = """
SELECT * FROM system_po_details WHERE active = 1
"""

GET_ALL_SHAREPOINT_MISMATCHES = """
SELECT sharepoint_po_det_id, system_po_id, mismatch_attribute
FROM sharepoint_po_mismatch_report
WHERE active = 1
"""

GET_EXISTING_SHAREPOINT_PO_MISSING_BY_SYSTEM_PO = """
SELECT 1
FROM sharepoint_po_missing_report
WHERE sharepoint_po_det_id = %s
  AND mismatch_attribute = 'po_missing'
LIMIT 1
"""

INSERT_SHAREPOINT_PO_MISSING = """
INSERT INTO sharepoint_po_missing_report (
    sharepoint_po_det_id,
    user_id,
    system_po_id,
    mismatch_attribute,
    system_value,
    scanned_value,
    comment
) VALUES (%s,%s, %s, %s, %s, %s, %s)
"""

INSERT_SHAREPOINT_MISMATCH = """
INSERT INTO sharepoint_po_mismatch_report (
    sharepoint_po_det_id,
    user_id,
    system_po_id,
    mismatch_attribute,
    system_value,
    scanned_value,
    comment
) VALUES (%s,%s, %s, %s, %s, %s, %s)
"""
class SharepointRepo(BaseRepository):
    
    
    #-------------------Fetching total document analyzed----------------------
    async def fetch_documents_analyzed_by_user_id(user_id: int, request: Request) -> int:
        query = """
         SELECT
        COUNT(s.sharepoint_file_id )
    FROM
        POlyticsAI.sharepoint_files s
    WHERE
        s.user_id = %s
        AND s.is_active = 1;
        """
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (user_id, ))
                row = await cursor.fetchone()
                return int(row[0]) if row else 0
    
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
    
    
    #---------------Insert PO Missing Data---------------#
    async def insert_po_missing(
        self,
        *,
        sharepoint_po_det_id: int,
        user_id: int,
        system_po_id: int | None,
        attribute: str,
        system_value: str,
        scanned_value: str,
        comment: str,
    ) -> int:

        await self._log_and_execute(
            INSERT_SHAREPOINT_PO_MISSING,
            (
                sharepoint_po_det_id,
                user_id,
                system_po_id,
                attribute,
                system_value,
                scanned_value,
                comment,
            ),
        )

        last_id = self._cur.lastrowid
        await self._cur.connection.commit()

        if not last_id:
            raise RuntimeError("Failed to insert PO missing report")

        return int(last_id)

    
    #---------------Insert PO Mismatch Data---------------#
    async def insert_mismatch(
        self,
        *,
        sharepoint_po_det_id: int,
        user_id: int,
        system_po_id: int,
        field: str,
        system_value: str,
        scanned_value: str,
        comment: str,
    ) -> int:

        await self._log_and_execute(
            INSERT_SHAREPOINT_MISMATCH,
            (
                sharepoint_po_det_id,
                user_id,
                system_po_id,
                field,
                system_value,
                scanned_value,
                comment,
            ),
        )

        last_id = self._cur.lastrowid
        await self._cur.connection.commit()

        if not last_id:
            raise RuntimeError("Failed to insert mismatch report")

        return int(last_id)
    
    # -------------------Insert Sharepoint PO details------------------- #
    async def insert_sharepoint_po_details(
        self,
        *,
        sharepoint_file_id:int,
        user_id: int,
        po_number: Optional[str],
        customer_name: Optional[str],
        vendor_number: Optional[str],
        po_date: Optional[str],
        delivery_date: Optional[str],
        cancel_date: Optional[str],
        gold_karat: Optional[str],
        ec_style_number: Optional[str],
        customer_style_number: Optional[str],
        color: Optional[str],
        quantity: Optional[str],
        description: Optional[str],
        created_by: Optional[int],
        gold_lock: Optional[str] ,
    ) -> int:
        
        await self._log_and_execute(
            insert_sharepoint_po_details,
            (
                sharepoint_file_id,
                user_id,
                po_number,
                customer_name,
                vendor_number,
                po_date,
                delivery_date,
                cancel_date,
                gold_karat,
                ec_style_number,
                customer_style_number,
                color,
                quantity,
                description,
                created_by,
                gold_lock,
            ),
        )

        last_id = self._cur.lastrowid
        await self._cur.connection.commit()

        if not last_id:
            raise RuntimeError("Failed to retrieve inserted po_details id")

        return int(last_id)
    
    
    
    async def get_po_details_by_ids(
        self,
        sharepoint_po_det_ids: list[int],
    ):
        if not sharepoint_po_det_ids:
            return []

        placeholders = ",".join(["%s"] * len(sharepoint_po_det_ids))

        query = f"""
            SELECT *
            FROM sharepoint_po_details
            WHERE active = 1
            AND sharepoint_po_det_id IN ({placeholders})
        """

        await self._log_and_execute(query, tuple(sharepoint_po_det_ids))
        return await self._cur.fetchall()
    
    
    async def get_system_pos_by_po_numbers(
        self,
        po_numbers: list[str],
    ):
        if not po_numbers:
            return []

        placeholders = ",".join(["%s"] * len(po_numbers))

        query = f"""
            SELECT *
            FROM system_po_details
            WHERE active = 1
            AND po_number IN ({placeholders})
        """

        await self._log_and_execute(query, tuple(po_numbers))
        return await self._cur.fetchall()
    
    
    async def po_missing_exists(
        self,
        *,
        user_id: int,
        sharepoint_po_det_id: int,
        system_po_id: int | None,
        mismatch_attribute: str,
        scanned_value: str,
        system_value: str,
    ) -> bool:

        query = """
            SELECT 1
            FROM sharepoint_po_missing_report
            WHERE active = 1
            AND user_id = %s
            AND sharepoint_po_det_id = %s
            AND mismatch_attribute = %s
            AND scanned_value = %s
            AND system_value = %s
            LIMIT 1
        """

        await self._log_and_execute(
            query,
            (
                user_id,
                sharepoint_po_det_id,
                mismatch_attribute,
                scanned_value,
                system_value,
            ),
        )

        return await self._cur.fetchone() is not None
    
    
    async def mismatch_exists(
        self,
        *,
        user_id: int,
        sharepoint_po_det_id: int,
        system_po_id: int,
        mismatch_attribute: str,
        scanned_value: str,
        system_value: str,
    ) -> bool:

        query = """
            SELECT 1
            FROM sharepoint_po_mismatch_report
            WHERE active = 1
            AND user_id = %s
            AND sharepoint_po_det_id = %s
            AND system_po_id = %s
            AND mismatch_attribute = %s
            AND scanned_value = %s
            AND system_value = %s
            LIMIT 1
        """

        await self._log_and_execute(
            query,
            (
                user_id,
                sharepoint_po_det_id,
                system_po_id,
                mismatch_attribute,
                scanned_value,
                system_value,
            ),
        )

        return await self._cur.fetchone() is not None
    
    
    # async def get_all_sharepoint_po_details(self):
    #     """Used in your PO mismatch service"""
    #     await self._log_and_execute(GET_ALL_SHAREPOINT_PO_DETAILS, [])
    #     return await self._cur.fetchall()

    # async def get_all_system_po_details(self):
    #     """Used in your PO mismatch service"""
    #     await self._log_and_execute(GET_ALL_SYSTEM_PO_DETAILS, [])
    #     return await self._cur.fetchall()
    
    # async def get_all_sharepoint_mismatches(self):
    #     await self._log_and_execute(GET_ALL_SHAREPOINT_MISMATCHES)
    #     return await self._cur.fetchall()
    
    # async def get_existing_sharepoint_po_missing(self, sharepoint_po_det_id: int):
    #     await self._log_and_execute(
    #         GET_EXISTING_SHAREPOINT_PO_MISSING_BY_SYSTEM_PO,
    #     [sharepoint_po_det_id],
    # )
    #     return await self._cur.fetchone()
    
    
    #----------------------Table Data On Sharepoint Dashboard-----------------
    async def fetch_missing_po_data(request: Request, frontendRequest):

        base_query = """
            SELECT
                pm.sharepoint_po_missing_id,
                pd.sharepoint_po_det_id,
                pm.system_po_id,

                COALESCE(pd.po_number, sp.po_number) AS po_number,
                COALESCE(pd.po_date, sp.po_date) AS po_date,
                COALESCE(pd.vendor_number, sp.vendor_number) AS vendor_code,
                COALESCE(pd.customer_name, sp.customer_name) AS customer_name,
                COALESCE(pd.created_on, sp.created_on) AS created_on,
                um.user_name AS username,

                pm.comment,
                'MISSING' AS po_status,

                CASE
                    WHEN pm.sharepoint_po_det_id IS NOT NULL THEN 'SCANNED'
                    ELSE 'SYSTEM'
                END AS source
            FROM sharepoint_po_missing_report pm
            LEFT JOIN sharepoint_po_details pd ON pm.sharepoint_po_det_id = pd.sharepoint_po_det_id
            LEFT JOIN system_po_details sp ON pm.system_po_id = sp.system_po_id
            LEFT JOIN users_master um ON pm.user_id = um.user_id
            WHERE pm.active = 1
        """

        params = []

        # Apply condition only when user_id == 1
        if frontendRequest.role_id == 1:
            base_query += " AND pm.user_id = %s"
            params.append(frontendRequest.user_id)

        base_query += " ORDER BY pm.sharepoint_po_missing_id DESC"

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(base_query, tuple(params))
                cols = [c[0] for c in cursor.description]
                rows = await cursor.fetchall()

        return [dict(zip(cols, r)) for r in rows]
            
            
    async def fetch_mismatch_po_data(request: Request, frontendRequest):

        base_query = """
            SELECT
                mm.sharepoint_po_mismatch_id,
                pd.sharepoint_po_det_id,
                mm.system_po_id,

                pd.po_number,
                pd.po_date,
                pd.vendor_number AS vendor_code,
                pd.customer_name,
                um.user_name AS username,

                mm.mismatch_attribute,
                mm.scanned_value,
                mm.system_value,
                mm.created_on,
            

                'MISMATCH' AS po_status
            FROM sharepoint_po_mismatch_report mm
            LEFT JOIN sharepoint_po_details pd 
                ON mm.sharepoint_po_det_id = pd.sharepoint_po_det_id
            LEFT JOIN system_po_details sp
                ON mm.system_po_id = sp.system_po_id
            LEFT JOIN users_master um ON mm.user_id = um.user_id
            WHERE mm.active = 1
        """

        params = []

        if frontendRequest.role_id == 1:
            base_query += " AND mm.user_id = %s"
            params.append(frontendRequest.user_id)

        base_query += " ORDER BY mm.sharepoint_po_mismatch_id DESC"

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(base_query, tuple(params))
                cols = [c[0] for c in cursor.description]
                rows = await cursor.fetchall()

        return [dict(zip(cols, r)) for r in rows]
            

    async def fetch_matched_po_data(request: Request, frontendRequest):

        base_query = """
                SELECT
                    pd.*,
                    'SHAREPOINT' AS source,
                    'NORMAL' AS record_type,
                    pd.vendor_number AS vendor_code,
                    u.user_name AS username
                FROM sharepoint_po_details pd
                LEFT JOIN sharepoint_po_missing_report pm
                    ON pm.sharepoint_po_det_id = pd.sharepoint_po_det_id
                AND pm.active = 1
                LEFT JOIN sharepoint_po_mismatch_report mm
                    ON mm.sharepoint_po_det_id = pd.sharepoint_po_det_id
                AND mm.active = 1
                LEFT JOIN users_master u
                    ON u.user_id = pd.user_id
                WHERE pd.active = 1
                AND pm.sharepoint_po_det_id IS NULL
                AND mm.sharepoint_po_det_id IS NULL
        """

        params = []

        # Apply user filter only when user_id == 1
        if frontendRequest.role_id == 1:
            base_query += " AND pd.user_id = %s"
            params.append(frontendRequest.user_id)

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(base_query, tuple(params))
                cols = [c[0] for c in cursor.description]
                rows = await cursor.fetchall()

        return [dict(zip(cols, r)) for r in rows]
    
    #For Downloading the PO Missing Report     
    async def download_sharepoint_missing_po_report(request: Request, user_id: int, role_id: int,selected_ids: List[int]):
        base_query  = """
            SELECT
                COALESCE(pd.po_number, s.po_number) AS po_number,
                COALESCE(pd.po_date, s.po_date) AS po_date,
                COALESCE(pd.vendor_number, s.vendor_number) AS vendor_code,
                COALESCE(pd.customer_name, s.customer_name) AS customer_name
            FROM
                sharepoint_po_missing_report pm
            LEFT JOIN sharepoint_po_details pd ON
                pd.sharepoint_po_det_id = pm.sharepoint_po_det_id
            LEFT JOIN system_po_details s ON
                s.system_po_id = pm.system_po_id
            WHERE
                pm.active = 1
        """
        
        params = []
        
        if role_id == 1:
            base_query += " AND pm.user_id = %s"
            params.append(user_id)
            
         #  Safe IN clause
        if selected_ids:
            placeholders = ",".join(["%s"] * len(selected_ids))
            base_query += f" AND pm.sharepoint_po_missing_id IN ({placeholders})"
            params.extend(selected_ids)
            
        base_query += " ORDER BY pm.sharepoint_po_missing_id DESC"

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(base_query, tuple(params))

                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()

                return [dict(zip(columns, row)) for row in rows]


    #For Doanloading the PO Mismatch Report   
    async def download_sharepoint_mismatch_po_report(request: Request, user_id: int, role_id: int,selected_ids: List[int]):
        base_query  = """
            SELECT
                pd.po_number,
                pd.po_date,
                pd.vendor_number AS vendor_code,
                pd.customer_name,
                pd.delivery_date,
                pd.cancel_date,
                pd.gold_karat,
                pd.ec_style_number,
                pd.customer_style_number,
                pd.color,
                pd.quantity,
                pd.description,
                mm.mismatch_attribute,
                mm.scanned_value,
                mm.system_value,
                mm.comment
            FROM sharepoint_po_mismatch_report mm
            JOIN sharepoint_po_details pd ON pd.sharepoint_po_det_id = mm.sharepoint_po_det_id
            WHERE mm.active = 1
        """
        
        params = []
        
        if role_id == 1:
            base_query += " AND mm.user_id = %s"
            params.append(user_id)
            
        if selected_ids:
            placeholders = ",".join(["%s"] * len(selected_ids))
            base_query += f" AND mm.sharepoint_po_mismatch_id IN ({placeholders})"
            params.extend(selected_ids)
            
        base_query += " ORDER BY mm.sharepoint_po_mismatch_id DESC"
        
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(base_query, tuple(params))

                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()

                return [dict(zip(columns, row)) for row in rows]
            
    
    async def download_selected_po_report(
        request: Request,
        user_id: int,
        role_id: int,
        sharepoint_missing_ids: List[int] = None,
        sharepoint_mismatch_ids: List[int] = None,
        sharepoint_matched_ids: List[int] = None
    ) -> List[Dict]:
        sharepoint_missing_ids = sharepoint_missing_ids or []
        sharepoint_mismatch_ids = sharepoint_mismatch_ids or []
        sharepoint_matched_ids = sharepoint_matched_ids or []

        queries = []
        params = []

        # SHAREPOINT MISSING
        if sharepoint_missing_ids:
            placeholders = ",".join(["%s"] * len(sharepoint_missing_ids))
            q = f"""
                SELECT
                    pd.po_number,
                    pd.po_date,
                    pd.vendor_number AS vendor_code,
                    pd.customer_name,
                    sm.created_on AS Sync_at,
                    'MISSING' AS record_type
                FROM sharepoint_po_missing_report sm
                JOIN sharepoint_po_details pd ON pd.sharepoint_po_det_id = sm.sharepoint_po_det_id
                WHERE sm.active = 1
            """
            if role_id == 1:
                q += " AND sm.user_id = %s"
                params.append(user_id)
            q += f" AND sm.sharepoint_po_missing_id IN ({placeholders})"
            params.extend(sharepoint_missing_ids)
            queries.append(q)

        # SHAREPOINT MISMATCH
        if sharepoint_mismatch_ids:
            placeholders = ",".join(["%s"] * len(sharepoint_mismatch_ids))
            q = f"""
                SELECT
                    pd.po_number,
                    pd.po_date,
                    pd.vendor_number AS vendor_code,
                    pd.customer_name,
                    mm.created_on AS Sync_at,
                    mm.mismatch_attribute,
                    mm.scanned_value,
                    mm.system_value,
                    mm.comment,
                    'MISMATCH' AS record_type
                FROM sharepoint_po_mismatch_report mm
                JOIN sharepoint_po_details pd ON pd.sharepoint_po_det_id = mm.sharepoint_po_det_id
                WHERE mm.active = 1
            """
            if role_id == 1:
                q += " AND mm.user_id = %s"
                params.append(user_id)
            q += f" AND mm.sharepoint_po_mismatch_id IN ({placeholders})"
            params.extend(sharepoint_mismatch_ids)
            queries.append(q)
            
        #Sharepoint Matched POs
        if sharepoint_matched_ids:
            queries.append(f"""
                SELECT
                    pd.po_number,
                    pd.po_date,
                    pd.vendor_number AS vendor_code,
                    pd.customer_name,
                    pd.created_on AS 'Sync_at',
                    'MATCHED' AS po_status
                FROM sharepoint_po_details pd
                WHERE pd.sharepoint_po_det_id IN ({",".join(["%s"] * len(sharepoint_matched_ids))})
            """)
            params.extend(sharepoint_matched_ids)

        if not queries:
            return []

        final_query = " UNION ALL ".join(queries) + " ORDER BY sync_at DESC"

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(final_query, tuple(params))
                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
     
     #------------------Last On Dashboard----------------------       
    async def get_last_sync_by_user_id(
        user_id: int,
        role_id: int,
        request: Request
    ) -> List[Dict[str, Any]]:
        try:
            #Role-based query selection
            if role_id in (2, 3):
                query = """
                    SELECT sf.user_id, sf.created_on AS last_sync
                    FROM sharepoint_files sf
                    ORDER BY sf.created_on DESC
                    LIMIT 1
                """
                params = ()
            else:
                query = """
                    SELECT sf.user_id, MAX(sf.created_on) AS last_sync
                    FROM sharepoint_files sf
                    WHERE sf.user_id = %s
                """
                params = (user_id,)

            async with request.app.state.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params)
                    row = await cursor.fetchone()

                    if not row or not row[1]:
                        return []

                    return [{
                        "user_id": row[0],
                        "last_sync": row[1].strftime('%Y-%m-%d %H:%M:%S')
                    }]

        except Exception as e:
            return []
        
        
    #Adding and Update comment for po missing  from UI
    async def save_sharepoint_po_missing_comment(
        sharepoint_po_missing_id: int,
        comment: str,
        request: Request
    ) -> bool:

        query = """
            UPDATE sharepoint_po_missing_report
            SET comment = %s
            WHERE sharepoint_po_missing_id = %s
            AND active = 1
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (comment, sharepoint_po_missing_id))
                await conn.commit()
                return cursor.rowcount > 0


    #Adding and Update comment for po mismatch from UI
    async def save_sharepoint_po_mismatch_comment(
        sharepoint_po_mismatch_id: int,
        comment: str,
        request: Request
    ) -> bool:

        query = """
            UPDATE sharepoint_po_mismatch_report
            SET comment = %s
            WHERE sharepoint_po_mismatch_id = %s
            AND active = 1
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (comment, sharepoint_po_mismatch_id))
                await conn.commit()
                return cursor.rowcount > 0



    #For Fetching the missing PO comment ON UI 
    async def fetch_sharepoint_missing_po_comment(
            sharepoint_po_missing_id: int,
            request: Request
        ) -> str | None:

            query = """
                SELECT comment
                FROM sharepoint_po_missing_report
                WHERE sharepoint_po_missing_id = %s
                AND active = 1
            """

            async with request.app.state.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, (sharepoint_po_missing_id,))
                    row = await cursor.fetchone()
                    return row[0] if row else None  
                


    #For Fetching the Mismatch PO comment ON UI 
    async def fetch_sharepoint_mismatch_po_comment(
            sharepoint_po_mismatch_id: int,
            request: Request
        ) -> str | None:

            query = """
                SELECT comment
                FROM sharepoint_po_mismatch_report
                WHERE sharepoint_po_mismatch_id = %s
                AND active = 1
            """

            async with request.app.state.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, (sharepoint_po_mismatch_id,))
                    row = await cursor.fetchone()
                    return row[0] if row else None


    #For Ignoring the Missing PO in Next Sync On UI
    async def ignore_sharepoint_missing_po(
        sharepoint_po_missing_id: int,
        request: Request
    ) -> bool:

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:

                # Get sharepoint_po_det_id
                await cursor.execute("""
                    SELECT sharepoint_po_det_id
                    FROM sharepoint_po_missing_report
                    WHERE sharepoint_po_missing_id = %s
                    AND active = 1
                """, (sharepoint_po_missing_id,))

                row = await cursor.fetchone()
                if not row or not row[0]:
                    return False

                sharepoint_po_det_id = row[0]

                # Update sharepoint_po_missing
                await cursor.execute("""
                    UPDATE sharepoint_po_missing_report
                    SET active = 0
                    WHERE sharepoint_po_missing_id = %s
                    AND active = 1
                """, (sharepoint_po_missing_id,))

                # Update sharepoint_po_details
                await cursor.execute("""
                    UPDATE sharepoint_po_details
                    SET active = 0
                    WHERE sharepoint_po_det_id = %s
                    AND active = 1
                """, (sharepoint_po_det_id,))

                await conn.commit()
                return True

                
    
    #For Ignoring the Mismatch PO in Next Sync On UI         
    async def ignore_sharepoint_mismatch_po(
        sharepoint_po_mismatch_id: int,
        request: Request
    ) -> bool:

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:

                await cursor.execute("""
                    SELECT sharepoint_po_det_id
                    FROM sharepoint_po_mismatch_report
                    WHERE sharepoint_po_mismatch_id = %s
                    AND active = 1
                """, (sharepoint_po_mismatch_id,))

                row = await cursor.fetchone()
                if not row or not row[0]:
                    return False

                sharepoint_po_det_id = row[0]

                await cursor.execute("""
                    UPDATE sharepoint_po_mismatch_report
                    SET active = 0
                    WHERE sharepoint_po_mismatch_id = %s
                    AND active = 1
                """, (sharepoint_po_mismatch_id,))

                await cursor.execute("""
                    UPDATE sharepoint_po_details
                    SET active = 0
                    WHERE sharepoint_po_det_id = %s
                    AND active = 1
                """, (sharepoint_po_det_id,))

                await conn.commit()
                return True

