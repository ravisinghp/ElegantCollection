from starlette.requests import Request
from typing import List, Tuple
from typing import Any,Dict
from datetime import datetime, timedelta
IST_OFFSET = timedelta(hours=5, minutes=30)
from asyncmy.cursors import DictCursor
from loguru import logger

#Total R&D Effort On User Dashboard
# async def fetch_total_user_effort_by_id(user_id: int, from_date: str, to_date: str, request: Request) -> float:
#     query = """
#         SELECT ROUND(COALESCE(SUM(rd.planned_effort_time), 0) / 60.0, 2) AS total_hours
#         FROM report_data rd, mail_details md
#         WHERE md.mail_dtl_id=rd.mail_dtl_id and rd.user_id = %s
#           AND DATE(md.date_time) BETWEEN %s AND %s
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (user_id, from_date, to_date))
#             row = await cursor.fetchone()
#             return float(row[0]) if row and row[0] is not None else 0.0
        
        

#Fetching Total Numbers of Emails on User Dashboard
async def fetch_emails_processed_by_user_id(user_id: int,  request: Request) -> int:
    query = """
       SELECT COUNT(*)
        FROM mail_details m
        WHERE m.is_active = 1
        AND m.user_id = %s;
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (user_id,))
            row = await cursor.fetchone()
            return int(row[0]) if row else 0


#Fetching Total Numbers of Attachments on User Dashboard
async def fetch_documents_analyzed_by_user_id(user_id: int, request: Request) -> int:
    query = """
       SELECT
	COUNT(em.mail_dtl_id)
FROM
	email_attachments em
WHERE
	em.user_id = %s
	AND em.is_active = 1;
    """
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (user_id, ))
            row = await cursor.fetchone()
            return int(row[0]) if row else 0
        
        
#For Downloading the PO Missing Report     
async def download_missing_po_report(
    request: Request,
    user_id: int,
    role_id: int,
    #selected_ids: List[int]
):
    base_query = """
        SELECT
            COALESCE(pd.po_number, s.po_number) AS po_number,
            COALESCE(pd.po_date, s.po_date) AS po_date,
            COALESCE(pd.vendor_number, s.vendor_number) AS vendor_code,
            COALESCE(pd.customer_name, s.customer_name) AS customer_name,
            pm.po_missing_id
        FROM
            po_missing_report pm
        LEFT JOIN po_details pd
            ON pd.po_det_id = pm.po_det_id
        LEFT JOIN system_po_details s
            ON s.system_po_id = pm.system_po_id
        WHERE
            pm.active = 1
    """

    params = []

    if role_id == 1:
        base_query += " AND pm.user_id = %s"
        params.append(user_id)

    #  Safe IN clause
    # if selected_ids:
    #     placeholders = ",".join(["%s"] * len(selected_ids))
    #     base_query += f" AND pm.po_missing_id IN ({placeholders})"
    #     params.extend(selected_ids)

    base_query += " ORDER BY pm.po_missing_id DESC"

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(base_query, tuple(params))

            columns = [col[0] for col in cursor.description]
            rows = await cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]


   #For Doanloading the PO Mismatch Report   
async def download_mismatch_po_report(request: Request, user_id: int, role_id: int):
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
            mm.comment,
            mm.po_mismatch_id
        FROM po_mismatch_report mm
        JOIN po_details pd ON pd.po_det_id = mm.po_det_id
        WHERE mm.active = 1
    """
    
    params = []
    
    if role_id == 1:
        base_query += " AND mm.user_id = %s"
        params.append(user_id)

    #  ADD THIS
    # if selected_ids:
    #     placeholders = ",".join(["%s"] * len(selected_ids))
    #     base_query += f" AND mm.po_mismatch_id IN ({placeholders})"
    #     params.extend(selected_ids)
        
    base_query += " ORDER BY mm.po_mismatch_id DESC"
    
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(base_query, tuple(params))

            columns = [col[0] for col in cursor.description]
            rows = await cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]
             
#For Business admin Dashboard download all missing pos 
async def download_all_missing_po_report(request: Request):
    try:
        query = """
            SELECT
                'EMAIL' AS source,
                pd.po_number,
                pd.po_date,
                pd.vendor_number AS vendor_code,
                pd.customer_name
            FROM po_missing_report pm
            JOIN po_details pd ON pd.po_det_id = pm.po_det_id
            WHERE pm.active = 1

            UNION ALL

            SELECT
                'SHAREPOINT' AS source,
                sp.po_number,
                sp.po_date,
                sp.vendor_number AS vendor_code,
                sp.customer_name
            FROM sharepoint_po_missing_report spm
            JOIN sharepoint_po_details sp
                ON sp.sharepoint_po_det_id = spm.sharepoint_po_det_id
            WHERE spm.active = 1

            ORDER BY po_date DESC
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        raise e
    
    
#For Business admin Dashboard download all mismatch pos     
async def download_all_mismatch_po_report(request: Request):
    try:
        query = """
            SELECT
                'EMAIL' AS source,
                pd.po_number,
                pd.vendor_number,
                mm.mismatch_attribute,
                mm.scanned_value,
                mm.system_value,
                mm.comment
            FROM po_mismatch_report mm
            JOIN po_details pd ON pd.po_det_id = mm.po_det_id
            WHERE mm.active = 1

            UNION ALL

            SELECT
                'SHAREPOINT' AS source,
                sp.po_number,
                sp.vendor_number,
                sm.mismatch_attribute,
                sm.scanned_value,
                sm.system_value,
                sm.comment
            FROM sharepoint_po_mismatch_report sm
            JOIN sharepoint_po_details sp
                ON sp.sharepoint_po_det_id = sm.sharepoint_po_det_id
            WHERE sm.active = 1
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        raise e


async def download_all_selected_po_report(
        request: Request,
        user_id: int,
        role_id: int,
        missing_po_ids: List[int],
        mismatch_po_ids: List[int],
        matched_po_ids: List[int],
    ) -> List[Dict[str, Any]]:

        queries = []
        params = []

        # -------- EMAIL MISSING --------
        if missing_po_ids:
            queries.append(f"""
                SELECT
                    pd.po_number,
                    pd.po_date,
                    pd.vendor_number AS vendor_code,
                    pd.customer_name,
                    pm.created_on AS 'Sync_at',
                    'MISSING' AS po_status
                FROM po_missing_report pm
                JOIN po_details pd ON pm.po_det_id = pd.po_det_id
                LEFT JOIN users_master um ON pm.user_id = um.user_id
                WHERE pm.po_missing_id IN ({",".join(["%s"] * len(missing_po_ids))})
            """)
            params.extend(missing_po_ids)

        # -------- EMAIL MISMATCH --------
        if mismatch_po_ids:
            queries.append(f"""
                SELECT
                    pd.po_number,
                    pd.po_date,
                    pd.vendor_number AS vendor_code,
                    pd.customer_name,
                    mm.created_on AS 'Sync_at',
                    'MISMATCH' AS po_status
                FROM po_mismatch_report mm
                JOIN po_details pd ON mm.po_det_id = pd.po_det_id
                LEFT JOIN users_master um ON mm.user_id = um.user_id
                WHERE mm.po_mismatch_id IN ({",".join(["%s"] * len(mismatch_po_ids))})
            """)
            params.extend(mismatch_po_ids)
		
		# -------- EMAIL MATCHED --------
        if matched_po_ids:
            queries.append(f"""
                SELECT
                    pd.po_number,
                    pd.po_date,
                    pd.vendor_number AS vendor_code,
                    pd.customer_name,
                    pd.created_on AS 'Sync_at',
                    'MATCHED' AS po_status
                FROM po_details pd
                WHERE pd.po_det_id IN ({",".join(["%s"] * len(matched_po_ids))})
            """)
            params.extend(matched_po_ids)

        if not queries:
            return []

        final_query = " UNION ALL ".join(queries) + " ORDER BY sync_at DESC"

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(final_query, tuple(params))
                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]

 
#On Business admin dashboard
async def download_combined_all_po_report(
    request: Request,
    user_id: int,
    role_id: int,
    email_missing_ids: list[int],
    email_mismatch_ids: list[int],
    email_matched_ids: list[int],
    sharepoint_missing_ids: list[int],
    sharepoint_mismatch_ids: list[int],
    sharepoint_matched_ids: list[int],
):
    try:
        queries = []
        params = []

        # ---------------- EMAIL MISSING ----------------
        if email_missing_ids:
            placeholders = ",".join(["%s"] * len(email_missing_ids))
            queries.append(f"""
                SELECT
                    'EMAIL' AS source,
                    'MISSING' AS record_type,
                    pd.po_number,
                    pd.po_date,
                    pd.vendor_number AS vendor_code,
                    pd.customer_name
                FROM po_missing_report pm
                JOIN po_details pd ON pd.po_det_id = pm.po_det_id
                WHERE pm.active = 1
                  AND pm.po_missing_id IN ({placeholders})
            """)
            params.extend(email_missing_ids)

        # ---------------- EMAIL MISMATCH ----------------
        if email_mismatch_ids:
            placeholders = ",".join(["%s"] * len(email_mismatch_ids))
            queries.append(f"""
                SELECT
                    'EMAIL' AS source,
                    'MISMATCH' AS record_type,
                    pd.po_number,
                    pd.po_date,
                    pd.vendor_number AS vendor_code,
                    pd.customer_name
                FROM po_mismatch_report mm
                JOIN po_details pd ON pd.po_det_id = mm.po_det_id
                WHERE mm.active = 1
                  AND mm.po_mismatch_id IN ({placeholders})
            """)
            params.extend(email_mismatch_ids)

        # ---------------- EMAIL MATCHED ----------------
        if email_matched_ids:
            placeholders = ",".join(["%s"] * len(email_matched_ids))
            queries.append(f"""
                SELECT
                    'EMAIL' AS source,
                    'MATCH' AS record_type,
                    pd.po_number,
                    pd.po_date,
                    pd.vendor_number AS vendor_code,
                    pd.customer_name
                FROM po_details pd
                WHERE pd.po_det_id IN ({placeholders})
            """)
            params.extend(email_matched_ids)

        # ---------------- SHAREPOINT MISSING ----------------
        if sharepoint_missing_ids:
            placeholders = ",".join(["%s"] * len(sharepoint_missing_ids))
            queries.append(f"""
                SELECT
                    'SHAREPOINT' AS source,
                    'MISSING' AS record_type,
                    sp.po_number,
                    sp.po_date,
                    sp.vendor_number AS vendor_code,
                    sp.customer_name
                FROM sharepoint_po_missing_report spm
                JOIN sharepoint_po_details sp
                  ON sp.sharepoint_po_det_id = spm.sharepoint_po_det_id
                WHERE spm.active = 1
                  AND spm.sharepoint_po_missing_id IN ({placeholders})
            """)
            params.extend(sharepoint_missing_ids)

        # ---------------- SHAREPOINT MISMATCH ----------------
        if sharepoint_mismatch_ids:
            placeholders = ",".join(["%s"] * len(sharepoint_mismatch_ids))
            queries.append(f"""
                SELECT
                    'SHAREPOINT' AS source,
                    'MISMATCH' AS record_type,
                    sp.po_number,
                    sp.po_date,
                    sp.vendor_number AS vendor_code,
                    sp.customer_name
                FROM sharepoint_po_mismatch_report spm
                JOIN sharepoint_po_details sp
                  ON sp.sharepoint_po_det_id = spm.sharepoint_po_det_id
                WHERE spm.active = 1
                  AND spm.sharepoint_po_mismatch_id IN ({placeholders})
            """)
            params.extend(sharepoint_mismatch_ids)

        # ---------------- SHAREPOINT MATCHED ----------------
        if sharepoint_matched_ids:
            placeholders = ",".join(["%s"] * len(sharepoint_matched_ids))
            queries.append(f"""
                SELECT
                    'SHAREPOINT' AS source,
                    'MATCH' AS record_type,
                    pd.po_number,
                    pd.po_date,
                    pd.vendor_number AS vendor_code,
                    pd.customer_name
                FROM sharepoint_po_details pd
                WHERE pd.sharepoint_po_det_id IN ({placeholders})
            """)
            params.extend(sharepoint_matched_ids)

        if not queries:
            return []

        final_query = " UNION ALL ".join(queries) + " ORDER BY po_date DESC"

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(final_query, tuple(params))
                columns = [col[0] for col in cursor.description]
                rows = await cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        raise e
        

#Adding and Update comment for po missing  from UI
async def save_po_missing_comment(
    po_missing_id: int,
    comment: str,
    request: Request
) -> bool:

    query = """
        UPDATE po_missing_report
        SET comment = %s
        WHERE po_missing_id = %s
          AND active = 1
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (comment, po_missing_id))
            await conn.commit()
            return cursor.rowcount > 0


#Adding and Update comment for po mismatch from UI
async def save_po_mismatch_comment(
    po_mismatch_id: int,
    comment: str,
    request: Request
) -> bool:

    query = """
        UPDATE po_mismatch_report
        SET comment = %s
        WHERE po_mismatch_id = %s
          AND active = 1
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (comment, po_mismatch_id))
            await conn.commit()
            return cursor.rowcount > 0



#For Fetching the missing PO comment ON UI 
async def fetch_missing_po_comment(
        po_missing_id: int,
        request: Request
    ) -> str | None:

        query = """
            SELECT comment
            FROM po_missing_report
            WHERE po_missing_id = %s
              AND active = 1
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (po_missing_id,))
                row = await cursor.fetchone()
                return row[0] if row else None  
            


#For Fetching the Mismatch PO comment ON UI 
async def fetch_mismatch_po_comment(
        po_mismatch_id: int,
        request: Request
    ) -> str | None:

        query = """
            SELECT comment
            FROM po_mismatch_report
            WHERE po_mismatch_id = %s
              AND active = 1
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (po_mismatch_id,))
                row = await cursor.fetchone()
                return row[0] if row else None


#For Ignoring the Missing PO in Next Sync On UI
async def ignore_missing_po(
        po_missing_id: int,
        request: Request
    ) -> bool:

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:

                # Get po_det_id
                await cursor.execute("""
                    SELECT po_det_id
                    FROM po_missing_report
                    WHERE po_missing_id = %s
                    AND active = 1
                """, (po_missing_id,))

                row = await cursor.fetchone()
                if not row or not row[0]:
                    return False

                po_det_id = row[0]

                # Update po_missing
                await cursor.execute("""
                    UPDATE po_missing_report
                    SET active = 0
                    WHERE po_missing_id = %s
                    AND active = 1
                """, (po_missing_id,))

                # Update po_details
                await cursor.execute("""
                    UPDATE po_details
                    SET active = 0
                    WHERE po_det_id = %s
                    AND active = 1
                """, (po_det_id,))

                await conn.commit()
                return True
            
   
#For Ignoring the Mismatch PO in Next Sync On UI         
async def ignore_mismatch_po(
        po_mismatch_id: int,
        request: Request
    ) -> bool:

         async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:

                await cursor.execute("""
                    SELECT po_det_id
                    FROM po_mismatch_report
                    WHERE po_mismatch_id = %s
                    AND active = 1
                """, (po_mismatch_id,))

                row = await cursor.fetchone()
                if not row or not row[0]:
                    return False

                po_det_id = row[0]

                await cursor.execute("""
                    UPDATE po_mismatch_report
                    SET active = 0
                    WHERE po_mismatch_id = %s
                    AND active = 1
                """, (po_mismatch_id,))

                await cursor.execute("""
                    UPDATE po_details
                    SET active = 0
                    WHERE po_det_id = %s
                    AND active = 1
                """, (po_det_id,))

                await conn.commit()
                return True
     
            
#Business admin fetching users list and vendor number list on dashboard
async def get_all_users_by_role_id_business_admin(
    request
):
    #Business admin can see all users
    query = """
        SELECT user_id, user_name
        FROM users_master
        WHERE is_active = 1
        AND role_id = 1
        ORDER BY user_name ASC
    """

    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                rows = await cursor.fetchall()

                return [
                    {
                        "user_id": row[0],
                        "user_name": row[1]
                    }
                    for row in rows
                ]
    except Exception as e:
        raise Exception(f"DB error while fetching users: {str(e)}")


async def get_vendors_business_admin(request):
        query = """
            SELECT DISTINCT vendor_number
            FROM (
                SELECT vendor_number FROM po_details WHERE vendor_number IS NOT NULL
                UNION
                SELECT vendor_number FROM sharepoint_po_details WHERE vendor_number IS NOT NULL
            ) vendor_list
            ORDER BY vendor_number;
        """

        try:
            async with request.app.state.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query)
                    rows = await cursor.fetchall()

                    return [
                        {
                            "vendor_number": row[0]
                        }
                        for row in rows
                    ]

        except Exception as e:
            raise Exception(f"DB error while fetching vendors: {str(e)}")
# async def create_po_missing_comment(
#     po_missing_id: int,
#     comment: str,
#     request: Request
# ) -> bool:

#     query = """
#         UPDATE po_missing_report
#         SET comment = %s
#         WHERE po_missing_id = %s
#           AND active = 1
#           AND (comment IS NULL OR comment = '')
#     """

#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (comment, po_missing_id))
#             await conn.commit()
#             return cursor.rowcount > 0
        
        
# async def create_po_mismatch_comment(
#     po_mismatch_id: int,
#     comment: str,
#     request: Request
# ) -> bool:

#     query = """
#         UPDATE po_mismatch_report
#         SET comment = %s
#         WHERE po_mismatch_id = %s
#           AND active = 1
#           AND (comment IS NULL OR comment = '')
#     """

#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (comment, po_mismatch_id))
#             await conn.commit()
#             return cursor.rowcount > 0

        
   
#     #Update the Comment For PO Missing 
# async def update_po_missing_comment(
#     po_missing_id: int,
#     comment: str,
#     request: Request
# ) -> bool:

#     query = """
#         UPDATE po_missing_report
#         SET comment = %s
#         WHERE po_missing_id = %s
#           AND active = 1
#     """

#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (comment, po_missing_id))
#             await conn.commit()
#             return cursor.rowcount > 0 
        


# #Update the Comment For PO Mismatch
# async def update_po_mismatch_comment(
#     po_mismatch_id: int,
#     comment: str,
#     request: Request
# ) -> bool:

#     query = """
#         UPDATE po_mismatch_report
#         SET comment = %s
#         WHERE po_mismatch_id = %s
#           AND active = 1
#     """

#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (comment, po_mismatch_id))
#             await conn.commit()
#             return cursor.rowcount > 0    

        
async def fetch_missing_po_data(request: Request, frontendRequest):

    base_query = """
        SELECT
            pm.po_missing_id,
            pm.po_det_id,
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
                WHEN pm.po_det_id IS NOT NULL THEN 'SCANNED'
                ELSE 'SYSTEM'
            END AS source
        FROM po_missing_report pm
        LEFT JOIN po_details pd ON pm.po_det_id = pd.po_det_id
        LEFT JOIN system_po_details sp ON pm.system_po_id = sp.system_po_id
        LEFT JOIN users_master um ON pm.user_id = um.user_id
        WHERE pm.active = 1
    """

    params = []

    # Apply condition only when user_id == 1
    if frontendRequest.role_id == 1:
        base_query += " AND pm.user_id = %s"
        params.append(frontendRequest.user_id)

    base_query += " ORDER BY pm.po_missing_id DESC"

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(base_query, tuple(params))
            cols = [c[0] for c in cursor.description]
            rows = await cursor.fetchall()

    return [dict(zip(cols, r)) for r in rows]
        
        
async def fetch_mismatch_po_data(request: Request, frontendRequest):

    base_query = """
        SELECT
            mm.po_mismatch_id,
            mm.po_det_id,
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
        FROM po_mismatch_report mm
        LEFT JOIN po_details pd 
            ON mm.po_det_id = pd.po_det_id
        LEFT JOIN system_po_details sp
            ON mm.system_po_id = sp.system_po_id
        LEFT JOIN users_master um ON mm.user_id = um.user_id
        WHERE mm.active = 1
    """

    params = []

    if frontendRequest.role_id == 1:
        base_query += " AND mm.user_id = %s"
        params.append(frontendRequest.user_id)

    base_query += " ORDER BY mm.po_mismatch_id DESC"

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
                pd.vendor_number AS vendor_code,
                u.user_name AS username
            FROM po_details pd
            LEFT JOIN po_missing_report pm
                ON pm.po_det_id = pd.po_det_id
            AND pm.active = 1
            LEFT JOIN po_mismatch_report mm
                ON mm.po_det_id = pd.po_det_id
            AND mm.active = 1
            LEFT JOIN mail_details md
                ON md.mail_dtl_id = pd.mail_dtl_id
            LEFT JOIN users_master u
                ON u.user_id = md.user_id
            WHERE pd.active = 1           
            AND pm.po_det_id IS NULL
            AND mm.po_det_id IS NULL
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
        
        #for schedular we are getting all users 
async def get_active_users(request: Request):
    query = """
        SELECT user_id
        FROM user_master
        WHERE role_id = 1
          AND is_active = 1
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
        
#----------------Search PO for Business Admin Dashboard-----------------#
def build_conditions(date_col, vendor_col, user_col, po_col, params, filters):
    cond = []

    if filters.fromDate:
        cond.append(f"{date_col} >= %s")
        params.append(filters.fromDate)

    if filters.toDate:
        cond.append(f"{date_col} <= %s")
        params.append(filters.toDate)

    if filters.userId:
        cond.append(f"{user_col} = %s")
        params.append(int(filters.userId))

    if filters.vendorNumber:
        cond.append(f"{vendor_col} = %s")
        params.append(filters.vendorNumber)

    if filters.poNumber:
        cond.append(f"{po_col} = %s")
        params.append(filters.poNumber)

    return " AND " + " AND ".join(cond) if cond else ""


async def search_pos_business_admin(request: Request, filters):
    params = []

    query = f"""
    SELECT * FROM (

        /* ================= EMAIL : MISSING ================= */
        SELECT
            pm.po_missing_id,
            NULL AS po_mismatch_id,
            NULL AS sharepoint_po_missing_id,
            NULL AS sharepoint_po_mismatch_id,

            pm.po_det_id,
            NULL AS sharepoint_po_det_id,
            pm.system_po_id,

            COALESCE(pd.po_number, sp.po_number) AS po_number,
            COALESCE(pd.po_date, sp.po_date) AS po_date,
            COALESCE(pd.vendor_number, sp.vendor_number) AS vendor_code,
            COALESCE(pd.customer_name, sp.customer_name) AS customer_name,
            COALESCE(pd.created_on, sp.created_on) AS created_on,
            um.user_name AS username,

            pm.comment,
            NULL AS mismatch_attribute,
            NULL AS scanned_value,
            NULL AS system_value,

            'MISSING' AS po_status,
            'EMAIL' AS source

        FROM po_missing_report pm
        LEFT JOIN po_details pd ON pm.po_det_id = pd.po_det_id
        LEFT JOIN system_po_details sp ON pm.system_po_id = sp.system_po_id
        LEFT JOIN users_master um ON pm.user_id = um.user_id
        WHERE pm.active = 1
        {build_conditions(
            "COALESCE(pd.po_date, sp.po_date)",
            "COALESCE(pd.vendor_number, sp.vendor_number)",
            "pm.user_id",
            "COALESCE(pd.po_number, sp.po_number)",
            params,
            filters
        )}

        UNION ALL

        /* ================= EMAIL : MISMATCH ================= */
        SELECT
            NULL,
            mm.po_mismatch_id,
            NULL,
            NULL,

            mm.po_det_id,
            NULL,
            mm.system_po_id,

            pd.po_number,
            pd.po_date,
            pd.vendor_number,
            pd.customer_name,
            mm.created_on,
            um.user_name,

            NULL,
            mm.mismatch_attribute,
            mm.scanned_value,
            mm.system_value,

            'MISMATCH',
            'EMAIL'

        FROM po_mismatch_report mm
        LEFT JOIN po_details pd ON mm.po_det_id = pd.po_det_id
        LEFT JOIN users_master um ON mm.user_id = um.user_id
        WHERE mm.active = 1
        {build_conditions(
            "pd.po_date",
            "pd.vendor_number",
            "mm.user_id",
            "pd.po_number",
            params,
            filters
        )}

        UNION ALL

        /* ================= EMAIL : NORMAL ================= */
        SELECT
            NULL,
            NULL,
            NULL,
            NULL,

            pd.po_det_id,
            NULL,
            NULL,

            pd.po_number,
            pd.po_date,
            pd.vendor_number,
            pd.customer_name,
            pd.created_on,
            u.user_name,

            NULL, NULL, NULL, NULL,

            'NORMAL',
            'EMAIL'

        FROM po_details pd
        LEFT JOIN po_missing_report pm
            ON pm.po_det_id = pd.po_det_id AND pm.active = 1
        LEFT JOIN po_mismatch_report mm
            ON mm.po_det_id = pd.po_det_id AND mm.active = 1
        LEFT JOIN users_master u ON u.user_id = pd.user_id
        WHERE pd.active = 1
          AND pm.po_det_id IS NULL
          AND mm.po_det_id IS NULL
        {build_conditions(
            "pd.po_date",
            "pd.vendor_number",
            "pd.user_id",
            "pd.po_number",
            params,
            filters
        )}

        UNION ALL

        /* ================= SHAREPOINT : MISSING ================= */
        SELECT
            NULL,
            NULL,
            pm.sharepoint_po_missing_id,
            NULL,

            NULL,
            pm.sharepoint_po_det_id,
            pm.system_po_id,

            COALESCE(pd.po_number, sp.po_number),
            COALESCE(pd.po_date, sp.po_date),
            COALESCE(pd.vendor_number, sp.vendor_number),
            COALESCE(pd.customer_name, sp.customer_name),
            COALESCE(pd.created_on, sp.created_on),
            um.user_name,

            pm.comment,
            NULL, NULL, NULL,

            'MISSING',
            'SHAREPOINT'

        FROM sharepoint_po_missing_report pm
        LEFT JOIN sharepoint_po_details pd
            ON pm.sharepoint_po_det_id = pd.sharepoint_po_det_id
        LEFT JOIN system_po_details sp
            ON pm.system_po_id = sp.system_po_id
        LEFT JOIN users_master um
            ON pm.user_id = um.user_id
        WHERE pm.active = 1
        {build_conditions(
            "COALESCE(pd.po_date, sp.po_date)",
            "COALESCE(pd.vendor_number, sp.vendor_number)",
            "pm.user_id",
            "COALESCE(pd.po_number, sp.po_number)",
            params,
            filters
        )}

        UNION ALL

        /* ================= SHAREPOINT : MISMATCH ================= */
        SELECT
            NULL,
            NULL,
            NULL,
            mm.sharepoint_po_mismatch_id,

            NULL,
            mm.sharepoint_po_det_id,
            mm.system_po_id,

            pd.po_number,
            pd.po_date,
            pd.vendor_number,
            pd.customer_name,
            mm.created_on,
            um.user_name,

            NULL,
            mm.mismatch_attribute,
            mm.scanned_value,
            mm.system_value,

            'MISMATCH',
            'SHAREPOINT'

        FROM sharepoint_po_mismatch_report mm
        LEFT JOIN sharepoint_po_details pd
            ON mm.sharepoint_po_det_id = pd.sharepoint_po_det_id
        LEFT JOIN users_master um
            ON mm.user_id = um.user_id
        WHERE mm.active = 1
        {build_conditions(
            "pd.po_date",
            "pd.vendor_number",
            "mm.user_id",
            "pd.po_number",
            params,
            filters
        )}

        UNION ALL

        /* ================= SHAREPOINT : NORMAL ================= */
        SELECT
            NULL,
            NULL,
            NULL,
            NULL,

            NULL,
            pd.sharepoint_po_det_id,
            NULL,

            pd.po_number,
            pd.po_date,
            pd.vendor_number,
            pd.customer_name,
            pd.created_on,
            u.user_name,

            NULL, NULL, NULL, NULL,

            'NORMAL',
            'SHAREPOINT'

        FROM sharepoint_po_details pd
        LEFT JOIN sharepoint_po_missing_report pm
            ON pm.sharepoint_po_det_id = pd.sharepoint_po_det_id AND pm.active = 1
        LEFT JOIN sharepoint_po_mismatch_report mm
            ON mm.sharepoint_po_det_id = pd.sharepoint_po_det_id AND mm.active = 1
        LEFT JOIN users_master u
            ON u.user_id = pd.user_id
        WHERE pd.active = 1
          AND pm.sharepoint_po_det_id IS NULL
          AND mm.sharepoint_po_det_id IS NULL
        {build_conditions(
            "pd.po_date",
            "pd.vendor_number",
            "pd.user_id",
            "pd.po_number",
            params,
            filters
        )}

    ) t
    ORDER BY t.po_date DESC
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, tuple(params))
            cols = [c[0] for c in cursor.description]
            rows = await cursor.fetchall()

    return [dict(zip(cols, row)) for row in rows]



#Fetching Total Numbers of Meeting on User Dashboard
# async def fetch_meetings_processed_by_user_id(user_id: int, from_date: str, to_date: str, request: Request) -> int:
#     query = """
#         SELECT COUNT(*) 
#         FROM meeting_report_data mrd,cal_master cm
#         WHERE mrd.cal_id=cm.cal_id and mrd.user_id = %s 
#           AND mrd.is_active = TRUE
#           AND DATE(cm.event_start_datetime) BETWEEN %s AND %s
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (user_id, from_date, to_date))
#             row = await cursor.fetchone()
#             return int(row[0]) if row else 0




# ### This code is used to fetch calculateing one month to current date data week wise
# async def get_weekly_hours_previous_month(request, from_date:str,to_date:str,org_id: int, user_id: int,) -> List[Dict[str, Any]]:
#     try:
#         query = """
#         WITH date_range AS (
#             SELECT
#                 CAST(%s AS DATE) AS start_date,
#                 CAST(DATE_ADD(%s, INTERVAL 1 DAY) AS DATE) AS end_date
#                                         )
#                                         SELECT
#                 DATE_FORMAT(MIN(md.date_time), '%%b %%Y') AS month_name,
#                 CONCAT('Week ', FLOOR(DATEDIFF(md.date_time, p.start_date) / 7) + 1) AS week_index,
#                 ROUND(SUM(r.planned_effort_time) / 60, 2) AS total_hours
#             FROM
#                 report_data r
#             LEFT JOIN 
#                             mail_details md ON
#                 md.mail_dtl_id = r.mail_dtl_id
#             JOIN 
#                 date_range p
#                                             ON
#                 md.date_time >= p.start_date
#                 AND md.date_time < p.end_date
#             WHERE
#                 r.org_id = %s
#                 AND r.user_id = %s
#             GROUP BY
#                 week_index
#             ORDER BY
#                 MIN(md.date_time);
#         """

#         async with request.app.state.pool.acquire() as conn:
#             async with conn.cursor() as cursor:
#                 #pass both org_id and user_id as parameters
#                 await cursor.execute(query, (from_date,to_date,org_id,user_id,))
#                 rows = await cursor.fetchall()

#                 result = [
#                     {
#                         "month_name": row[0],
#                         "week_of_month": row[1],
#                         "total_hours": float(row[2]) if row[2] is not None else 0.0,
#                     }
#                     for row in rows
#                 ]

#                 return result
#     except Exception as e:
#         return []


# #Fetching Top Keywords On User Dashboard 
# async def fetch_keywords_by_userId(request, org_id: int, user_id: int,from_date:str,to_date:str) -> List[Tuple[str]]:
#     try:
#         query = """
#            SELECT
#             rd.keywords_found
#         FROM
#             report_data rd
#         JOIN users_master u ON
#             rd.user_id = u.user_id
#         Join mail_details m on m.mail_dtl_id =rd.mail_dtl_id
#         WHERE
#             u.user_id = %s
#             AND u.is_active = 1
#             AND m.date_time between %s and %s;
#         """
#         async with request.app.state.pool.acquire() as conn:
#             async with conn.cursor() as cursor:
#                 await cursor.execute(query, (user_id,from_date,to_date))
#                 return await cursor.fetchall()
#     except Exception as e:
#         return []
    
#  #Last Sync On User Dashboard
async def get_last_sync_by_user_id(
    user_id: int,
    role_id: int,
    request: Request
) -> List[Dict[str, Any]]:
    try:
        # 🔹 Role-based query selection
        if role_id in (2, 3):
            query = """
                SELECT m.user_id, m.created_on AS last_sync
                FROM mail_details m
                ORDER BY m.created_on DESC
                LIMIT 1
            """
            params = ()
        else:
            query = """
                SELECT m.user_id, MAX(m.created_on) AS last_sync
                FROM mail_details m
                WHERE m.user_id = %s
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


#Last sync for business admin and system admin dashboard
async def get_last_sync(request: Request) -> List[Dict[str, Any]]:
        try:
            # 🔹 Latest created_on from both tables for Business/System Admin
            query = """
                SELECT GREATEST(
                    COALESCE((SELECT MAX(created_on) FROM mail_details), 'No Sync yet'),
                    COALESCE((SELECT MAX(created_on) FROM sharepoint_files), 'No Sync yet')
                ) AS last_sync
            """
            async with request.app.state.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query)
                    row = await cursor.fetchone()
 
                    if not row or not row[0]:
                        return []
 
                    return [{
                        "last_sync": row[0]  # row[0] is already 'YYYY-MM-DD HH:MM:SS'
                    }]
        except Exception as e:
            raise Exception(f"Error fetching last sync data: {str(e)}")
 
 
#For duplicates folder checking
async def check_folder_mapping_exists_repo(
    request: Request,
    user_id: int,
    folder_name: str
) -> bool:
    query = """
        SELECT 1
        FROM sd_folder_mapping_table
        WHERE user_id = %s
          AND folder_name = %s
          AND is_active = 1
        LIMIT 1
    """

    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (user_id, folder_name))
                row = await cursor.fetchone()
                return row is not None

    except Exception as e:
        raise Exception(f"DB error while checking folder mapping: {str(e)}")

#Insert Folder in DB 
async def insert_folder_mapping_repo(
    request: Request,
    user_id: int,
    folder_name: str
) -> bool:
    query = """
        INSERT INTO sd_folder_mapping_table (user_id, folder_name)
        VALUES (%s, %s)
    """

    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (user_id, folder_name))
                await conn.commit()
                return cursor.rowcount > 0

    except Exception as e:
        raise Exception(f"DB error while inserting folder mapping: {str(e)}")
   
    
async def check_duplicate_schedule(request, day: str, schedule_time):
 
    query = """
        SELECT 1
        FROM sd_task_master_table
        WHERE day = %s
        AND time = %s
        AND is_active = 1
        LIMIT 1
    """
 
    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (day, schedule_time))
            result = await cursor.fetchone()
            return result is not None
#Save the Scheduler details in sd task master table in db 
async def save_schedule(
    request,
    days: str,
    schedule_time,
    created_by: int
) -> bool:

    if not isinstance(schedule_time, datetime):
        raise ValueError("schedule_time must be datetime")

    query = """
        INSERT INTO sd_task_master_table
        (day, time, created_by)
        VALUES (%s, %s, %s)
    """

    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    query,
                    (
                        days,
                        schedule_time,
                        created_by
                    )
                )
                await conn.commit()
                return cursor.rowcount > 0

    except Exception as e:
        raise Exception(f"DB error while inserting scheduler: {str(e)}")

#---------------------Get Active Schedule From task_sd_master_table-------------
async def get_active_schedule(request):
    query = """
        SELECT
            task_sd_id,
            day,
            time
        FROM sd_task_master_table
        WHERE is_active = 1
        ORDER BY created_on DESC
        LIMIT 1
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cursor:
            await cursor.execute(query)
            return await cursor.fetchone()
 
 #--------------------Get All Active Users with refresh Token------------           
async def get_users_with_refresh_token(request):
    query = """
        SELECT
            user_id,
            refresh_token
        FROM outlook_tokens
        WHERE refresh_token IS NOT NULL
          AND is_active = 1
    """

    async with request.app.state.pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cursor:
            await cursor.execute(query)
            return await cursor.fetchall()
 
 #---------------Get folders which we have to sync----------------           
async def get_user_folders(request, user_id: int):
        query = """
            SELECT
                folder_name
            FROM sd_folder_mapping_table
            WHERE user_id = %s
              AND is_active = 1
        """

        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (user_id,))
                rows = await cursor.fetchall()

        return [row[0] for row in rows]
# #Update Term Condition Fleg When User login once
# async def update_term_condition_flag(user_id: int, role_id: int, org_id: int, request: Request, flag: int = 1):
#     query = """
#         UPDATE users_master
#         SET term_condition_flag = %s
#         WHERE user_id = %s
#           AND role_id = %s
#           AND org_id = %s
#     """
#     async with request.app.state.pool.acquire() as conn:
#         async with conn.cursor() as cursor:
#             await cursor.execute(query, (flag, user_id, role_id, org_id))
#             await conn.commit() 
#             return cursor.rowcount > 0   #  True if row updated



#--------------Soft Delete and Hard Delete User and all related tables--------------
# table_name : status_column
RELATED_TABLES = {
    "audit_po_details": "active",
    "mail_details": "is_active",
    "email_attachments": "is_active",
    "sharepoint_files": "is_active",
    "po_details": "active",
    "sharepoint_po_details": "active",
    "po_missing_report": "active",
    "sharepoint_po_missing_report": "active",
    "po_mismatch_report": "active",
    "sharepoint_po_mismatch_report": "active",
    "outlook_tokens": "is_active",
    "category_master": "is_active",
    "keyword_master": "is_active",
    "user_source_mapping": "is_active",
    "sd_folder_mapping_table": "is_active",
}

async def soft_delete_user(request, user_id: int) -> bool:
    """Mark user and all related records as inactive"""
    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await conn.begin()

                # Soft delete user
                await cursor.execute(
                    "UPDATE users_master SET is_active = 0 WHERE user_id = %s",
                    (user_id,)
                )

                # Soft delete related tables
                for table, status_col in RELATED_TABLES.items():
                    await cursor.execute(
                        f"""
                        UPDATE {table}
                        SET {status_col} = 0
                        WHERE user_id = %s
                        """,
                        (user_id,)
                    )

                await conn.commit()

        logger.info(f"User {user_id} soft-deleted successfully")
        return True

    except Exception as e:
        logger.error(f"Soft delete failed for user {user_id}: {e}")
        return False


AUDIT_TABLES = {
    "audit_po_details": "active",
}

HARD_DELETE_TABLES = [
    "sd_folder_mapping_table",
    "user_source_mapping",
    "category_master",
    "keyword_master",
    "outlook_tokens",
    "sharepoint_files",
    "sharepoint_po_details",
    "sharepoint_po_mismatch_report",
    "sharepoint_po_missing_report",
    "mail_details",
    "email_attachments",
    "po_details",
    "po_missing_report",
    "po_mismatch_report",
    "audit_po_details"
]

async def hard_delete_user(request, user_id: int) -> bool:
    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await conn.begin()

                # Soft delete audit tables
                for table, col in AUDIT_TABLES.items():
                    await cursor.execute(
                        f"UPDATE {table} SET {col} = 0 WHERE user_id = %s",
                        (user_id,)
                    )

                # Delete child tables first
                for table in reversed(HARD_DELETE_TABLES):
                    await cursor.execute(
                        f"DELETE FROM {table} WHERE user_id = %s",
                        (user_id,)
                    )

                # Delete user last
                await cursor.execute(
                    "DELETE FROM users_master WHERE user_id = %s",
                    (user_id,)
                )

                await conn.commit()

        return True

    except Exception as e:
        logger.error(f"Hard delete failed for user {user_id}: {e}")
        return False

#--------------Soft Delete and Hard Delete PO by Business Admin--------------
TABLE_PK_MAP = {
    "po_missing_report": "po_missing_id",
    "po_mismatch_report": "po_mismatch_id",
    "po_details": "po_det_id",

    "sharepoint_po_missing_report": "sharepoint_po_missing_id",
    "sharepoint_po_mismatch_report": "sharepoint_po_mismatch_id",
    "sharepoint_po_details": "sharepoint_po_det_id",
}

VALID_SOURCES = {"email", "sharepoint"}
VALID_TYPES = {"missing", "mismatch"}


def get_table_name(source: str, record_type: str | None) -> str:
    if source not in VALID_SOURCES:
        raise ValueError("Invalid source")

    if record_type and record_type in VALID_TYPES:
        if source == "email":
            return f"po_{record_type}_report"
        else:
            return f"{source}_po_{record_type}_report"

    if source == "email":
        return "po_details"
    else:
        return f"{source}_po_details"


def get_pk_column(table: str) -> str:
    pk = TABLE_PK_MAP.get(table)
    if not pk:
        raise ValueError(f"No PK mapping found for table: {table}")
    return pk

async def resolve_detail_id(cursor, record_id: int, source: str, record_type: str | None):
    
    if source == "email":
        detail_col = "po_det_id"
        missing_table = "po_missing_report"
        mismatch_table = "po_mismatch_report"
        missing_pk = "po_missing_id"
        mismatch_pk = "po_mismatch_id"

    else:
        detail_col = "sharepoint_po_det_id"
        missing_table = "sharepoint_po_missing_report"
        mismatch_table = "sharepoint_po_mismatch_report"
        missing_pk = "sharepoint_po_missing_id"
        mismatch_pk = "sharepoint_po_mismatch_id"

    # If coming from missing table
    if record_type == "missing":
        await cursor.execute(
            f"SELECT {detail_col} FROM {missing_table} WHERE {missing_pk} = %s",
            (record_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    # If coming from mismatch table
    elif record_type == "mismatch":
        await cursor.execute(
            f"SELECT {detail_col} FROM {mismatch_table} WHERE {mismatch_pk} = %s",
            (record_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    # If coming from details directly
    else:
        return record_id

async def soft_delete_po_by_business_admin(
    request,
    record_id: int,
    source: str,
    record_type: str | None = None
) -> bool:
    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await conn.begin()

                # Resolve detail ID
                detail_id = await resolve_detail_id(cursor, record_id, source, record_type)

                if not detail_id:
                    raise Exception("Detail ID not found")

                if source == "email":
                    detail_table = "po_details"
                    detail_col = "po_det_id"
                    missing_table = "po_missing_report"
                    mismatch_table = "po_mismatch_report"

                else:
                    detail_table = "sharepoint_po_details"
                    detail_col = "sharepoint_po_det_id"
                    missing_table = "sharepoint_po_missing_report"
                    mismatch_table = "sharepoint_po_mismatch_report"

                # 1️⃣ Inactivate parent
                await cursor.execute(
                    f"UPDATE {detail_table} SET active = 0 WHERE {detail_col} = %s",
                    (detail_id,)
                )

                # 2️⃣ Inactivate all missing
                await cursor.execute(
                    f"UPDATE {missing_table} SET active = 0 WHERE {detail_col} = %s",
                    (detail_id,)
                )

                # 3️⃣ Inactivate all mismatch
                await cursor.execute(
                    f"UPDATE {mismatch_table} SET active = 0 WHERE {detail_col} = %s",
                    (detail_id,)
                )

                await conn.commit()

        logger.info(f"Soft delete successful for detail_id {detail_id}")
        return True

    except Exception as e:
        logger.error(f"Soft delete failed: {e}")
        return False

async def hard_delete_po_by_business_admin(
    request,
    record_id: int,
    source: str,
    record_type: str | None = None
) -> bool:
    try:
        async with request.app.state.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await conn.begin()

                # Resolve detail ID
                detail_id = await resolve_detail_id(cursor, record_id, source, record_type)

                if not detail_id:
                    raise Exception("Detail ID not found")

                if source == "email":
                    detail_table = "po_details"
                    detail_col = "po_det_id"
                    missing_table = "po_missing_report"
                    mismatch_table = "po_mismatch_report"

                else:
                    detail_table = "sharepoint_po_details"
                    detail_col = "sharepoint_po_det_id"
                    missing_table = "sharepoint_po_missing_report"
                    mismatch_table = "sharepoint_po_mismatch_report"

                # Delete children first
                await cursor.execute(
                    f"DELETE FROM {missing_table} WHERE {detail_col} = %s",
                    (detail_id,)
                )

                await cursor.execute(
                    f"DELETE FROM {mismatch_table} WHERE {detail_col} = %s",
                    (detail_id,)
                )

                # Delete parent
                await cursor.execute(
                    f"DELETE FROM {detail_table} WHERE {detail_col} = %s",
                    (detail_id,)
                )

                await conn.commit()

        logger.info(f"Hard delete successful for detail_id {detail_id}")
        return True

    except Exception as e:
        logger.error(f"Hard delete failed: {e}")
        return False
